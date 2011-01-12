/*
 * NetboxInfo
 * 
 * $LastChangedRevision$
 *
 * $LastChangedDate$
 *
 * Copyright 2002-2004 Norwegian University of Science and Technology
 * 
 * This file is part of Network Administration Visualized (NAV)
 * 
 * NAV is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 * 
 * NAV is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with NAV; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 */

package no.ntnu.nav.netboxinfo;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Set;

import no.ntnu.nav.Database.Database;
import no.ntnu.nav.logger.Log;

/**
 * <p> This class supports the storage of string values in a variable
 * = value format, and is separate for each netbox. In addition a key
 * can be specified to get separate namespaces for the variables. For
 * variables which do not require namespace separation "null" should
 * be used as the key. </p>
 *
 * <p> The methods of this class are thread-safe. </p>
 *
 * <p> A connection to the database must be open before any of the
 * methods of this class are called. </p>
 *
 * <p> All operations are done directly on the database (no caching);
 * thus there may be performance issues with retrieving a large number
 * of variables. </p>
 *
 * <p> <b>Note:</b> If values are added for a key and variable, any
 * old values will be deleted before the new are inserted (actually,
 * the implementation is smart enough to try to update values if
 * possible instead of always deleting and inserting). </p>
 *
 * @version $LastChangedRevision$ $LastChangedDate$
 * @author Kristian Eide &lt;kreide@online.no&gt;
 */

public class NetboxInfo {

	private static Map netboxidMap = Collections.synchronizedMap(new HashMap());

	/**
	 * Set the default netboxid to use. This is stored per thread, and
	 * it is thus safe for multiple threads to use this method at the
	 * same time.
	 */
	public static void setDefaultNetboxid(String netboxid) {
		netboxidMap.put(Thread.currentThread(), netboxid);
	}

	/**
	 * Get a single value for the given variable; if no values exist
	 * null is returned; if there are more than one the lexiographically
	 * first is returned. The key is assumed to be null; var must not be
	 * null. A default netboxid must be set before this method is
	 * called.
	 *
	 * @param var The variable to get the value for
	 * @return a value, or null if no value exists
	 */
	public static String getSingleton(String var) {
		Iterator i = get(var);
		if (i.hasNext()) {
			return (var == null) ? ((String[])i.next())[1] : (String)i.next();
		}
		return null;
	}

	/**
	 * Get a single value for the given key and variable; if no values
	 * exist null is returned; if there are more than one the
	 * lexiographically first is returned. The key is allowed to be
	 * null; var is not. A default netboxid must be set before this
	 * method is called.
	 *
	 * @param key The key to get the value for
	 * @param var The variable to get the value for
	 * @return a value, or null if no value exists
	 */
	public static String getSingleton(String key, String var) {
		Iterator i = get(key, var);
		if (i.hasNext()) {
			return (var == null) ? ((String[])i.next())[1] : (String)i.next();
		}
		return null;
	}

	/**
	 * Get a single value for the given netboxid, key and variable; if
	 * no values exist null is returned; if there are more than one the
	 * lexiographically first is returned. The key is allowed to be
	 * null; var is not. If a default netboxid is set netboxid is also
	 * allowed to be null.
	 *
	 * @param netboxid The netboxid to get the value for
	 * @param var The variable to get the value for
	 * @return a value, or null if no value exists
	 */
	public static String getSingleton(String netboxid, String key, String var) {
		Iterator i = get(netboxid, key, var);
		if (i.hasNext()) {
			return (var == null) ? ((String[])i.next())[1] : (String)i.next();
		}
		return null;
	}

	/**
	 * Get the values for the given variable. The key is assumed to be
	 * null; if var is null it is treated as a wildcard and an array of
	 * String[2] is returned. A default netboxid must be set before this
	 * method is called. The iterator returns the values in
	 * lexiographical order.
	 *
	 * @param var The variable to get values for
	 * @return an iterator over the values (String-objects, or String[2] if var is null)
	 */
	public static Iterator get(String var) {
		return getError(null, null, var);
	}

	/**
	 * Get the values for the given key and variable. The key is allowed
	 * to be null; if var is null it is treated as a wildcard and an
	 * array of String[2] is returned. A default netboxid must be set
	 * before this method is called. The iterator returns the values in
	 * lexiographical order.
	 *
	 * @param key The key to get values for
	 * @param var The variable to get values for
	 * @return an iterator over the values (String-objects, or String[2] if var is null)
	 */
	public static Iterator get(String key, String var) {
		return getError(null, key, var);
	}

	/**
	 * Get the values for the given netboxid, key and variable. The key
	 * is allowed to be null; if var is null it is treated as a wildcard
	 * and an array of String[2] is returned. If a default netboxid is
	 * set netboxid is also allowed to be null. The iterator returns the
	 * values in lexiographical order.
	 *
	 * @param netboxid The netboxid to get values for
	 * @param key The key to get values for
	 * @param var The variable to get values for
	 * @return an iterator over the values (String-objects, or String[2] if var is null)
	 */
	public static Iterator get(String netboxid, String key, String var) {
		return getError(netboxid, key, var);
	}

	// Check for errors
	private static Iterator getError(String netboxid, String key, String var) {
		if (netboxid == null) netboxid = (String)netboxidMap.get(Thread.currentThread());
		if (netboxid == null) throw new NullPointerException("Netboxid and var are not allowed to be null");
		
		try {
			return getNoError(netboxid, key, var);
		} catch (SQLException se) {
			throw new RuntimeException("Got SQLException, aborting get: " + se.getMessage());
		}
	}

	// Does not check for errors
	private static Iterator getNoError(String netboxid, String key, String var) throws SQLException {
		ResultSet rs = getVals(netboxid, key, var);
		List l = new ArrayList();
		while (rs.next()) {
			if (var == null) {
				l.add(new String[] { rs.getString("var"), rs.getString("val") });
			} else {
				l.add(rs.getString("val"));
			}
		}
		return l.iterator();
	}

	/**
	 * Add the value for the given variable. The key is assumed to be
	 * null; var must not be null. A default netboxid must be set before
	 * this method is called.
	 *
	 * @param var The variable to insert values for
	 * @param val The value to insert
	 * @return true if previous vals did not exist.
	 */
	public static boolean put(String var, String val) {
		return put(null, null, var, Collections.singletonList(val));
	}

	/**
	 * Add the values for the given variable. The key is assumed to be
	 * null; var must not be null. A default netboxid must be set before
	 * this method is called.
	 *
	 * @param var The variable to insert values for
	 * @param vals The values to insert
	 * @return true if previous vals did not exist.
	 */
	public static boolean put(String var, String[] vals) {
		return put(null, null, var, Arrays.asList(vals));
	}

	/**
	 * Add the values for the given variable. The key is assumed to be
	 * null; var must not be null. A default netboxid must be set before
	 * this method is called.
	 *
	 * @param var The variable to insert values for
	 * @param vals The values to insert
	 * @return true if previous vals did not exist.
	 */
	public static boolean put(String var, List vals) {
		return put(null, null, var, vals);
	}

	/**
	 * Add the value for the given key and variable. The key
	 * is allowed to be null; var and val are not. A default netboxid
	 * must be set before this method is called.
	 *
	 * @param key The key to insert values for
	 * @param var The variable to insert values for
	 * @param val The value to insert
	 * @return true if previous vals did not exist.
	 */
	public static boolean put(String key, String var, String val) {
		return put(null, key, var, Collections.singletonList(val));
	}

	/**
	 * Add the values for the given netboxid, key and variable. The key
	 * is allowed to be null; var and val are not. A default netboxid
	 * must be set before this method is called.
	 *
	 * @param key The key to insert values for
	 * @param var The variable to insert values for
	 * @param vals The values to insert
	 * @return true if previous vals did not exist.
	 */
	public static boolean put(String key, String var, String[] vals) {
		return put(null, key, var, Arrays.asList(vals));
	}

	/**
	 * Add the values for the given netboxid, key and variable. The key
	 * is allowed to be null; var and val are not. A default netboxid
	 * must be set before this method is called.
	 *
	 * @param key The key to insert values for
	 * @param var The variable to insert values for
	 * @param vals The values to insert
	 * @return true if previous vals did not exist.
	 */
	public static boolean put(String key, String var, List vals) {
		return put(null, key, var, vals);
	}

	/**
	 * Add the value for the given netboxid, key and variable. The key
	 * is allowed to be null; var and val are not. If a default netboxid
	 * is set netboxid is also allowed to be null.
	 *
	 * @param netboxid The netboxid to insert values for
	 * @param key The key to insert values for
	 * @param var The variable to insert values for
	 * @param val The value to insert
	 * @return true if previous vals did not exist.
	 */
	public static boolean put(String netboxid, String key, String var, String val) {
		return put(netboxid, key, var, Collections.singletonList(val));
	}

	/**
	 * Add the values for the given netboxid, key and variable. The key
	 * is allowed to be null; var and val are not. If a default netboxid
	 * is set netboxid is also allowed to be null.
	 *
	 * @param netboxid The netboxid to insert values for
	 * @param key The key to insert values for
	 * @param var The variable to insert values for
	 * @param vals The values to insert
	 * @return true if previous vals did not exist.
	 */
	public static boolean put(String netboxid, String key, String var, String[] vals) {
		return put(netboxid, key, var, Arrays.asList(vals));
	}

	/**
	 * Add the values for the given netboxid, key and variable. The key
	 * is allowed to be null; var and val are not. If a default netboxid
	 * is set netboxid is also allowed to be null.
	 *
	 * @param netboxid The netboxid to insert values for
	 * @param key The key to insert values for
	 * @param var The variable to insert values for
	 * @param vals List of String objects; the values to insert
	 * @return true if previous vals did not exist.
	 */
	public static boolean put(String netboxid, String key, String var, List vals) {
		return putError(netboxid, key, var, vals.iterator());
	}

	// Check for errors
	private static boolean putError(String netboxid, String key, String var, Iterator newVals) {
		if (netboxid == null) netboxid = (String)netboxidMap.get(Thread.currentThread());
		if (netboxid == null || var == null) throw new NullPointerException("Netboxid and var are not allowed to be null");
		
		try {
			return putNoError(netboxid, key, var, newVals);
		} catch (SQLException se) {
			try {
				Database.rollback();
			} catch (SQLException expr) {
				Log.d("NETBOXINFO", "PUT_ERROR", "SQLException when rolling back: " + expr);
			}				
			throw new RuntimeException("Got SQLException, aborting put: " + se.getMessage());
		}
}

	// Does not check for errors
	private static boolean putNoError(String netboxid, String key, String var, Iterator newVals) throws SQLException {
		ResultSet rs = getVals(netboxid, key, var);
		Map valMap = new HashMap();
		while (rs.next()) {
			valMap.put(rs.getString("val"), rs.getString("netboxinfoid"));
		}
		
		try {
			Database.beginTransaction();

			if (valMap.size() == 0) {
				// Var is new, simply insert new records
				insertVals(netboxid, key, var, newVals);
				Database.commit();
				return true;

			} else {
				// Var exists, try to update before delete
				Set newValSet = new HashSet();
				while (newVals.hasNext()) {
					newValSet.add(newVals.next());
				}

				// Remove all equal values (the intersection) from both sets
				// since we don't need to update those
				Set intersection = new HashSet(newValSet);
				intersection.retainAll(valMap.keySet());
				newValSet.removeAll(intersection);
				valMap.keySet().removeAll(intersection);

				// All remaining values in valMap should no longer be present; if there are
				// any values left in newValMap, update rows from valMap
				for (Iterator newValIt = newValSet.iterator(), valIt = valMap.values().iterator();
					 newValIt.hasNext() && valIt.hasNext();) {
					String newVal = (String)newValIt.next();
					String netboxinfoid = (String)valIt.next();
					newValIt.remove();
					valIt.remove();

					String[] set = {
						"val", Database.addSlashes(newVal)
					};
					String[] where = {
						"netboxinfoid", netboxinfoid
					};
					Database.update("netboxinfo", set, where);
				}

				// Now either newValSet or valMap (or both) are empty; in the
				// first case the remaning entries from valMap are deleted, in
				// the second the remaining entries in newValSet are inserted.
				if (!newValSet.isEmpty()) {
					insertVals(netboxid, key, var, newValSet.iterator());
				}
						
				if (!valMap.isEmpty()) {
					for (Iterator valIt = valMap.values().iterator(); valIt.hasNext();) {
						Database.update("DELETE FROM netboxinfo WHERE netboxinfoid = '" + valIt.next() + "'");
					}
				}

			}

			Database.commit();
		} catch (SQLException e) {
			try {
				Database.rollback();
			} catch (SQLException expr) {
				Log.d("NETBOXINFO", "PUT_NOERROR", "SQLException when rolling back: " + expr);
			}				
			throw e;
		}
		return false;
	}

	/**
	 * Remove the values for the given variable. The key is assumed to
	 * be null; var must not be null. A default netboxid must be set
	 * before this method is called.
	 *
	 * @param var The variable to remove values for
	 * @return the number of removed values
	 */
	public static int remove(String var) {
		return removeError(null, null, var);
	}

	/**
	 * Remove the values for the given key and variable. The key is
	 * allowed to be null; var and val are not. A default netboxid must
	 * be set before this method is called.
	 *
	 * @param key The key to remove values for
	 * @param var The variable to remove values for
	 * @return the number of removed values
	 */
	public static int remove(String key, String var) {
		return removeError(null, key, var);
	}

	/**
	 * Remove the values for the given netboxid, key and variable. The key
	 * is allowed to be null; var and val are not. If a default netboxid
	 * is set netboxid is also allowed to be null.
	 *
	 * @param netboxid The netboxid to remove values for
	 * @param key The key to remove values for
	 * @param var The variable to remove values for
	 * @return the number of removed values
	 */
	public static int remove(String netboxid, String key, String var) {
		return removeError(netboxid, key, var);
	}

	// Check for errors
	private static int removeError(String netboxid, String key, String var) {
		if (netboxid == null) netboxid = (String)netboxidMap.get(Thread.currentThread());
		if (netboxid == null || var == null) throw new NullPointerException("Netboxid and var are not allowed to be null");
		
		try {
			return removeNoError(netboxid, key, var);
		} catch (SQLException se) {
			throw new RuntimeException("Got SQLException, aborting remove: " + se.getMessage());
		}
	}

	// Does not check for errors
	private static int removeNoError(String netboxid, String key, String var) throws SQLException {
		String k = (key == null || key.length() == 0) ? "key IS NULL" : "key = '"+Database.addSlashes(key)+"'";

		String q = "DELETE FROM netboxinfo WHERE netboxid = '"+netboxid+"' AND " + k + " AND var = '"+Database.addSlashes(var)+"'";
		return Database.update(q);
	}

	private static ResultSet getVals(String netboxid, String key, String var) throws SQLException {
		String k = (key == null || key.length() == 0) ? "key IS NULL" : "key = '"+Database.addSlashes(key)+"'";
		String v = (var == null) ? "" : " AND var = '" + Database.addSlashes(var) + "'";
		String v2 = (var == null) ? ", var" : "";

		String q = "SELECT netboxinfoid, val" + v2 + " FROM netboxinfo WHERE netboxid = '"+netboxid+"' AND " + k + v + " ORDER BY val";
		return Database.query(q);
	}

	// Insert new values into netboxinfo
	private static void insertVals(String netboxid, String key, String var, Iterator valIt) throws SQLException {
		while (valIt.hasNext()) {
			String val = (String)valIt.next();
			
			String[] ins = {
				"netboxid", netboxid,
				"key", key,
				"var", var,
				"val", Database.addSlashes(val)
			};
			
			Database.insert("netboxinfo", ins);
		}
	}


}
