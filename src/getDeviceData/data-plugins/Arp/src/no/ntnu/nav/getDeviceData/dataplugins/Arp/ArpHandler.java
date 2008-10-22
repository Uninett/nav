package no.ntnu.nav.getDeviceData.dataplugins.Arp;

import java.net.InetAddress;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

import no.ntnu.nav.Database.Database;
import no.ntnu.nav.getDeviceData.Netbox;
import no.ntnu.nav.getDeviceData.dataplugins.DataContainer;
import no.ntnu.nav.getDeviceData.dataplugins.DataHandler;
import no.ntnu.nav.logger.Log;

/**
 * Datahandler plugin for getDeviceData. This plugin provides an interface
 * for storing IP-to-MAC mappings for both IPv4 and IPv6 in the ARP table.
 * 
 * @author gogstad
 *
 */

public class ArpHandler implements DataHandler {

	private static final int PREFIX_CACHE_SYNC_INTERVAL = 600000; //DEFAULT ten minuits
	
	private Map<InetAddress,String> oldIpMacMap;
	private Map<String,Integer> oldMacArpIdMap;

	private Map<InetAddress,String> deviceIpMacMap;
	
	private static Map<NavIP,Integer> prefixCache = null;
	private static long previousCacheSync;

	public DataContainer dataContainerFactory() {
		return new ArpContainer(this);
	}

	public void handleData(Netbox nb, DataContainer dc, Map changedDeviceids) {
		if (!(dc instanceof ArpContainer))
			return;
		ArpContainer ac = (ArpContainer)dc;

		if (!ac.isCommited())
			return;

		Log.setDefaultSubsystem("ARPHandler");

		synchronized(this) {
			if(prefixCache == null)
				syncPrefixCache();
			
			deviceIpMacMap = ac.getIpMacMap();
			buildOldMaps(nb);

			Set<InetAddress> oldIps = oldIpMacMap.keySet();
			Set<InetAddress> currentIps = deviceIpMacMap.keySet();

			Set<InetAddress> deadIps = new HashSet<InetAddress>(oldIps);
			deadIps.removeAll(currentIps);

			Set<InetAddress> newIps = new HashSet<InetAddress>(currentIps);
			newIps.removeAll(oldIps);

			Set<InetAddress> stillAliveIps = new HashSet<InetAddress>(oldIps);
			stillAliveIps.retainAll(newIps);

			Map<InetAddress,String> newIpMacMap = new HashMap<InetAddress,String>();
			for(InetAddress ip: newIps)
				newIpMacMap.put(ip, deviceIpMacMap.get(ip));

			Map<InetAddress,String> updatedIpMacMap = new HashMap<InetAddress,String>();
			for(InetAddress ip: stillAliveIps) {
				String oldMac = oldIpMacMap.get(ip);
				String newMac = deviceIpMacMap.get(ip);
				if(!oldMac.equals(newMac))
					updatedIpMacMap.put(ip,newMac);
			}

			if(!deadIps.isEmpty()) {
				terminateArpEntries(deadIps);
			}

			if(!newIps.isEmpty()) {
				insertIpsIntoArp(nb,newIpMacMap);
			}

			if(!updatedIpMacMap.isEmpty()) {
				updateArpEntries(nb,updatedIpMacMap);		
			}
		}
	}
	
	private void updateArpEntries(Netbox nb, Map<InetAddress,String> ipMacMap) {
		terminateArpEntries(ipMacMap.keySet());
		insertIpsIntoArp(nb,ipMacMap);
	}
	
	private synchronized void terminateArpEntries(Set<InetAddress> deadIps) {
		if(deadIps.isEmpty())
			return;
		
		List<String> stringList = new ArrayList<String>(deadIps.size());
		for(InetAddress ip: deadIps) {
			String mac = oldIpMacMap.get(ip);
			Integer arpid = oldMacArpIdMap.get(mac);
			stringList.add(arpid.toString());
		}

		String[] array = stringList.toArray(new String[stringList.size()]);
		String termSql = "UPDATE arp SET end_time=NOW() WHERE arpid IN (" + Util.stringJoin(array, ",") + ")";
		try {
			Database.update(termSql);
		} catch (SQLException e) {
			Log.e("handleData","Terminate dead IPs resultet in SQLException. SQL: " + termSql);
			e.printStackTrace();
		}
	}

	private synchronized void insertIpsIntoArp(Netbox nb, Map<InetAddress,String> ipMacMap) {
		if(System.currentTimeMillis() - previousCacheSync >= PREFIX_CACHE_SYNC_INTERVAL)
			syncPrefixCache();

		int insertCounter = 0;
		for(InetAddress ip: ipMacMap.keySet()) {
			if(ipMacMap.get(ip) == null || ipMacMap.get(ip).equals("")) { //this has been observed on some responses from cInetNetToMediaPhysAddress
				Log.e("ARPHandler", "IP address not bound to any MAC. Box: " + nb.getSysname() + ", IP: " +
						ip + ". The OIDs used is listed in no.ntnu.nav.getDeviceData.deviceplugins.ARPLogger.ARPLogger.java");
				continue;
			}

			int prefixid = -1;

			NavIP thisIp = new NavIP(ip,128);

			for(Map.Entry<NavIP,Integer> entry: prefixCache.entrySet()) {
				if(Util.isSubnet(entry.getKey(), thisIp)) {
					Integer cacheHit = entry.getValue();
					if (cacheHit == null) {
						Log.e("ARP_INSERT", "Got empty prefixid from cache for " + entry.getKey().getPrefixAddress() + "/" + entry.getKey().getPrefixLength() + ". Cache size is " + prefixCache.size());
					} else {
						prefixid = cacheHit.intValue();
					}

				}
			}

			if(prefixid == -1) {
				Log.w("ARPHandler", "Can't find prefix for " + thisIp.getPrefixAddress().getHostAddress() + " in cache, trying database.");
				Integer liveHit = doLivePrefixSearch(thisIp.getPrefixAddress());
				if(liveHit == null)
					Log.e("ARPHandler","Can't find prefix for " + thisIp.getPrefixAddress().getHostAddress() + ".");
				else
					prefixid = liveHit.intValue();
			}
			
			try {				
				String[] fieldValues = {"netboxid",Integer.toString(nb.getNetboxid()),
						"prefixid",prefixid == -1 ? "null":Integer.toString(prefixid),
						"ip",ip.getHostAddress(),
						"mac",ipMacMap.get(ip),
						"sysname",nb.getSysname(),
						"start_time","NOW()"
				};
				Database.insert("arp",fieldValues);
				insertCounter += 1;

			} catch (SQLException e) {
				e.printStackTrace();
			}
		}
		Log.d("ARP_INSERT", "Inserted " + insertCounter + " new ARP entries.");
	}

	private Integer doLivePrefixSearch(InetAddress prefixAddress) {
		String sql = "SELECT prefixid FROM prefix LEFT JOIN vlan USING (vlanid) WHERE nettype NOT IN ('reserved', 'scope', 'static') AND netaddr >> '" + prefixAddress.getHostAddress() + "'";
		int closestPrefixId = -1;
		try {
			ResultSet rs = Database.query(sql);
			while(rs.next()) {
				closestPrefixId = rs.getInt("prefixid");
				break;				
			};
		} catch (SQLException e) {
			e.printStackTrace();
		}
		
		if(closestPrefixId == -1)
			return null;
		else
			return new Integer(closestPrefixId);
	}

	public void init(Map persistentStorage, Map changedDeviceids) {
		if (persistentStorage.containsKey("initDone"))
			return;
		persistentStorage.put("initDone", null);

		Log.setDefaultSubsystem("ARPHandler");
	}
	
	private synchronized void buildOldMaps(Netbox nb) {
		String sql = "SELECT arpid, host(ip) AS ip, mac FROM arp where end_time='infinity' AND netboxid=" + nb.getNetboxid();
		oldIpMacMap = new HashMap<InetAddress, String>();
		oldMacArpIdMap = new HashMap<String, Integer>();
		
		try {
			ResultSet rs = Database.query(sql);
			
			while(rs.next()) {
				Integer arpid = rs.getInt("arpid");
				String ipAddr = rs.getString("ip");
				String mac = rs.getString("mac");
				
				InetAddress ip = Util.getInetAddress(ipAddr);
				
				oldIpMacMap.put(ip, mac);
				oldMacArpIdMap.put(mac,arpid);
			}
			
		} catch (SQLException e) {
			Log.e("ARPLogger", "An error occurred while querying the database: " + sql);
			e.printStackTrace();
			return;
		}
	}
	
	/**
	 * <p>(Re)Populates the ArpHandler's prefix cache.</p>
	 * 
	 * <p>The prefixCache class variable is created as a ConcurrentHashMap 
	 * instance.  This is to ensure that other threads can safely iterate
	 * the map while this method is updating it; the map is most likely 
	 * iterated many times between each call to this method.</p>
	 */
	public synchronized static void syncPrefixCache() {
		Log.d("SYNC_PREFIX_CACHE", "Synchronizing prefix cache");
		if(prefixCache == null)
			prefixCache = new ConcurrentHashMap<NavIP, Integer>();
		
		String sql = "SELECT prefixid,host(netaddr) AS ip, masklen(netaddr) AS prefixlength FROM prefix LEFT JOIN vlan USING (vlanid) WHERE nettype NOT IN ('reserved', 'scope', 'static')";
		HashMap tmpPrefixCache = new HashMap<NavIP, Integer>();
		
		try {
			ResultSet rs = Database.query(sql);
			while(rs.next()) {
				int prefixid = rs.getInt("prefixid");
				String ip = rs.getString("ip");
				int prefixLength = rs.getInt("prefixlength");
				NavIP nip = new NavIP(ip,prefixLength);
				tmpPrefixCache.put(nip, prefixid);		
			}

			prefixCache.clear();
			prefixCache.putAll(tmpPrefixCache);

			previousCacheSync = System.currentTimeMillis();
		} catch (SQLException e) {
			Log.e("SYNC_PREFIX_CACHE", "An error occured while synchronizing the prefix cache");
			e.printStackTrace();
		}
		Log.d("SYNC_PREFIX_CACHE", "Loaded " + prefixCache.size() + " prefixes from database");
	}

}
