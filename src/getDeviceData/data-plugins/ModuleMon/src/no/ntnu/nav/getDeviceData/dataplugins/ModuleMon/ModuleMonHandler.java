package no.ntnu.nav.getDeviceData.dataplugins.ModuleMon;

import java.util.*;
import java.sql.*;

import no.ntnu.nav.logger.*;
import no.ntnu.nav.Database.*;
import no.ntnu.nav.util.*;
import no.ntnu.nav.event.*;
import no.ntnu.nav.getDeviceData.Netbox;
import no.ntnu.nav.getDeviceData.dataplugins.*;

/**
 * DataHandler plugin for getDeviceData; provides an interface for storing
 * info about which modules of a switch/router is responding to requests.
 *
 * @see ModuleMonContainer
 */

public class ModuleMonHandler implements DataHandler {

	private static final boolean DB_UPDATE = true;
	private static final boolean DB_COMMIT = true;

	private static Map ifindMap;
	private static Map modidMap;
	private static MultiMap modules;
	
	private static MultiMap queryIfindices;

	private static Set modulesDown = new HashSet();
	

	/**
	 * Fetch initial data from swport table.
	 */
	public synchronized void init(Map persistentStorage, Map changedDeviceids) {
		if (persistentStorage.containsKey("initDone") && changedDeviceids.isEmpty()) return;
		persistentStorage.put("initDone", null);

		Log.setDefaultSubsystem("ModuleMonHandler");

		synchronized (modulesDown) {
			int oldcnt = modidMap != null ? modidMap.size() : 0;

			try {
				// We need to the mapping from netboxid:ifindex -> module and the modules belonging to each netbox
				Map ifindMapL = new HashMap();
				Map modidMapL = new HashMap();
				MultiMap modulesL = new HashMultiMap();
				MultiMap queryIfindicesL = new HashMultiMap();
				Set queryDupe = new HashSet();
				ResultSet rs = Database.query("SELECT deviceid,netboxid,ifindex,moduleid,module FROM module JOIN swport USING(moduleid) ORDER BY RANDOM()");
				while (rs.next()) {
					ifindMapL.put(rs.getString("netboxid")+":"+rs.getString("ifindex"), rs.getString("moduleid"));
					modidMapL.put(rs.getString("moduleid"), rs.getString("deviceid"));
					modulesL.put(rs.getString("netboxid"), rs.getString("moduleid"));

					String k = rs.getString("netboxid")+":"+rs.getString("moduleid");
					if (queryDupe.add(k)) {
						queryIfindicesL.put(rs.getString("netboxid"), new String[] { rs.getString("ifindex"), rs.getString("module") });
					}
				}

				modidMap = modidMapL;
				ifindMap = ifindMapL;
				modules = modulesL;
				queryIfindices = queryIfindicesL;
				Log.d("INIT", "Fetched " + modidMap.size() + " modules (" + (modidMap.size()-oldcnt) + " new)");

			} catch (SQLException e) {
				Log.e("INIT", "SQLException: " + e.getMessage());
				e.printStackTrace(System.err);
			}
		}

	}

	/**
	 * Return a DataContainer object used to return data to this
	 * DataHandler.
	 */
	public DataContainer dataContainerFactory() {
		return new ModuleMonContainer(this, queryIfindices);
	}
	
	/**
	 * Store the data in the DataContainer in the database.
	 */
	public void handleData(Netbox nb, DataContainer dc, Map changedDeviceids) {
		if (!(dc instanceof ModuleMonContainer)) return;
		ModuleMonContainer mmc = (ModuleMonContainer)dc;
		if (!mmc.isCommited()) return;

		synchronized (modulesDown) {

			Set mod = modules.get(nb.getNetboxidS());
			if (mod == null) {
				Log.w("MODULE_MON", "HANDLE", "No modules found for netbox " + nb.getSysname());
				return;
			}

			// Local copy we can modify
			mod = new HashSet(mod);

			int severity = 50;

			for (Iterator it = mmc.getActiveIfindices(); it.hasNext();) {
				String moduleid = (String)ifindMap.get(nb.getNetboxid()+":"+it.next());;
				String deviceid = (String)modidMap.get(moduleid);
				String key = nb.getNetboxid()+":"+moduleid;

				if (modulesDown.contains(key)) {
					// The module is coming up, send up event
					sendEvent(nb, deviceid, moduleid, Event.STATE_END, severity);
					modulesDown.remove(key);
				}
				mod.remove(moduleid);
			}

			// All remaining modules are now considered down; send event
			for (Iterator it = mod.iterator(); it.hasNext();) {
				String moduleid = (String)it.next();
				String deviceid = (String)modidMap.get(moduleid);

				sendEvent(nb, deviceid, moduleid, Event.STATE_START, severity);
				modulesDown.add(nb.getNetboxid()+":"+moduleid);
			}
		}

	}

	// Post the event
	private void sendEvent(Netbox nb, String deviceid, String moduleid, int state, int severity) {
		if (!EventQ.createAndPostEvent("moduleMon", "eventEngine", Integer.parseInt(deviceid), nb.getNetboxid(), Integer.parseInt(moduleid), "moduleState", state, -1, severity, null)) {
			Log.c("MODULE_MON", "SEND_EVENT", "Error sending moduleUp|Down event for " + nb + ", moduleid: " + moduleid);
		}
	}

}
