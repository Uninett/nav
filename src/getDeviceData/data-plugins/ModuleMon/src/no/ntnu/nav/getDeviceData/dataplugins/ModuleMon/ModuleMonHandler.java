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
	private static MultiMap modules;
	
	private static MultiMap queryIfindices;

	private static Set modulesDown = Collections.synchronizedSet(new HashSet());
	

	/**
	 * Fetch initial data from swport table.
	 */
	public synchronized void init(Map persistentStorage) {
		if (persistentStorage.containsKey("initDone")) return;
		persistentStorage.put("initDone", null);

		Log.setDefaultSubsystem("ModuleMonHandler");

		try {
			// We need to the mapping from netboxid:ifindex -> module and the modules belonging to each netbox
			Map ifindMapL = new HashMap();
			MultiMap modulesL = new HashMultiMap();
			MultiMap queryIfindicesL = new HashMultiMap();
			Set queryDupe = new HashSet();
			ResultSet rs = Database.query("SELECT netboxid,ifindex,moduleid,module FROM module JOIN swport USING(moduleid) ORDER BY RANDOM()");
			while (rs.next()) {
				ifindMapL.put(rs.getString("netboxid")+":"+rs.getString("ifindex"), rs.getString("moduleid"));
				modulesL.put(rs.getString("netboxid"), rs.getString("moduleid"));

				String k = rs.getString("netboxid")+":"+rs.getString("moduleid");
				if (queryDupe.add(k)) {
					queryIfindicesL.put(rs.getString("netboxid"), new String[] { rs.getString("ifindex"), rs.getString("module") });
				}
			}

			ifindMap = ifindMapL;
			modules = modulesL;
			queryIfindices = queryIfindicesL;

		} catch (SQLException e) {
			Log.e("INIT", "SQLException: " + e.getMessage());
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
	public void handleData(Netbox nb, DataContainer dc) {
		if (!(dc instanceof ModuleMonContainer)) return;
		ModuleMonContainer mmc = (ModuleMonContainer)dc;
		if (!mmc.isCommited()) return;

		Set mod = modules.get(nb.getNetboxidS());
		if (mod == null) {
			Log.w("MODULE_MON", "HANDLE", "No modules found for netbox " + nb.getSysname());
			return;
		}

		// Local copy we can modify
		mod = new HashSet(mod);

		int severity = 50;

		for (Iterator it = mmc.getActiveIfindices(); it.hasNext();) {
			String m = (String)ifindMap.get(nb.getNetboxid()+":"+it.next());
			String key = nb.getNetboxid()+":"+m;

			if (modulesDown.contains(key)) {
				// The module is coming up, send up event
				sendEvent(nb, m, Event.STATE_END, severity);
				modulesDown.remove(key);
			}
			mod.remove(m);
		}

		// All remaining modules are now considered down; send event
		for (Iterator it = mod.iterator(); it.hasNext();) {
			String m = (String)it.next();

			sendEvent(nb, m, Event.STATE_START, severity);
			modulesDown.add(nb.getNetboxid()+":"+m);
		}
	}

	// Post the event
	private void sendEvent(Netbox nb, String m, int state, int severity) {
			Event e = EventQ.eventFactory("moduleMon", "eventEngine", nb.getDeviceid(), nb.getNetboxid(), Integer.parseInt(m), "moduleState", state, -1, severity, null);
			EventQ.postEvent(e);
	}

}
