package no.ntnu.nav.getDeviceData.dataplugins.NetboxInfo;

import java.util.*;
import java.sql.*;

import no.ntnu.nav.logger.*;
import no.ntnu.nav.Database.*;
import no.ntnu.nav.getDeviceData.Netbox;
import no.ntnu.nav.getDeviceData.dataplugins.*;

/**
 * DataHandler plugin for getDeviceData; provides an interface for storing
 * values for a netbox in a variable = value format.
 *
 * @see NetboxInfoContainer
 */

public class NetboxInfoHandler implements DataHandler {

	private static Map netboxMap;	

	/**
	 * Fetch initial data from netboxinfo table.
	 */
	public synchronized void init(Map persistentStorage, Map changedDeviceids) {
		if (persistentStorage.containsKey("initDone")) return;
		persistentStorage.put("initDone", null);

		Map m;
		ResultSet rs;
		long dumpBeginTime,dumpUsedTime;

		Log.setDefaultSubsystem("NetboxInfoHandler");

		try {
		
			// netboxinfo
			dumpBeginTime = System.currentTimeMillis();
			m  = Collections.synchronizedMap(new HashMap());
			rs = Database.query("SELECT netboxinfoid, netboxid, key, var, val FROM netboxinfo");
			while (rs.next()) {
				String netboxid = rs.getString("netboxid");
				Map keyMap;
				if ( (keyMap = (Map)m.get(netboxid)) == null) m.put(netboxid, keyMap = new HashMap());

				String key = rs.getString("key");
				if (key != null && (key.length() == 0 || key.equals("null"))) key = null;
				Map varMap;
				if ( (varMap = (Map)keyMap.get(key)) == null) keyMap.put(key, varMap = new HashMap());

				String var = rs.getString("var");
				Map vals; // Is really a set, but implemented as a map to netboxinfoid's to allow for easy updating
				if ( (vals = (Map)varMap.get(var)) == null) varMap.put(var, vals = new HashMap());

				// Finally we can insert the value
				vals.put(rs.getString("val"), rs.getString("netboxinfoid"));
			}

			netboxMap = m;
			dumpUsedTime = System.currentTimeMillis() - dumpBeginTime;
			Log.d("INIT", "Dumped netboxinfo in " + dumpUsedTime + " ms");

		} catch (SQLException e) {
			Log.e("INIT", "SQLException: " + e.getMessage());
		}

	}

	/**
	 * Return a DataContainer object used to return data to this
	 * DataHandler.
	 */
	public DataContainer dataContainerFactory() {
		return new NetboxInfoContainer(this);
	}
	
	/**
	 * Store the data in the DataContainer in the database.
	 */
	public void handleData(Netbox nb, DataContainer dc, Map changedDeviceids) {
		if (!(dc instanceof NetboxInfoContainer)) return;
		NetboxInfoContainer nic = (NetboxInfoContainer)dc;
		if (!nic.isCommited()) return;

		Log.setDefaultSubsystem("NetboxInfoHandler");

		String netboxid = nb.getNetboxidS();
		Map keyMap;
		if ( (keyMap = (Map)netboxMap.get(netboxid)) == null) netboxMap.put(netboxid, keyMap = new HashMap());

		try {

			Map newKeyMap = nic.getKeyMap();

			for (Iterator it = newKeyMap.entrySet().iterator(); it.hasNext();) {
				Map.Entry me = (Map.Entry)it.next();
				String newKey = (String)me.getKey();
				Map newVarMap = (Map)me.getValue();
				
				// Check if key is present in table
				Map varMap;
				if ( (varMap = (Map)keyMap.get(newKey)) == null) keyMap.put(newKey, varMap = new HashMap());

				for (Iterator i = newVarMap.entrySet().iterator(); i.hasNext();) {
					me = (Map.Entry)i.next();
					String newVar = (String)me.getKey();
					Map newValMap = (Map)me.getValue();
					
					Map valMap = (Map)varMap.get(newVar);
					varMap.put(newVar, newValMap); // Store the new values

					if (valMap == null) {
						// Var is new, simply insert new records
						insertVals(netboxid, newKey, newVar, newValMap.keySet().iterator(), newValMap);

					} else {
						// Var exists, try to update before delete

						// Remove all equal values (the intersection) from both sets
						// since we don't need to update those
						Map intersection = new HashMap(valMap);
						intersection.keySet().retainAll(newValMap.keySet());
						newValMap.keySet().removeAll(intersection.keySet());
						valMap.keySet().removeAll(intersection.keySet());

						// All remaining values in valMap should no longer be present; if there are
						// any values left in newValMap, update rows from valMap
						for (Iterator newValIt = newValMap.keySet().iterator(), valIt = valMap.values().iterator();
								 newValIt.hasNext() && valIt.hasNext();) {
							String newVal = (String)newValIt.next();
							String netboxinfoid = (String)valIt.next();
							newValIt.remove();
							valIt.remove();

							String[] set = {
								"val", newVal
							};
							String[] where = {
								"netboxinfoid", netboxinfoid
							};
							Database.update("netboxinfo", set, where);
							newValMap.put(newVal, netboxinfoid);
						}

						// Now either newValMap or valMap is empty; in the first
						// case the remaning entries from valMap are deleted, in
						// the second the remaining entries in newValMap are
						// inserted.
						if (!newValMap.isEmpty()) {
							insertVals(netboxid, newKey, newVar, newValMap.keySet().iterator(), newValMap);
						}
						
						if (!valMap.isEmpty()) {
							for (Iterator valIt = valMap.values().iterator(); valIt.hasNext();) {
								Database.update("DELETE FROM netboxinfo WHERE netboxinfoid = '" + valIt.next() + "'");
							}
						}

						// Add back the intersection as these values already exist in the database
						newValMap.putAll(intersection);

					}
				}
			}

		} catch (SQLException e) {
			Log.e("HANDLE", "SQLException: " + e.getMessage());
			e.printStackTrace(System.err);
		}
	}

	// Insert new values into netboxinfo
	private void insertVals(String netboxid, String key, String var, Iterator valIt, Map valMap) throws SQLException {
		while (valIt.hasNext()) {
			String val = (String)valIt.next();
			
			String[] ins = {
				"netboxinfoid", "",
				"netboxid", netboxid,
				"key", key,
				"var", var,
				"val", val
			};
			
			String netboxinfoid = Database.insert("netboxinfo", ins, "netboxinfo_netboxinfoid_seq");
			valMap.put(val, netboxinfoid);
		}
	}
	
}
