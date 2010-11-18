/*
 * util
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

package no.ntnu.nav.util;

import java.util.*;
import java.util.regex.*;
import java.text.*;

/**
 * Various utility functions.
 *
 * @version $LastChangedRevision$ $LastChangedDate$
 * @author Kristian Eide &lt;kreide@online.no&gt;
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
		int k;
		if (s == null || rem == null || (k=s.indexOf(rem)) < 0) return s;

		StringBuffer sb = new StringBuffer();
		int begin = 0;
		do {
			sb.append(s.substring(begin, k));
			begin = k + rem.length();

		} while ((k=s.indexOf(rem, begin)) >= 0);
		sb.append(s.substring(begin, s.length()));

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
		String[] a = new String[s.size()];
		int i=0;
		for (Iterator it = s.iterator(); it.hasNext();) a[i++] = (String)it.next();
		return a;
	}

	public static Comparator intComparatorFactory() {
		return new Comparator() {
				public int compare (Object o1, Object o2) {
					try {
						return new Integer(""+o1).compareTo(new Integer(""+o2));
					} catch (Exception e) {
					}
					return o1.toString().compareTo(o2.toString());
				}

				public boolean equals(Object o1, Object o2) {
					return compare(o1, o2) == 0;
				}
			};
	}

	public static SortedSet intSortedSetFactory(Collection c) {
		SortedSet s = new TreeSet(intComparatorFactory());
		s.addAll(c);
		return s;
	}

}
