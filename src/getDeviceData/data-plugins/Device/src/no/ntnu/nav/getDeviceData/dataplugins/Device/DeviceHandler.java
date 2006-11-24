package no.ntnu.nav.getDeviceData.dataplugins.Device;

import java.util.*;
import java.sql.*;

import no.ntnu.nav.logger.*;
import no.ntnu.nav.Database.*;
import no.ntnu.nav.event.*;
import no.ntnu.nav.getDeviceData.Netbox;
import no.ntnu.nav.getDeviceData.dataplugins.*;

/**
 * DataHandler plugin for getDeviceData; provides an interface for storing
 * phyiscal device data.
 *
 * @see DeviceContainer
 */

public class DeviceHandler implements DataHandler {

	//private static Map devidMap;
	//private static Map devserialMap;

	/**
	 * Fetch initial data from device and module tables.
	 */
	public synchronized void init(Map persistentStorage, Map changedDeviceids) {
		if (persistentStorage.containsKey("initDone")) return;
		persistentStorage.put("initDone", null);

		/*
		ResultSet rs;
		long dumpBeginTime,dumpUsedTime;

		Log.setDefaultSubsystem("DeviceHandler");

		try {
		
			// device
			dumpBeginTime = System.currentTimeMillis();
			devidMap = Collections.synchronizedMap(new HashMap());
			devserialMap = Collections.synchronizedMap(new HashMap());
			//rs = Database.query("SELECT deviceid,serial,hw_ver,sw_ver FROM device");
			rs = Database.query("SELECT deviceid,serial,hw_ver,fw_ver,sw_ver FROM device");
			while (rs.next()) {				
				String deviceid = rs.getString("deviceid");
				String serial = rs.getString("serial");
				String hw_ver = rs.getString("hw_ver");
				String fw_ver = rs.getString("fw_ver");
				String sw_ver = rs.getString("sw_ver");

				Device d = new Device(serial, hw_ver, fw_ver, sw_ver);
				d.setDeviceid(deviceid);

				devidMap.put(deviceid, d);
				if (serial != null) devserialMap.put(serial, d);
			}
			dumpUsedTime = System.currentTimeMillis() - dumpBeginTime;
			Log.d("INIT", "Dumped device in " + dumpUsedTime + " ms");

		} catch (SQLException e) {
			Log.e("INIT", "SQLException: " + e.getMessage());
		}
		*/

	}

	// Check if the serial is in use in the DB, and if it is, update devidMap
	private Device getDevice(ResultSet rs) throws SQLException {
		String deviceid = rs.getString("deviceid");
		String serial = rs.getString("serial");
		String hw_ver = rs.getString("hw_ver");
		String fw_ver = rs.getString("fw_ver");
		String sw_ver = rs.getString("sw_ver");

		Device d = new Device(serial, hw_ver, fw_ver, sw_ver);
		d.setDeviceid(deviceid);

		return d;
	}

	private void checkActive(ResultSet rs) throws SQLException {
		if (!rs.getBoolean("active")) {
			Database.update("UPDATE device SET active=true WHERE deviceid="+rs.getString("deviceid"));
		}
	}

	/**
	 * Return a DataContainer object used to return data to this
	 * DataHandler.
	 */
	public DataContainer dataContainerFactory() {
		return new DeviceContainer(this);
	}
	
	/**
	 * Store the data in the DataContainer in the database.
	 */
	public void handleData(Netbox nb, DataContainer dc, Map changedDeviceids) {
		if (!(dc instanceof DeviceContainer)) return;
		DeviceContainer devc = (DeviceContainer)dc;
		if (!devc.isCommited()) return;

		Log.setDefaultSubsystem("DeviceHandler");
		//new RuntimeException().printStackTrace(System.err);

		try {
			Set seenSerials = new HashSet();

			for (Iterator devices = devc.getDevices(); devices.hasNext();) {
				Device dev = (Device)devices.next();

				// Check if this is a new device
				Device olddev = null;
				String serial = dev.getSerial();
				String deviceid = dev.getDeviceidS();

				try {
					String fields = "deviceid,serial,hw_ver,fw_ver,sw_ver,active FROM device WHERE";
					ResultSet rs = Database.query("SELECT " + fields + " serial='"+serial+"'");
					if (rs.next()) {
						checkActive(rs);
						if (seenSerials.add(serial)) {
							olddev = getDevice(rs);
						} else {
							Log.e("DUPLICATE_SERIAL", "Duplicate serial found for device " + dev + ", ignoring serial");
							if (dev.getDeviceid() == rs.getInt("deviceid")) {
								deviceid = null;
							}
							dev.setSerial(null);
						}
						//System.err.println("Found old device: " + olddev);
					} else {
						//System.err.println("Not found: " + "SELECT " + fields + " serial='"+serial+"'");
					}

					if (olddev == null && deviceid != null && !"0".equals(deviceid)) {
						rs = Database.query("SELECT " + fields + " deviceid='"+deviceid+"'");
						if (rs.next()) {
							checkActive(rs);
							olddev = getDevice(rs);
							//System.err.println("Found old device2: " + olddev);
						}
					}
				} catch (SQLException e) {
					Log.e("HANDLE", "Cannot fetch old device: " + serial + ", " + deviceid);
					e.printStackTrace(System.err);
				}

				if (olddev == null) {
					// FIXME: Skal gi feilmelding her hvis vi ikke oppretter devicer automatisk!
					// Først oppretter vi device
					String[] ins = {
						"deviceid", "",
						"serial", dev.getSerial(),
						"hw_ver", dev.getHwVer(),
						"fw_ver", dev.getFwVer(),
						"sw_ver", dev.getSwVer(),
						"auto", "t",
						"active", "t",
					};
					deviceid = Database.insert("device", ins, null);
					//dev.setDeviceid(deviceid);
					//changedDeviceids.put(deviceid, new Integer(DataHandler.DEVICE_ADDED));
					Log.i("NEW_DEVICE", "New device("+deviceid+") with serial: " + dev.getSerial() + ", " + dev);
				} else {
					deviceid = olddev.getDeviceidS();
					if (!dev.equalsDevice(olddev)) {
						// Device needs to be updated
						Log.i("UPDATE_DEVICE", "Update deviceid="+deviceid+" serial="+dev.getSerial()+" hw_ver="+dev.getHwVer()+" fw_ver="+dev.getFwVer()+" sw_ver="+dev.getSwVer());
						//System.err.println("new: " + dev);
						//System.err.println("old: " + olddev);
						
						String[] set = {
							"serial", dev.getSerial(),
							"hw_ver", dev.getHwVer(),
							"fw_ver", dev.getFwVer(),
							"sw_ver", dev.getSwVer()
						};
						String[] where = {
							"deviceid", deviceid,
						};
						Database.update("device", set, where);
						//changedDeviceids.put(deviceid, new Integer(DataHandler.DEVICE_UPDATED));

						// Now we need to send events if hw_ver, fw_ver or sw_ver changed
						if (!equalsNN(dev.getHwVer(), olddev.getHwVer())) {
							Map varMap = new HashMap();
							varMap.put("alerttype", "deviceHwVerChanged");
							varMap.put("deviceid", deviceid);
							varMap.put("old_hwver", String.valueOf(olddev.getHwVer()));
							varMap.put("new_hwver", String.valueOf(dev.getHwVer()));
							EventQ.createAndPostEvent("getDeviceData", "eventEngine", nb.getDeviceid(), nb.getNetboxid(), 0, "info", Event.STATE_NONE, 0, 0, varMap);
						}
						
						if (!equalsNN(dev.getFwVer(), olddev.getFwVer())) {
							Map varMap = new HashMap();
							varMap.put("alerttype", "deviceFwVerChanged");
							varMap.put("deviceid", deviceid);
							varMap.put("old_fwver", String.valueOf(olddev.getFwVer()));
							varMap.put("new_fwver", String.valueOf(dev.getFwVer()));
							EventQ.createAndPostEvent("getDeviceData", "eventEngine", nb.getDeviceid(), nb.getNetboxid(), 0, "info", Event.STATE_NONE, 0, 0, varMap);
						}
						
						if (!equalsNN(dev.getSwVer(), olddev.getSwVer())) {
							Map varMap = new HashMap();
							varMap.put("alerttype", "deviceSwVerChanged");
							varMap.put("deviceid", deviceid);
							varMap.put("old_swver", String.valueOf(olddev.getSwVer()));
							varMap.put("new_swver", String.valueOf(dev.getSwVer()));
							EventQ.createAndPostEvent("getDeviceData", "eventEngine", nb.getDeviceid(), nb.getNetboxid(), 0, "info", Event.STATE_NONE, 0, 0, varMap);
						}
					}
					//dev.setEqual(olddev);
				}
				dev.setDeviceid(deviceid);
				//devidMap.put(deviceid, dev);
				//if (serial != null) devserialMap.put(serial, dev);

			}

		} catch (SQLException e) {
			Log.e("HANDLE", "SQLException: " + e.getMessage());
			e.printStackTrace(System.err);
		}
	}

	private boolean equals(String s1, String s2) {
		if (s1 == null && s2 == null) return true;
		if (s1 != null) return s1.equals(s2);
		return s2.equals(s1);
	}

	// Returns true if either string is null
	private boolean equalsNN(String s1, String s2) {
		if (s1 == null || s2 == null) return true;
		if (s1 != null) return s1.equals(s2);
		return s2.equals(s1);
	}

}
