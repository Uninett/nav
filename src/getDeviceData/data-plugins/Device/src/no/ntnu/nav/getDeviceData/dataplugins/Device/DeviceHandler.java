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

	private static final boolean DB_COMMIT = true;

	private static Map devidMap;
	private static Map devserialMap;

	/**
	 * Fetch initial data from device and module tables.
	 */
	public synchronized void init(Map persistentStorage) {
		if (persistentStorage.containsKey("initDone")) return;
		persistentStorage.put("initDone", null);

		ResultSet rs;
		long dumpBeginTime,dumpUsedTime;

		Log.setDefaultSubsystem("DeviceHandler");

		try {
		
			// device
			dumpBeginTime = System.currentTimeMillis();
			devidMap = Collections.synchronizedMap(new HashMap());
			devserialMap = Collections.synchronizedMap(new HashMap());
			rs = Database.query("SELECT deviceid,serial,hw_ver,sw_ver FROM device");
			while (rs.next()) {				
				String deviceid = rs.getString("deviceid");
				String serial = rs.getString("serial");
				String hw_ver = rs.getString("hw_ver");
				String sw_ver = rs.getString("sw_ver");

				Device d = new Device(serial, hw_ver, sw_ver);
				d.setDeviceid(deviceid);

				devidMap.put(deviceid, d);
				if (serial != null) devserialMap.put(serial, d);
			}
			dumpUsedTime = System.currentTimeMillis() - dumpBeginTime;
			Log.d("INIT", "Dumped device in " + dumpUsedTime + " ms");

		} catch (SQLException e) {
			Log.e("INIT", "SQLException: " + e.getMessage());
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
	public void handleData(Netbox nb, DataContainer dc) {
		if (!(dc instanceof DeviceContainer)) return;
		DeviceContainer devc = (DeviceContainer)dc;
		if (!devc.isCommited()) return;

		Log.setDefaultSubsystem("DeviceHandler");

		try {

			for (Iterator devices = devc.getDevices(); devices.hasNext();) {
				Device dev = (Device)devices.next();

				// Check if this is a new device
				String serial = dev.getSerial();
				String deviceid = dev.getDeviceidS();

				// Try to look up device by serial first
				Device olddev = (Device)devserialMap.get(serial);

				// If that didn't work we try by deviceid
				if (olddev == null && deviceid != null) olddev = (Device)devidMap.get(deviceid); 

				if (olddev == null) {
					// FIXME: Skal gi feilmelding her hvis vi ikke oppretter devicer automatisk!
					// Først oppretter vi device
					Log.i("NEW_DEVICE", "New device with serial: " + dev.getSerial());

					String[] ins = {
						"deviceid", "",
						"serial", dev.getSerial(),
						"hw_ver", dev.getHwVer(),
						"sw_ver", dev.getSwVer()
					};
					deviceid = Database.insert("device", ins, null);
				} else {
					deviceid = olddev.getDeviceidS();
					int devid = olddev.getDeviceid();
					int nbid = nb.getDeviceid();

					// If the serial changes we need to recreate the netbox
					// If devids don't match it means that we are dealing with an existing device moved
					// If serials don't match we have a new serial to an existing deviceid
					if (dev.getDeviceid() != olddev.getDeviceid() || !olddev.getSerial().equals(dev.getSerial())) {
						NetboxUpdatable nu = (NetboxUpdatable)nb;
						nu.recreate();
						Map varMap = new HashMap();
						varMap.put("old_deviceid", String.valueOf(olddev.getDeviceid()));
						varMap.put("new_deviceid", String.valueOf(dev.getDeviceid()));
						varMap.put("old_serial", String.valueOf(olddev.getSerial()));
						varMap.put("new_serial", String.valueOf(dev.getSerial()));
						EventQ.createAndPostEvent("getDeviceData", "eventEngine", nb.getDeviceid(), nb.getNetboxid(), 0, "deviceHwUpgrade", Event.STATE_NONE, 0, 0, varMap);
					}

					if (!dev.equalsDevice(olddev)) {
						// Device needs to be updated
						Log.i("UPDATE_DEVICE", "Update deviceid="+deviceid+" serial="+dev.getSerial()+" hw_ver="+dev.getHwVer()+" sw_ver="+dev.getSwVer());

						String[] set = {
							"serial", dev.getSerial(),
							"hw_ver", dev.getHwVer(),
							"sw_ver", dev.getSwVer()
						};
						String[] where = {
							"deviceid", deviceid,
						};
						Database.update("device", set, where);

						// Now we need to send events if hw_ver or sw_ver changed
						if (!dev.getHwVer().equals(olddev.getHwVer())) {
							Map varMap = new HashMap();
							varMap.put("deviceid", String.valueOf(devid));
							varMap.put("old_hwver", String.valueOf(olddev.getHwVer()));
							varMap.put("new_hwver", String.valueOf(dev.getHwVer()));
							EventQ.createAndPostEvent("getDeviceData", "eventEngine", nb.getDeviceid(), nb.getNetboxid(), 0, "deviceHwUpgrade", Event.STATE_NONE, 0, 0, varMap);
						}
						
						if (!dev.getSwVer().equals(olddev.getSwVer())) {
							Map varMap = new HashMap();
							varMap.put("deviceid", String.valueOf(devid));
							varMap.put("old_swver", String.valueOf(olddev.getSwVer()));
							varMap.put("new_swver", String.valueOf(dev.getSwVer()));
							EventQ.createAndPostEvent("getDeviceData", "eventEngine", nb.getDeviceid(), nb.getNetboxid(), 0, "deviceSwUpgrade", Event.STATE_NONE, 0, 0, varMap);
						}
					}
				}
				dev.setDeviceid(deviceid);

				devidMap.put(deviceid, dev);
				if (serial != null) devserialMap.put(serial, dev);

				if (DB_COMMIT) Database.commit(); else Database.rollback();
			}

		} catch (SQLException e) {
			Log.e("HANDLE", "SQLException: " + e.getMessage());
			e.printStackTrace(System.err);
		}
	}

}
