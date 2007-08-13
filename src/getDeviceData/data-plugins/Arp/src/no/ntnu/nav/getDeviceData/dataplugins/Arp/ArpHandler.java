package no.ntnu.nav.getDeviceData.dataplugins.Arp;

import java.net.InetAddress;
import java.net.UnknownHostException;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

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

	private Map<InetAddress,String> oldIpMacMap;
	private Map<String,Integer> oldMacArpIdMap;

	private Map<InetAddress,String> deviceIpMacMap;

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
	
	/*
	 * FIXME: Make out a smarter way to retrieve the prefixid (i.e. retrieve all ids at once in one SQL and store them in a Map).
	 */
	private synchronized void insertIpsIntoArp(Netbox nb, Map<InetAddress,String> ipMacMap) {
		try {
			for(InetAddress ip: ipMacMap.keySet()) {
				if(ipMacMap.get(ip) == null || ipMacMap.get(ip).equals("")) { //this has been observed on some responses from cInetNetToMediaPhysAddress
					Log.e("ARPHandler", "IP address not bound to any MAC. Box: " + nb.getSysname() + ", IP: " +
							ip + ". The OIDs used is listed in no.ntnu.nav.getDeviceData.deviceplugins.ARPLogger.ARPLogger.java");
					continue;
				}
				String prefixIdSql = "SELECT prefixid FROM prefix where netaddr >> '" + ip.getHostAddress() + "'";
				//only interested in the "smallest" supernet
				ResultSet rs;
				rs = Database.query(prefixIdSql);
				int prefixId = -1;
				while(rs.next()) {
					prefixId = rs.getInt("prefixid");
					break;
				}
				
				if(prefixId == -1) {
					Log.e("ARPHandler", "Can't find any supernet for " + ip.getHostAddress() + ". Entry not saved!");
					continue;
				}
				
				String[] fieldValues = {"netboxid",Integer.toString(nb.getNetboxid()),
										"prefixid",Integer.toString(prefixId),
										"ip",ip.getHostAddress(),
										"mac",ipMacMap.get(ip),
										"sysname",nb.getSysname(),
										"start_time","NOW()"
										};
				Database.insert("arp",fieldValues);

			}
		} catch (SQLException e) {
			e.printStackTrace();
		}
	}

	public void init(Map persistentStorage, Map changedDeviceids) {
		if (persistentStorage.containsKey("initDone"))
			return;
		persistentStorage.put("initDone", null);

		Log.setDefaultSubsystem("ARPHandler");
	}
	
	private synchronized void buildOldMaps(Netbox nb) {
		String sql = "SELECT arpid, host(ip) AS ip, mac, family(ip) AS version FROM arp where end_time='infinity' AND netboxid=" + nb.getNetboxid();
		oldIpMacMap = new HashMap<InetAddress, String>();
		oldMacArpIdMap = new HashMap<String, Integer>();
		
		try {
			ResultSet rs = Database.query(sql);
			
			while(rs.next()) {
				Integer arpid = rs.getInt("arpid");
				String ipAddr = rs.getString("ip");
				String mac = rs.getString("mac");
				Integer version = rs.getInt("version");
				
				InetAddress ip = null;
				
				if(version == 4) {
					try {
						String[] ipArray = ipAddr.split("\\.");
						ip = InetAddress.getByAddress(Util.convertToUnsignedByte(ipArray, 10));
					} catch (UnknownHostException e) {
						Log.e("ARPLogger", "Error while parsing IPv4 address.");
						e.printStackTrace();
						continue;
					}
				}
				
				if(version == 6) {
					String[] longAddress = Util.ipv6ShortToLong(ipAddr).split(":");
					ArrayList<String> nybbleArrayBuilder = new ArrayList<String>(32);
					for(String hexlet: longAddress) {
						String nybble1 = hexlet.substring(0, 2);
						String nybble2 = hexlet.substring(2);
						nybbleArrayBuilder.add(nybble1);
						nybbleArrayBuilder.add(nybble2);
					}
					String[] nybbleArray = nybbleArrayBuilder.toArray(new String[nybbleArrayBuilder.size()]);
					try {
						ip = InetAddress.getByAddress(Util.convertToUnsignedByte(nybbleArray, 16));
					} catch (UnknownHostException e) {
						Log.e("ARPLogger", "Error while parsing IPv6 address.");
						e.printStackTrace();
					}
				}
				
				oldIpMacMap.put(ip, mac);
				oldMacArpIdMap.put(mac,arpid);
			}
			
		} catch (SQLException e) {
			Log.e("ARPLogger", "An error occurred while querying the database: " + sql);
			e.printStackTrace();
			return;
		}
	}

}
