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

	/**
	 * Removes all occurrences of a string from another string.
	 */
	public static String remove(String s, String rem) {
		if (s == null || rem == null || s.indexOf(rem) < 0) return s;
		StringBuffer sb = new StringBuffer();
		StringTokenizer st = new StringTokenizer(s, rem);
		while (st.hasMoreTokens()) sb.append(st.nextToken());
		return sb.toString();
	}

}
