package no.ntnu.nav.getDeviceData.dataplugins.NetboxInfo;

import java.util.*;

import no.ntnu.nav.getDeviceData.dataplugins.*;

/**
 * <p> The interface to device plugins for storing collected data.
 * </p>
 *
 * <p> This container supports the storage of string values in a
 * variable = value format, and is separate for each netbox. In
 * addition a key can be specified to get separate namespaces for the
 * variables. For variables which do not require namespace separation
 * "null" should be used as the key.  </p>
 *
 * <p> <b>Note:</b> old keys and variables are never deleted. However,
 * if values are added for a key and variable, any old values will be
 * deleted before the new are inserted (actually, the implementation
 * is smart enough to try to update values if possible instead of
 * always deleting and inserting). The {@link #commit commit()} method
 * must still be called.  </p>
 *
 * @see NetboxInfoHandler
 */

        
public class NetboxInfoContainer implements DataContainer {
	private static final int PRIORITY_NETBOXINFO = PRIORITY_NORMAL;

	private NetboxInfoHandler nih;
	private Map keyMap = new HashMap();
	private boolean commit = false;
    protected static Map mapGet(Map map, Object key) {
        /** Returns the key from map if it exists, 
          * if else a HashMap is created, inserted and returned.
          */
        if (! map.containsKey(key)) {
            map.put(key, new HashMap());
        }
        return (Map)map.get(key);
    }


	NetboxInfoContainer(NetboxInfoHandler nih) {
		this.nih = nih;
	}

	/**
	 * Get the name of the container; returns the string NetboxInfoContainer
	 */
	public String getName() {
		return "NetboxInfoContainer";
	}

	/**
	 * Get a data-handler for this container; this is a reference to the
	 * SwportHandler object which created the container.
	 */
	public DataHandler getDataHandler() {
		return nih;
	}

	/**
	* Add a list of values for the given variable. The key is
 	* assumed to be null. Var and val are not allowed to be null.
	*/
	public void put(String var, List vals) {
		put(null, var, vals);
	}

	/**
	* Add a list of values for the given variable. The key is
	* assumed to be null. Var and val are not allowed to be null.
	*/
	public void put(String var, String[] vals) {
		put(null, var, vals);
	}

	/**
	* Add a value for the given variable. The key is assumed to be
	* null. Var and val are not allowed to be null.
	*/
	public void put(String var, String val) {
		put(null, var, val);
	}

	/**
	* Add a list of values for the given key and variable. The key is allowed 
	* to be null; var and val are not.
	*/
	public void put(String key, String var, List vals) {
		for (Iterator i = vals.iterator(); i.hasNext();) {
			put(key, var, (String)i.next());
		}			
	}

	/**
	* Add a list of values for the given key and variable. The key is allowed 
	* to be null; var and val are not.
	*/
	public void put(String key, String var, String[] vals) {
		for (int i=0; i < vals.length; i++) {
			put(key, var, vals[i]);
		}
	}

	/**
	* Add a value for the given key and variable. The key is allowed to be
	* null; var and val are not.
	*/
	public void put(String key, String var, String val) {
		if (var == null || val == null) {
            System.err.println("NetboxInfoContainer.put called with var/val == null");
            return;
        }
        Map varMap = mapGet(keyMap, key);
		Map valMap = mapGet(varMap, var);
		valMap.put(val, null);
	}

	public void commit() {
		commit = true;		
	}

	boolean isCommited() {
		return commit;
	}

	Map getKeyMap() {
		return keyMap;
	}


	public int getPriority() {
		return PRIORITY_NETBOXINFO;
	}


}
