package no.ntnu.nav.getDeviceData.dataplugins.Module;

import java.util.*;
import java.sql.*;

import no.ntnu.nav.logger.*;
import no.ntnu.nav.Database.*;
import no.ntnu.nav.getDeviceData.dataplugins.*;
import no.ntnu.nav.getDeviceData.deviceplugins.Netbox;

/**
 * DataHandler plugin for getDeviceData; provides an interface for storing
 * module data.
 *
 * @see ModuleContainer
 */

public class ModuleHandler implements DataHandler {

	private static final boolean DB_UPDATE = true;
	private static final boolean DB_COMMIT = true;

	private static Map deviceMap;
	private static Map moduleMap;
	

	/**
	 * Fetch initial data from device and module tables.
	 */
	public synchronized void init(Map persistentStorage) {
		if (persistentStorage.containsKey("initDone")) return;
		persistentStorage.put("initDone", null);

		Map m;
		ResultSet rs;
		long dumpBeginTime,dumpUsedTime;

		Log.setDefaultSubsystem("ModuleHandler");

		try {
		
			// device
			dumpBeginTime = System.currentTimeMillis();
			m  = Collections.synchronizedMap(new HashMap());
			rs = Database.query("SELECT deviceid,serial FROM device");
			while (rs.next()) {
				m.put(rs.getString("serial"), rs.getString("deviceid"));
			}
			deviceMap = m;
			dumpUsedTime = System.currentTimeMillis() - dumpBeginTime;
			Log.d("INIT", "Dumped device in " + dumpUsedTime + " ms");

			// module
			dumpBeginTime = System.currentTimeMillis();
			m = Collections.synchronizedMap(new HashMap());
			rs = Database.query("SELECT deviceid,serial,hw_ver,sw_ver,moduleid,module,netboxid,submodule FROM device JOIN module USING (deviceid)");
			while (rs.next()) {
				Module md = new Module(rs.getString("serial"), rs.getString("hw_ver"), rs.getString("sw_ver"), rs.getString("module"));
				md.setDeviceid(rs.getInt("deviceid"));
				md.setModuleid(rs.getInt("moduleid"));
				md.setSubmodule(rs.getString("submodule"));

				String key = rs.getString("netboxid")+":"+md.getKey();
				m.put(key, md);
			}
			moduleMap = m;
			dumpUsedTime = System.currentTimeMillis() - dumpBeginTime;
			Log.d("INIT", "Dumped module in " + dumpUsedTime + " ms");

		} catch (SQLException e) {
			Log.e("INIT", "SQLException: " + e.getMessage());
		}

	}

	/**
	 * Return a DataContainer object used to return data to this
	 * DataHandler.
	 */
	public DataContainer dataContainerFactory() {
		return new ModuleContainer(this);
	}
	
	/**
	 * Store the data in the DataContainer in the database.
	 */
	public void handleData(Netbox nb, DataContainer dc) {
		if (!(dc instanceof ModuleContainer)) return;
		ModuleContainer mc = (ModuleContainer)dc;
		if (!mc.isCommited()) return;

		Log.setDefaultSubsystem("ModuleHandler");

		try {

			Iterator modules = mc.getModules();
			//outld("T"+id+":   DeviceHandler["+dhNum+"] returned MoudleDataList, modules found: : " + moduleDataList.size());

			while (modules.hasNext()) {
				Module md = (Module)modules.next();

				// Er dette serienummeret i device-tabellen?
				String deviceid = (String)deviceMap.get(md.getSerial());
				boolean insertedDevice = false;
				if (deviceid == null) {
					// FIXME: Skal gi feilmelding her hvis vi ikke oppretter devicer automatisk!
					// Først oppretter vi device
					Log.i("NEW_DEVICE", "New device with serial: " + md.getSerial());

					ResultSet rs = Database.query("SELECT nextval('device_deviceid_seq') AS deviceid");
					rs.next();
					deviceid = rs.getString("deviceid");

					String[] insd = {
						"deviceid", deviceid,
						"serial", md.getSerial(),
						"hw_ver", md.getHwVer(),
						"sw_ver", md.getSwVer()
					};
					if (DB_UPDATE) Database.insert("device", insd);
					insertedDevice = true;
					deviceMap.put(md.getSerial(), deviceid);
				}
				md.setDeviceid(deviceid);

				// OK, først sjekk om denne porten er i module fra før
				String moduleKey = nb.getNetboxid()+":"+md.getKey();
				String moduleid;
				Module oldmd = (Module)moduleMap.get(moduleKey);
				moduleMap.put(moduleKey, md);

				if (oldmd == null) {
					// Sett inn i module
					Log.i("NEW_MODULE", "New module: " + md.getModule());

					ResultSet rs = Database.query("SELECT nextval('module_moduleid_seq') AS moduleid");
					rs.next();
					moduleid = rs.getString("moduleid");

					String[] insm = {
						"moduleid", moduleid,
						"deviceid", deviceid,
						"netboxid", nb.getNetboxid(),
						"module", md.getModule(),
						"submodule", md.getSubmodule()
					};
					if (DB_UPDATE) Database.insert("module", insm);

				} else {
					moduleid = oldmd.getModuleidS();
					if (!oldmd.equals(md)) {
						// Vi må oppdatere module
						Log.i("UPDATE_MODULE", "Update moduleid: " + moduleid + " deviceid="+deviceid+" module="+md.getModule());

						String[] set = {
							"deviceid", deviceid,
							"module", md.getModule(),
							"submodule", md.getSubmodule()
						};
						String[] where = {
							"moduleid", moduleid
						};
						if (DB_UPDATE) Database.update("module", set, where);
					}
				}
				md.setModuleid(moduleid);

				if (!insertedDevice && (oldmd == null || !oldmd.equalsDevice(md))) {
					// Oppdater device
					Log.i("UPDATE_DEVICE", "Update deviceid: " + deviceid + " hw_ver="+md.getHwVer()+" sw_ver="+md.getSwVer());

					String[] set = {
						"hw_ver", md.getHwVer(),
						"sw_ver", md.getSwVer()
					};
					String[] where = {
						"deviceid", deviceid
					};
					if (DB_UPDATE) Database.update("device", set, where);
				}

				//outld("T"+id+":   DeviceHandler["+dhNum+"] returned Module["+i+"], swports new: " + md.getSwportCount() + (oldmd==null?" (no old)":" old: " + oldmd.getSwportCount()) );

				if (DB_COMMIT) Database.commit(); else Database.rollback();

			}

		} catch (SQLException e) {
			Log.e("HANDLE", "SQLException: " + e.getMessage());
			e.printStackTrace(System.err);
		}
	}

}
