package no.ntnu.nav.util;

import java.util.*;
import java.text.*;

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

	/**
	 * Return the filename and line number of the parent of the caller
	 * to this method.
	 */
	public static String parentCodeLine() {
		Throwable t = new Throwable();
		StackTraceElement elements[] = t.getStackTrace();
		return elements.length >= 3 ? elements[2].toString() : null;
	}

	/**
	 * Return the double as a String rounded to n decimals.
	 */
	public static String format(double d, int n) {
		DecimalFormat df = new DecimalFormat("0.0", new DecimalFormatSymbols(Locale.ENGLISH) );
		df.setMinimumFractionDigits(n);
		return df.format(d);
	}

}
