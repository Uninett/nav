package no.ntnu.nav.util;

import java.util.*;
import java.util.regex.*;
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

	/**
	 * Return the number of groups before the first non-NULL group.
	 */
	public static int groupCountNotNull(Matcher m) {
		int cnt;
		for (cnt = 1; cnt <= m.groupCount() && m.group(cnt) != null; cnt++);
		return cnt-1;
	}

	/**
	 * Join the string elements into a single string, with each element
	 * separated by the given sep (which can be empty).
	 */
	public static String join(String[] s, String sep) {
		return join(s, sep, 0);
	}

	/**
	 * Join the string elements into a single string, with each element
	 * separated by the given sep (which can be empty), starting with
	 * the idx'th element.
	 */
	public static String join(String[] s, String sep, int idx) {
		if (idx < 0) return null;
		StringBuffer sb = new StringBuffer();
		for (int i=idx; i < s.length; i++) {
			sb.append(s[i]);
			if (i != s.length-1) sb.append(sep);
		}
		return sb.toString();
	}

	/**
	 * The set must contain only String objects; its elements are
	 * returned as a String array.
	 */
	public static String[] stringArray(Set s) {
		if (s == null) return null;
		String[] a = new String[s.length()];
		int i=0;
		for (Iterator it = s.iterator(); it.hasNext();) a[i++] = (String)it.next();
	}

}
