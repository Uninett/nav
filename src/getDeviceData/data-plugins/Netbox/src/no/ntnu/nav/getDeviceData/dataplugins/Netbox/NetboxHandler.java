package no.ntnu.nav.getDeviceData.dataplugins.Netbox;

import java.util.*;
import java.sql.*;

import no.ntnu.nav.logger.*;
import no.ntnu.nav.Database.*;
import no.ntnu.nav.event.*;
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
	public synchronized void init(Map persistentStorage) {
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
			rs = Database.query("SELECT deviceid,serial,hw_ver,sw_ver,netboxid,sysname,upsince,EXTRACT(EPOCH FROM upsince) AS uptime FROM device JOIN netbox USING (deviceid)");
			while (rs.next()) {
				NetboxData n = new NetboxData(rs.getString("serial"),
																			rs.getString("hw_ver"),
																			rs.getString("sw_ver"),
																			null);
				n.setDeviceid(rs.getInt("deviceid"));
				n.setSysname(rs.getString("sysname"));
				n.setUpsince(rs.getString("upsince"));
				n.setUptime(rs.getDouble("uptime"));
				set.add(rs.getString("sysname"));
				
				String key = rs.getString("netboxid");
				m.put(key, n);
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
	public void handleData(Netbox nb, DataContainer dc) {
		if (!(dc instanceof NetboxContainer)) return;
		NetboxContainer nc = (NetboxContainer)dc;
		if (!nc.isCommited()) return;

		// Because it's possible for serial to be empty, but we can still
		// identify the device by deviceid in netbox, we need to check the
		// deviceid if serial is empty.
		NetboxData n = (NetboxData)nc.getNetbox();
		String netboxid = nb.getNetboxidS();
		NetboxData oldn = (NetboxData)netboxMap.get(netboxid);
		netboxMap.put(netboxid, n);
		if (n.hasEmptySerial()) {
			n.setDeviceid(oldn.getDeviceid());
		}

		// Let DeviceHandler update the device table first
		DeviceHandler dh = new DeviceHandler();
		dh.handleData(nb, dc);

		Log.setDefaultSubsystem("NetboxHandler");

		try {
			Log.d("UPDATE_NETBOX", "netboxid="+netboxid+" deviceid="+n.getDeviceidS()+" sysname="+n.getSysname() + " uptime="+n.getUptime());

				// Check if we need to update netbox
			if (oldn == null || !n.equalsNetboxData(oldn)) {
				// We need to update netbox
				if (oldn != null) sysnameSet.remove(oldn.getSysname());

				// Convert uptime to timestamp
				ResultSet rs = Database.query("SELECT 'epoch'::timestamp with time zone + ("+n.getUptime()+" || ' seconds')::interval AS upsince");
				rs.next();
				n.setUpsince(rs.getString("upsince"));

				Log.i("UPDATE_NETBOX", "Updating netbox " + nb.getSysname() + " ("+netboxid+"), uptime ticks = "+n.getUptime() + " (" + n.getUpsince()+")");

				// Send event if uptime changed
				if (!oldn.equalsUptime(n)) {
					Map varMap = new HashMap();
					varMap.put("old_upsince", String.valueOf((oldn==null?null:oldn.getUpsince())));
					varMap.put("new_upsince", String.valueOf(n.getUpsince()));
					EventQ.createAndPostEvent("getDeviceData", "eventEngine", nb.getDeviceid(), nb.getNetboxid(), 0, "coldStart", Event.STATE_NONE, 0, 0, varMap);
				}

				if (sysnameSet.contains(n.getSysname())) {
					Log.w("UPDATE_NETBOX", "Cannot change " + oldn + " to " + n + " as it is already present in netbox");
					n.setSysname(null);
				} else {
					sysnameSet.add(n.getSysname());
				}

				String[] set = {
					"deviceid", n.getDeviceidS(),
					"sysname", n.getSysname(),
					"upsince", n.getUpsince(),
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
