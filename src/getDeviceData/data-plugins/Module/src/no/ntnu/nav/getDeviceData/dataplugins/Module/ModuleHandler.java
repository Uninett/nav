package no.ntnu.nav.getDeviceData.dataplugins.Module;

import java.util.*;
import java.sql.*;

import no.ntnu.nav.logger.*;
import no.ntnu.nav.Database.*;
import no.ntnu.nav.getDeviceData.Netbox;
import no.ntnu.nav.getDeviceData.dataplugins.*;
import no.ntnu.nav.getDeviceData.dataplugins.Device.DeviceHandler;


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
			rs = Database.query("SELECT deviceid,serial,hw_ver,sw_ver,moduleid,module,netboxid,descr FROM device JOIN module USING (deviceid)");
			while (rs.next()) {
				Module md = new Module(rs.getString("serial"), rs.getString("hw_ver"), rs.getString("sw_ver"), rs.getInt("module"));
				md.setDeviceid(rs.getInt("deviceid"));
				md.setModuleid(rs.getInt("moduleid"));
				md.setDescr(rs.getString("descr"));

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

		// Because it's possible for serial to be empty, but we can still
		// identify the device by deviceid in module, we need to loop over
		// all modules and check the deviceid if serial is empty.
		for (Iterator modules = mc.getModules(); modules.hasNext();) {
			Module md = (Module)modules.next();
			String moduleKey = nb.getNetboxid()+":"+md.getKey();
			Module oldmd = (Module)moduleMap.get(moduleKey);
			if (md.hasEmptySerial() && oldmd != null) {
				md.setDeviceid(oldmd.getDeviceid());
			}
		}

		// Let DeviceHandler update the device table first
		DeviceHandler dh = new DeviceHandler();
		dh.handleData(nb, dc);

		Log.setDefaultSubsystem("ModuleHandler");

		try {

			for (Iterator modules = mc.getModules(); modules.hasNext();) {
				Module md = (Module)modules.next();

				// Check if the module is new
				String moduleKey = nb.getNetboxid()+":"+md.getKey();
				String moduleid;
				Module oldmd = (Module)moduleMap.get(moduleKey);
				moduleMap.put(moduleKey, md);

				if (oldmd == null) {
					// Sett inn i module
					Log.i("NEW_MODULE", "deviceid="+md.getDeviceidS()+" netboxid="+nb.getNetboxid()+" module="+md.getModule()+" descr="+md.getDescr());

					String[] ins = {
						"moduleid", "",
						"deviceid", md.getDeviceidS(),
						"netboxid", nb.getNetboxidS(),
						"module", ""+md.getModule(),
						"descr", md.getDescr()
					};
					moduleid = Database.insert("module", ins, null);

				} else {
					moduleid = oldmd.getModuleidS();
					if (!md.equalsModule(oldmd)) {
						// Vi må oppdatere module
						Log.i("UPDATE_MODULE", "moduleid="+moduleid+" deviceid="+md.getDeviceidS()+" module="+md.getModule()+" descr="+md.getDescr());

						String[] set = {
							"deviceid", md.getDeviceidS(),
							"module", ""+md.getModule(),
							"descr", md.getDescr()
						};
						String[] where = {
							"moduleid", moduleid
						};
						if (DB_UPDATE) Database.update("module", set, where);
					}
				}
				md.setModuleid(moduleid);

				if (DB_COMMIT) Database.commit(); else Database.rollback();

			}

		} catch (SQLException e) {
			Log.e("HANDLE", "SQLException: " + e.getMessage());
			e.printStackTrace(System.err);
		}
	}

}
