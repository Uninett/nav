package no.ntnu.nav.getDeviceData.dataplugins.Netbox;

import java.util.*;
import java.sql.*;

import no.ntnu.nav.logger.*;
import no.ntnu.nav.Database.*;
import no.ntnu.nav.event.*;
import no.ntnu.nav.util.*;
import no.ntnu.nav.getDeviceData.Netbox;
import no.ntnu.nav.getDeviceData.dataplugins.*;
import no.ntnu.nav.getDeviceData.dataplugins.Device.DeviceHandler;


/**
 * DataHandler plugin for getDeviceData; provides an interface for storing
 * netbox data.
 *
 * @see NetboxContainer
 */

public class NetboxHandler implements DataHandler {

	private static Map netboxMap;
	private static Set sysnameSet;

	/**
	 * Fetch initial data from device and netbox tables.
	 */
	public synchronized void init(Map persistentStorage, Map changedDeviceids) {
		// Remove any devices no longer present
		if (!changedDeviceids.isEmpty()) {
			for (Iterator it = changedDeviceids.entrySet().iterator(); it.hasNext();) {
				Map.Entry me = (Map.Entry)it.next();
				if (((Integer)me.getValue()).intValue() == DataHandler.DEVICE_DELETED) {
					// Lookup netbox
					try {
						ResultSet rs = Database.query("SELECT netboxid FROM netbox WHERE deviceid = '" + me.getKey() + "'");
						if (rs.next()) {
							netboxMap.remove(rs.getString("netboxid"));
						}
					} catch (SQLException exp) {
						System.err.println("SQLException: " + exp.getMessage());
						exp.printStackTrace(System.err);
					}
				}
			}
		}
		if (persistentStorage.containsKey("initDone")) return;
		persistentStorage.put("initDone", null);

		Map m;
		Set set;
		ResultSet rs;
		long dumpBeginTime,dumpUsedTime;

		Log.setDefaultSubsystem("NetboxHandler");

		try {
		
			// netbox
			dumpBeginTime = System.currentTimeMillis();
			m = Collections.synchronizedMap(new HashMap());
			set = Collections.synchronizedSet(new HashSet());
			rs = Database.query("SELECT deviceid,serial,hw_ver,fw_ver,sw_ver,netboxid,sysname,upsince,EXTRACT(EPOCH FROM upsince) AS uptime,vtpvlan FROM device JOIN netbox USING (deviceid) LEFT JOIN netbox_vtpvlan USING (netboxid) ORDER BY netboxid");
			while (rs.next()) {
				NetboxData n = new NetboxData(rs.getString("serial"),
											  rs.getString("hw_ver"),
											  rs.getString("fw_ver"),
											  rs.getString("sw_ver"),
											  null);
				n.setDeviceid(rs.getInt("deviceid"));
				n.setSysname(rs.getString("sysname"));
				n.setUpsince(rs.getString("upsince"));
				n.setUptime(rs.getDouble("uptime"));
				set.add(rs.getString("sysname"));
				
				String key = rs.getString("netboxid");
				m.put(key, n);
				
				int netboxid = rs.getInt("netboxid");
				do {
					n.addVtpVlan(rs.getInt("vtpvlan"));
				} while (rs.next() && rs.getInt("netboxid") == netboxid);
				rs.previous();
			}

			netboxMap = m;
			sysnameSet = set;
			dumpUsedTime = System.currentTimeMillis() - dumpBeginTime;
			Log.d("INIT", "Dumped device/netbox in " + dumpUsedTime + " ms");

		} catch (SQLException e) {
			Log.e("INIT", "SQLException: " + e.getMessage());
		}

	}

	/**
	 * Return a DataContainer object used to return data to this
	 * DataHandler.
	 */
	public DataContainer dataContainerFactory() {
		return new NetboxContainer(this);
	}
	
	/**
	 * Store the data in the DataContainer in the database.
	 */
	public void handleData(Netbox nb, DataContainer dc, Map changedDeviceids) {
		if (!(dc instanceof NetboxContainer)) return;
		NetboxContainer nc = (NetboxContainer)dc;
		if (!nc.isCommited()) return;

		// Because it's possible for serial to be empty, but we can still
		// identify the device by deviceid in netbox, we need to check the
		// deviceid if serial is empty.
		NetboxData n = (NetboxData)nc.getNetbox();
		String netboxid = nb.getNetboxidS();
		NetboxData oldn;
		synchronized (netboxMap) {
			oldn = (NetboxData)netboxMap.get(netboxid);
			if (oldn == null) {
				// Time to update the netboxMap
				init(new HashMap(), new HashMap());
				oldn = (NetboxData)netboxMap.get(netboxid);
			}
			if (oldn == null) {
				// Cannot happen!
				Log.e("UPDATE_NETBOX", "Cannot find old netbox from netboxid("+netboxid+"), cannot happen, contact nav support!");
				return;
			}
			netboxMap.put(netboxid, n);
			if (n.hasEmptySerial()) {
				n.setDeviceid(oldn.getDeviceid());
			}
		}

		// Let DeviceHandler update the device table first
		DeviceHandler dh = new DeviceHandler();
		dh.handleData(nb, dc, changedDeviceids);

		Log.setDefaultSubsystem("NetboxHandler");

		try {
			// Check if we have the wrong deviceid
			if (n.getDeviceid() != oldn.getDeviceid()) {
				String[] set = {
					"deviceid", n.getDeviceidS(),
				};
				String[] where = {
					"netboxid", netboxid
				};
				Database.update("netbox", set, where);
			}

			if (nb.needRefetch()) {
				// Delete all modules
				{
					ResultSet rs = Database.query("SELECT deviceid FROM module WHERE netboxid = '"+netboxid+"'");
					while (rs.next()) {
						changedDeviceids.put(rs.getString("deviceid"), new Integer(DataHandler.DEVICE_DELETED));
					}
					int alerthistCnt = Database.update("UPDATE alerthist SET end_time=NOW() WHERE end_time='infinity' AND deviceid IN (SELECT deviceid FROM module WHERE netboxid='"+nb.getNetboxidS()+"' AND eventtypeid='moduleState')");
					int delModuleCnt = Database.update("DELETE FROM module WHERE netboxid = '"+netboxid+"'");
					Log.d("UPDATE_NETBOX", "Closed " + alerthistCnt + " alerthist records, deleted " + delModuleCnt + " modules from nb: " + nb);					
					//System.err.println("Exec: DELETE FROM module WHERE netboxid = '"+netboxid+"', " + changedDeviceids);
				}
				sysnameSet.remove(nb.getSysname());
				return;
			}

			// Check if the serial has changed
			if (oldn.getSerial() != null && n.getSerial() != null && !n.getSerial().equals(oldn.getSerial())) {
				// New serial, we need to recreate the netbox
				Log.d("UPDATE_NETBOX", "Serial changed (" + oldn.getSerial() + " -> " + n.getSerial() + ")");
				/*
				NetboxUpdatable nu = (NetboxUpdatable)nb;
				nu.recreate();
				changedDeviceids.put(String.valueOf(nb.getDeviceid()), new Integer(DataHandler.DEVICE_DELETED));
				// Also all modules
				{
					ResultSet rs = Database.query("SELECT deviceid FROM module WHERE netboxid = '"+netboxid+"'");
					while (rs.next()) {
						changedDeviceids.put(rs.getString("deviceid"), new Integer(DataHandler.DEVICE_DELETED));
					}
				}
				*/
				Map varMap = new HashMap();
				varMap.put("alerttype", "serialChanged");
				varMap.put("old_deviceid", String.valueOf(oldn.getDeviceid()));
				varMap.put("new_deviceid", String.valueOf(n.getDeviceid()));
				varMap.put("old_serial", String.valueOf(oldn.getSerial()));
				varMap.put("new_serial", String.valueOf(n.getSerial()));
				EventQ.createAndPostEvent("getDeviceData", "eventEngine", 0, 0, 0, "info", Event.STATE_NONE, 0, 0, varMap);
				//netboxMap.remove(netboxid);
				//return;
			}

			// Update vtpVlan if necessary
			try {
				//Database.beginTransaction();
				for (Iterator addIt = n.vtpVlanDifference(oldn).iterator(); addIt.hasNext();) {
					String[] ins = {
						"netboxid", netboxid,
						"vtpvlan", ""+addIt.next(),
					};
					Database.insert("netbox_vtpvlan", ins);
				}
				for (Iterator delIt = oldn.vtpVlanDifference(n).iterator(); delIt.hasNext();) {
					Database.update("DELETE FROM netbox_vtpvlan WHERE netboxid="+netboxid+" AND vtpvlan='"+delIt.next()+"'");
				}
				//Database.commit();
			} catch (SQLException e) {
				e.printStackTrace(System.err);
				//Database.rollback();
			}

			String deltaS = oldn != null ? " delta = " + util.format(n.uptimeDelta(oldn),1) + "s" : "";
			
			/*
			if (n.uptimeDelta(oldn) > 0) {
				ResultSet rs = Database.query("SELECT 'epoch'::timestamp with time zone + ("+n.getUptime()+" || ' seconds')::interval AS upsince");
				rs.next();
				System.err.println(n.getSysname() + ": " + util.format(n.uptimeDelta(oldn),1) + " ticks: " + n.getTicks() + " uptime: " + n.getUptime() + " upsince: " + rs.getString("upsince") + " u1: " + n.u1 + " u2: " + n.u2);
				System.err.println("baseDiff: " + (System.currentTimeMillis()-n.baseTime));
				if (oldn != null) {
					rs = Database.query("SELECT 'epoch'::timestamp with time zone + ("+oldn.getUptime()+" || ' seconds')::interval AS upsince");
					rs.next();
					System.err.println(oldn.getSysname() + ": " + util.format(oldn.uptimeDelta(n),1) + " ticks: " + oldn.getTicks() + " uptime: " + oldn.getUptime() + " upsince: " + rs.getString("upsince") + " u1: " + oldn.u1 + " u2: " + oldn.u2);
					System.err.println("baseDiff: " + (System.currentTimeMillis()-oldn.baseTime));
				}
				System.err.println();
			}
			*/
				
			if (n.getUptime() > 0) {
				Log.d("UPDATE_NETBOX", "devid="+n.getDeviceidS()+" "+n.getSysname() + " ("+netboxid+") ticks=" + n.getTicks() + deltaS);
			}

			// Check if we need to update netbox
			if (oldn == null || !n.equalsNetboxData(oldn)) {
				// We need to update netbox
				if (oldn != null) sysnameSet.remove(oldn.getSysname());

				// Convert uptime to timestamp
				ResultSet rs = Database.query("SELECT 'epoch'::timestamp with time zone + ("+n.getUptime()+" || ' seconds')::interval AS upsince");
				rs.next();
				n.setUpsince(rs.getString("upsince"));

				Log.i("UPDATE_NETBOX", "Updating netbox " + nb.getSysname() + " ("+n.getSysname()+") ("+netboxid+")," + deltaS + " uptime ticks = "+n.getTicks() + " (" + n.getUpsince()+")");

				// Send event if uptime changed
				if (oldn == null || !oldn.equalsUptime(n)) {
					if (oldn != null && oldn.uptimeDelta(n) > NetboxData.EVENT_DELTA) {
						Map varMap = new HashMap();
						varMap.put("alerttype", "coldStart");
						varMap.put("old_upsince", String.valueOf((oldn==null?null:oldn.getUpsince())));
						varMap.put("new_upsince", String.valueOf(n.getUpsince()));
						EventQ.createAndPostEvent("getDeviceData", "eventEngine", nb.getDeviceid(), nb.getNetboxid(), 0, "boxRestart", Event.STATE_NONE, 0, 0, varMap);
					}

					// Update DB. We should only do this if the update really
					// has changed since the value might have wrapped.
					String[] set = {
						"upsince", n.getUpsince(),
					};
					String[] where = {
						"netboxid", netboxid
					};
					Database.update("netbox", set, where);
				}

				if (sysnameSet.contains(n.getSysname())) {
					Log.w("UPDATE_NETBOX", "Cannot change " + oldn + " to " + n + " as it is already present in netbox");
					n.setSysname(null);
				} else {
					sysnameSet.add(n.getSysname());
				}

				String[] set = {
					"sysname", n.getSysname(),
				};
				String[] where = {
					"netboxid", netboxid
				};
				Database.update("netbox", set, where);
			}
			
		} catch (SQLException e) {
			Log.e("HANDLE", "SQLException: " + e.getMessage());
			e.printStackTrace(System.err);
		}
	}
	
}
