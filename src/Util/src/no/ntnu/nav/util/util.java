package no.ntnu.nav.util;

import java.util.*;

/**
 * Various utility functions.
 */

public class util {

	/**
	 * Reverse the mappings in the given map. Returns a MultiMap as
	 * there may be duplicate values.
	 */
	public static MultiMap reverse(Map m) {
		if (m == null) return null;
		MultiMap mm = new HashMultiMap();
		for (Iterator it = m.entrySet().iterator(); it.hasNext();) {
			Map.Entry me = (Map.Entry)it.next();
			mm.put(me.getValue(), me.getKey());
		}
		return mm;
	}

}
