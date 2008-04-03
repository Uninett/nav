/*
 * $Id$
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
 * 
 * Author: Kristian Eide <kreide@gmail.com>
 */

import java.io.PrintStream;
import java.sql.ResultSet;
import java.sql.ResultSetMetaData;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.StringTokenizer;

import no.ntnu.nav.Database.Database;
import no.ntnu.nav.util.util;

class HandlerNettinfo
{
	private final String gfxRoot;

	public HandlerNettinfo(String[] Is, Com Icom, int InNum, int InTempNr)
	{
		s = Is;
		com = Icom;
		tempNr = InTempNr;
		num = InNum;
		gfxRoot = com.getReq().getContextPath() + "/gfx";
	}

	public String begin()
	{
		/************************************************************
		* Level 1 handler											*
		* user.*													*
		************************************************************/

		if (s.length >= 2)
		{
			try {
				if (s[1].equals("visTopologi")) { visTopologi(); return null; }
			} catch (SQLException e) {
				com.outl("<br>\nSQLException: " + e.getMessage() + "<br>");
				PrintStream ps = com.getPStream();
				e.printStackTrace(ps);
				com.outl("Done printing stack trace.<br>");
				return null;
			} catch (Exception e) {
				com.outl("<br>\nException: " + e.getMessage() + "<br>");
				PrintStream ps = com.getPStream();
				e.printStackTrace(ps);
				com.outl("Done printing stack trace.<br>");
				return null;
			}


				/*
				 * Kall opp metode med riktig navn
				 *
				 *
				 */
			try {
				java.lang.reflect.Method metode = this.getClass().getDeclaredMethod(s[1], new Class[0]);
				metode.invoke(this, new Object[0]);
			} catch (NoSuchMethodException e) {
				com.outl("NoSuchMethodException: " + e.getMessage());
				com.outl("<!--Invalid tag: "+s[1]+"-->");
			} catch (IllegalAccessException e) {
				com.outl("IllegalAccessException: " + e.getMessage());
				com.outl("<!--Inaccessible tag: "+s[1]+"-->");
			} catch (java.lang.reflect.InvocationTargetException e) {
				com.outl("<br>\nInvocationTargetException: " + e.getMessage() + "<br>");
				PrintStream ps = com.getPStream();
				e.printStackTrace(ps);
				com.outl("Done printing stack trace.<br>");
			}

		}

		return null;
	}

	/************************************************************
	* Level 2 handler											*
	* user.<>.*													*
	************************************************************/


	/************************************************************
	* Level 1 functions											*
	* user.*													*
	************************************************************/


	HashMap sysnameMap = null;
	private synchronized HashMap[] getPortMap() throws SQLException {
		final long AGE_LIMIT = 1000*60*15; // 5 mins

		final String TOPOLOGI_MAP = "no.ntnu.nav.navAdmin.topologiMap";

		HashMap[] topologiMap;

		Object[] cachedTopologi = (Object[])com.getContext().getAttribute(TOPOLOGI_MAP);
		long age=Long.MAX_VALUE;
		if (cachedTopologi != null) age = System.currentTimeMillis() - ((Long)cachedTopologi[0]).longValue();

		if (age > AGE_LIMIT) {
			com.getContext().removeAttribute(TOPOLOGI_MAP);
			System.gc();
			HashMap portMap = null;
			HashMap rootMap = null;
			HashMap sysnameMap = null;
			HashMap katMap = null;

			portMap = new HashMap();
			rootMap = new HashMap();
			sysnameMap = new HashMap();
			katMap = new HashMap();

			String domainSuffix = com.getNavConf().get("DOMAIN_SUFFIX");
			if (domainSuffix == null) domainSuffix = "";

			// Hent gw'ene som danner røttene i treet
			ResultSet rs = Database.query(
					"SELECT DISTINCT ON (sysname, vlan.vlanid) \n" + 
					"       mg.netboxid,\n" + 
					"       sysname,\n" + 
					"       ip,\n" + 
					"       catid,\n" + 
					"       roomid,\n" + 
					"       sw_ver,\n" + 
					"       serial,\n" + 
					"       gwport.ifindex,\n" + 
					"       gwport.interface,\n" + 
					"       vlan.vlan,\n" + 
					"       netaddr,\n" + 
					"       prefix.prefixid,\n" + 
					"       nettype,\n" + 
					"       netident,\n" + 
					"       gwport.to_netboxid,\n" + 
					"       gwport.to_swportid,\n" + 
					"       mg.module AS to_module,\n" + 
					"       port AS to_port,\n" + 
					"       swport.interface AS to_interface\n" + 
					"FROM gwport\n" + 
					"JOIN module AS mg USING (moduleid)\n" + 
					"JOIN netbox USING (netboxid)\n" + 
					"JOIN device ON (netbox.deviceid = device.deviceid)\n" + 
					"LEFT JOIN gwportprefix USING (gwportid)\n" + 
					"LEFT JOIN prefix ON (gwportprefix.prefixid = prefix.prefixid)\n" + 
					"LEFT JOIN vlan USING (vlanid)\n" + 
					"LEFT JOIN swport ON (gwport.to_swportid = swportid)\n" + 
					"LEFT JOIN module AS ms ON (ms.moduleid = swport.moduleid)\n" + 
					"ORDER BY sysname, vlan.vlanid, gwport.interface");
			ResultSetMetaData rsmd = rs.getMetaData();
			while (rs.next()) {
				//HashMap hm = getHashFromResultSet(rs, rsmd, false);
				String boksid = rs.getString("netboxid");
				String boksbak = rs.getString("to_netboxid");
				String kat = rs.getString("catid");
				String vlan = rs.getString("vlan");

				// GSW'er er både GW og SW i samme enhet
				String gsw = "";
				if (kat.equals("GSW")) {
					boksbak = boksid;
					// Need this to avoid the root being under the loopback interface
					if (vlan != null && vlan.equals("0")) gsw = "r";
				}

				String key = boksid+":0";
				List l;
				if ( (l=(List)portMap.get(key)) == null) portMap.put(key, l=new ArrayList());


				HashMap hm = new HashMap();
				hm.put("netboxid", boksbak);
				hm.put("to_netboxid", boksbak+gsw);
				hm.put("vlan", rs.getString("vlan"));
				hm.put("direction", "n");
				hm.put("ifindex", rs.getString("ifindex"));
				hm.put("port", rs.getString("interface"));
				hm.put("interface", rs.getString("interface"));
				hm.put("to_module", rs.getString("to_module"));
				hm.put("to_port", rs.getString("to_port"));
				hm.put("to_interface", rs.getString("to_interface"));
				hm.put("to_catid", "gwport");
				hm.put("netaddr", rs.getString("netaddr"));
				hm.put("prefixid", rs.getString("prefixid"));
				hm.put("nettype", rs.getString("nettype"));
				hm.put("netident", rs.getString("netident"));

				// For search
				String sysname = rs.getString("sysname");
				if (sysname.endsWith(domainSuffix)) sysname = sysname.substring(0, sysname.length()-domainSuffix.length());
				hm.put("sysname", sysname);
				hm.put("ip", rs.getString("ip"));
				hm.put("room", rs.getString("roomid"));
				hm.put("software", rs.getString("sw_ver"));
				hm.put("serial", rs.getString("serial"));



				l.add(hm);

				if (!rootMap.containsKey(boksid)) {
					hm = new HashMap();
					hm.put("vlan", "0");
					hm.put("direction", "n");
					hm.put("netboxid", boksid);
					hm.put("to_netboxid", boksid);
					hm.put("catid", kat);
					rootMap.put(boksid, hm);
				}
			}

			// Hent hele swport
			rs = Database.query(
					"SELECT a.swportid, \n" + 
					"       module.netboxid,\n" + 
					"       netbox.sysname,\n" + 
					"       netbox.ip,\n" + 
					"       netbox.roomid AS room,\n" + 
					"       sw_ver AS software, \n" + 
					"       serial, \n" + 
					"       netbox2.sysname AS to_sysname,\n" + 
					"       module.module,\n" + 
					"       a.port,\n" + 
					"       a.interface,\n" + 
					"       a.ifindex,\n" + 
					"       vlan.vlan,\n" + 
					"       direction,\n" + 
					"       module.up,\n" + 
					"       a.speed,\n" + 
					"       a.duplex, \n" + 
					"       a.media,\n" + 
					"       module.up,\n" + 
					"       a.trunk,\n" + 
					"       a.portname,\n" + 
					"       a.to_netboxid,\n" + 
					"       module2.module AS to_module,\n" + 
					"       b.port AS to_port,\n" + 
					"       b.interface AS to_interface\n" + 
					"FROM swport AS a \n" + 
					"JOIN module USING (moduleid)\n" + 
					"JOIN netbox USING (netboxid)\n" + 
					"JOIN device ON (netbox.deviceid = device.deviceid)\n" + 
					"JOIN swportvlan USING (swportid)\n" + 
					"JOIN vlan USING (vlanid)\n" + 
					"LEFT JOIN swport AS b ON (a.to_swportid = b.swportid)\n" + 
					"LEFT JOIN module AS module2 ON (b.moduleid = module2.moduleid)\n" + 
					"LEFT JOIN netbox AS netbox2 ON (a.to_netboxid = netbox2.netboxid)");
			
			rsmd = rs.getMetaData();
			while (rs.next()) {
				String key = rs.getString("netboxid")+":"+rs.getString("vlan");
				List l;
				if ( (l=(List)portMap.get(key)) == null) portMap.put(key, l=new ArrayList());

				HashMap hm = getHashFromResultSet(rs, rsmd, false);
				if (rs.getString("to_netboxid") == null) {
					hm.put("to_netboxid", "cam"+rs.getString("netboxid")+":"+rs.getString("ifindex"));
				}
				l.add(hm);
			}

			// Hent servicer
			rs = Database.query(
					"SELECT netboxid,\n" + 
					"       active AS up,\n" + 
					"       handler AS portname,\n" + 
					"       version,\n" + 
					"       vlan\n" + 
					"FROM service\n" + 
					"JOIN netbox USING (netboxid)\n" + 
					"JOIN prefix USING (prefixid)\n" + 
					"JOIN vlan USING(vlanid)\n" + 
					"");
			rsmd = rs.getMetaData();
			while (rs.next()) {
				String key = rs.getString("netboxid")+":"+rs.getString("vlan");
				List l;
				if ( (l=(List)portMap.get(key)) == null) portMap.put(key, l=new ArrayList());

				HashMap hm = getHashFromResultSet(rs, rsmd, false);
				hm.put("direction", "n");
				hm.put("nodeType", "service");

				l.add(hm);
			}

			// Hent cam
			rs = Database.query(
					"SELECT cam.netboxid,\n" + 
					"       ifindex,\n" + 
					"       arp.ip,\n" + 
					"       REPLACE(mac::text, \':\', \'\') AS portname,\n" + 
					"       cam.start_time,\n" + 
					"       cam.end_time,\n" + 
					"       vlan\n" + 
					"FROM cam\n" + 
					"JOIN netbox USING (netboxid)\n" + 
					"JOIN arp USING (mac)\n" + 
					"JOIN prefix ON (arp.prefixid = prefix.prefixid)\n" + 
					"JOIN vlan USING (vlanid)\n" + 
					"WHERE cam.end_time=\'infinity\'\n" + 
					"  AND arp.end_time=\'infinity\'\n" + 
					"  AND vlan IS NOT NULL\n" + 
					""); 
			rsmd = rs.getMetaData();
			while (rs.next()) {
				String key = "cam"+rs.getString("netboxid")+":"+rs.getString("ifindex")+":"+rs.getString("vlan");
				List l;
				if ( (l=(List)portMap.get(key)) == null) portMap.put(key, l=new ArrayList());

				HashMap hm = getHashFromResultSet(rs, rsmd, false);
				hm.put("parentKey", key);
				hm.put("direction", "o");
				hm.put("nodeType", "cam");

				l.add(hm);
			}

			// Hent sysname,kat
			rs = Database.query("SELECT netboxid,sysname,catid FROM netbox");
			while (rs.next()) {
				String boksid = rs.getString("netboxid");
				String sysname = rs.getString("sysname");
				if (sysname.endsWith(domainSuffix)) sysname = sysname.substring(0, sysname.length()-domainSuffix.length());
				sysnameMap.put(boksid, sysname);
				katMap.put(boksid, rs.getString("catid"));
			}

			topologiMap = new HashMap[] { portMap, rootMap, sysnameMap, katMap };

			cachedTopologi = new Object[] { new Long(System.currentTimeMillis()), topologiMap };
			com.getContext().setAttribute(TOPOLOGI_MAP, cachedTopologi);
		}

		topologiMap = (HashMap[])cachedTopologi[1];
		return topologiMap;
	}

	private static final int SORT_SYSNAME = 0;
	private static final int SORT_IFINDEX = 10;
	private static final int SORT_PORT = 20;
	private Collection sort(Collection c, final int sortOn) {
		List l = new ArrayList(c);
		Collections.sort(l,	new Comparator() {
					public int compare(Object o1, Object o2) {
						if (!(o1 instanceof HashMap) || !(o2 instanceof HashMap)) return 0;
						HashMap m1 = (HashMap)o1;
						HashMap m2 = (HashMap)o2;
						switch (sortOn) {
						case SORT_SYSNAME: {
							String s1 = (String)sysnameMap.get(m1.containsKey("to_netboxid") ? m1.get("to_netboxid") : "");
							String s2 = (String)sysnameMap.get(m2.containsKey("to_netboxid") ? m2.get("to_netboxid") : "");
							return s1.compareTo(s2);
						}

						case SORT_IFINDEX: {
							String if1 = (String)m1.get("ifindex");
							String if2 = (String)m2.get("ifindex");
							Integer i1 = new Integer(if1 != null && !"null".equals(if1) ? if1 : "0");
							Integer i2 = new Integer(if2 != null && !"null".equals(if2) ? if2 : "0");
							int cmp = i1.compareTo(i2);
							if (cmp != 0) return cmp;
						}

						case SORT_PORT: {
							String p1 = (String)m1.get("port");
							String p2 = (String)m2.get("port");
							try {
								Integer i1 = new Integer(p1 != null && !"null".equals(p1) ? p1 : "0");
								Integer i2 = new Integer(p2 != null && !"null".equals(p2) ? p2 : "0");
								return i1.compareTo(i2);
							} catch (NumberFormatException exp) {
								return p1 == null ? 0 : p1.compareTo(p2);
							}
						}
						}
						return 0;
					}
			});
		return l;
	}

	private boolean showdetails = false;

	/* [/ni.visTopologi]
	 *
	 */
	private boolean firstSearchHit = false;
	private void visTopologi() throws SQLException
	{
		if (s.length > 2) {
			if (s[2].equals("showdetails")) {
				com.out( com.get("ni.visTopologi.showdetails") );
			}
			if (s[2].equals("showempty")) {
				com.out( com.get("ni.visTopologi.showempty") );
			}
			if (s[2].equals("searchexact")) {
				com.out( com.get("ni.visTopologi.searchexact") );
			}
			if (s[2].equals("showpath")) {
				com.out( com.get("ni.visTopologi.showpath") );
			}
			if (s[2].equals("searchblocked")) {
				com.out( com.get("ni.visTopologi.searchblocked") );
			}

			if (s.length > 3 && s[2].equals("searchField")) {
				String num = s[3];
				com.out( (num.equals(com.get("ni.visTopologi.searchFieldNum")) ? " selected" : "") );
			}
			if (s[2].equals("searchFor")) {
				//com.out( (com.get("ni.visTopologi.searchFor") != null) ? com.get("ni.visTopologi.searchFor") : "" );
				com.out( (com.getp("searchFor") != null ? com.getp("searchFor") : "") );
			}

			return;
		}

		showdetails = false;
		{
			String s = com.get("ni.visTopologi.showdetails");
			if (s != null && s.equals("checked")) showdetails = true;
		}
		boolean showempty = false;
		{
			String s = com.get("ni.visTopologi.showempty");
			if (s != null && s.equals("checked")) showempty = true;
		}
		boolean searchexact = false;
		{
			String s = com.get("ni.visTopologi.searchexact");
			if (s != null && s.equals("checked")) searchexact = true;
		}
		boolean showpath = false;
		{
			String s = com.get("ni.visTopologi.showpath");
			if (s != null && s.equals("checked")) showpath = true;
		}
		boolean searchblocked = false;
		{
			String s = com.get("ni.visTopologi.searchblocked");
			if (s != null && s.equals("checked")) searchblocked = true;
		}

		String name = "<b>Network&nbsp;</b>";
		String imgRoot = "<img border=0 src=\"" + gfxRoot + "/";
		String ntnuImg = imgRoot + "ntnunet.gif" + "\">";
		String expandIcon = imgRoot + "expand.gif" + "\" alt=\"Expand entire branch\">";
		String label = "<a name=\"0:0\"></a>";

		com.out("<table border=0 cellspacing=0 cellpadding=0 style=\"font-size: 13\">\n");
		com.outl("  <tr>");
		com.outl("    <td>");
		com.outl("      " + label + ntnuImg);
		com.outl("    </td>");
		com.outl("    <td colspan=50 style=\"font-size: 13\">");

		com.outl("      <font color=black>" + name + "</font>");
		com.outl("    </td>");
		com.outl("  </tr>");

		long begin = System.currentTimeMillis();
		HashMap portMap;
		Map rootMap;
		HashMap katMap;
		{
			HashMap[] hmA = getPortMap();
			portMap = hmA[0];
			rootMap = hmA[1];
			sysnameMap = hmA[2];
			katMap = hmA[3];
		}

		long p1 = System.currentTimeMillis();

		HashMap travMap = (HashMap)com.getUser().getData("traverseList");
		if (travMap == null) {
			travMap = new HashMap();
			//com.outl("no trav list found<br>");
		}
		com.getUser().setData("traverseList", travMap);

		// sjekk om vi skal traverese hele ntnunet
		boolean expandRoot = false;
		{
			Boolean b = (Boolean)travMap.get("0");
			if (b != null) expandRoot = b.booleanValue();
		}

		HashMap rootRec = new HashMap();
		rootRec.put("to_netboxid", "0");
		rootRec.put("vlan", "0");
		rootRec.put("rootRec", null);
		Set visitSet = new HashSet();

		HashSet searchHitSet = new HashSet();
		if (com.getp("searchField") != null && com.getp("searchFor").length() > 0) {
			String searchF = com.getp("searchField");
			String searchFor = com.getp("searchFor");
			if (searchFor != null) searchFor = searchFor.trim();

			// Remove leading number in searchField
			searchF = searchF.substring(searchF.indexOf(".")+1, searchF.length());

			// Convert MAC
			if ("mac".equals(searchF)) {
 				if (searchFor != null) {
					if (searchFor.split(":").length == 6) searchFor = util.remove(searchFor, ":");
					if (searchFor.split("\\.").length == 6) searchFor = util.remove(searchFor, ".");
				}
				searchF = "portname";
			}


			StringTokenizer st = new StringTokenizer(searchF, "|");
			String[] searchField = new String[st.countTokens()];
			for (int i=0; i < searchField.length; i++) searchField[i] = st.nextToken();

			for (Iterator iter=rootMap.values().iterator(); iter.hasNext();) {
				HashMap swrec = (HashMap)iter.next();
				swportExpand(swrec, rootRec, 0, !iter.hasNext(), expandRoot, showempty, searchexact, showpath, searchblocked, searchField, searchFor, searchHitSet, portMap, travMap, sysnameMap, katMap, visitSet);
			}
			visitSet.clear();
		}



		com.out("<table border=0 cellspacing=0 cellpadding=0>\n");
		for (Iterator iter=sort(rootMap.values(), SORT_SYSNAME).iterator(); iter.hasNext();) {
			HashMap swrec = (HashMap)iter.next();
			swportExpand(swrec, rootRec, 0, !iter.hasNext(), expandRoot, showempty, false, showpath, searchblocked, null, null, searchHitSet, portMap, travMap, sysnameMap, katMap, visitSet);
		}

		long p2 = System.currentTimeMillis();

		com.out("</table>\n");

		com.outl("<div style=\"font-size: 13\">");
		com.outl("<br>Fetch from DB/cache: " + (p1-begin) + " ms. Output HTML: " + (p2-p1) + " ms.");
		com.outl("</div>");
		firstSearchHit = false;
	}

	private boolean swportExpand(HashMap swrec, HashMap parentSwrec, int depth, boolean lastPort, boolean expand, boolean showempty, boolean searchexact, boolean showpath, boolean searchblocked, String[] searchField, String searchFor, HashSet searchHitSet, HashMap portMap, HashMap travMap, HashMap sysnameMap, HashMap katMap, Set visitSet)
	{
		int strekType = (lastPort ? BOXOPEN_BOTTOM : BOXOPEN_BOTH);

		if (depth > 24) {
			com.outl("<tr><td colspan=50 style=\"font-size: 13\">ERROR, depth too large, return.</td></tr>");
			return false;
		}

		String boksid = (String)swrec.get("netboxid");
		String boksbak = (String)swrec.get("to_netboxid");
		String kat = (String)swrec.get("catid");
		String vlan = (String)swrec.get("vlan");
		String key = boksid+":"+vlan;
		String keyBak = boksbak+":"+vlan;

		String direction = (String)swrec.get("direction");
		boolean dirDown = direction == null || !(direction.equals("b") || direction.equals("o"));

		boolean searchFound = false;

		// sjekk om vi skal traverse videre
		boolean traverse = expand;
		if (!traverse) {
			Boolean b = (Boolean)travMap.get(keyBak);
			if (b != null) {
				traverse = true;
				expand = b.booleanValue();
			}
		}

		List portList = (List)portMap.get(keyBak);
		boolean expandable = portList != null && !visitSet.contains(boksbak);


		if (searchField == null) {
			if (!showempty) {
				String bb = (String)swrec.get("to_netboxid");
				String portname = (String)swrec.get("portname");
				if (bb == null && (portname == null || portname.length() == 0)) return false;
			}

			// Skriv ut denne noden
			if (!expandable) strekType = (lastPort ? STREK_BOTTOM : STREK_BOTH);
			else if (!traverse) strekType = (lastPort ? BOXCLOSED_BOTTOM : BOXCLOSED_BOTH);

			String searchKey = ((boksbak==null||boksbak.length()==0)?swrec.get("swportid"):boksbak)+":"+vlan;
			boolean searchHit = searchHitSet.contains(searchKey);
			printNode(swrec, parentSwrec, depth, strekType, searchHit, sysnameMap, katMap);
			if (!traverse) return false;
		} else {
			for (int i=0; i < searchField.length && !searchFound; i++) {
				String s = (String)swrec.get(searchField[i]);
				if (searchexact) {
					if (s != null && s.equalsIgnoreCase(searchFor)) searchFound = true;
				} else {
					if (s != null && s.toLowerCase().indexOf(searchFor.toLowerCase()) != -1) searchFound = true;
				}
			}
		}

		if (searchField != null && searchFound) {
			String parentKey = boksid+":"+vlan;
			if (swrec.containsKey("parentKey")) parentKey = (String)swrec.get("parentKey");
			travMap.put(parentKey, new Boolean(false) );
			String searchKey = ((boksbak==null||boksbak.length()==0)?swrec.get("swportid"):boksbak)+":"+vlan;
			searchHitSet.add(searchKey);
		}

		if (depth == 0 && kat != null && kat.equals("GSW")) {
			// Vi legger ikke til i visitSet i først rekursjon da vi treffer på samme enhet ett nivå ned
		} else
		// Pass på at vi ikke går i løkke
		if (!visitSet.add(boksbak)) {
			return searchFound;
		}

		if (!dirDown && searchField != null && !searchblocked) {
			visitSet.remove(boksbak);
			return searchFound;
		}

		// Hent ut listen over porter tilhørende denne enheten
		if (portList == null)
		{
			visitSet.remove(boksbak);
			return searchFound;
		}

		for (Iterator it=sort(portList, SORT_IFINDEX).iterator(); it.hasNext();) {
			HashMap port = (HashMap)it.next();

			boolean b = swportExpand(port, swrec, depth+1, it.hasNext(), expand, showempty, searchexact, showpath, searchblocked, searchField, searchFor, searchHitSet, portMap, travMap, sysnameMap, katMap, visitSet);
			if (searchField != null && b) searchFound = true;

		}

		visitSet.remove(boksbak);

		if (searchField != null && searchFound) {
			key = boksid+":"+vlan;
			travMap.put(key, new Boolean(false) );
		}
		return searchFound;

	}

	private void printNode(HashMap swrec, HashMap parentrec, int depth, int strekType, boolean searchHit, HashMap sysnameMap, HashMap katMap)
	{
		String imgRoot = "<img border=0 src=\"" + gfxRoot + "/";
		String expandIcon = imgRoot + "expand.gif" + "\" alt=\"Expand entire branch\">";
		String expandGrayIcon = imgRoot + "expand-gray.gif" + "\" alt=\"No branches to expand\">";
		String portIcon = imgRoot + "porticon" + ("t".equals(swrec.get("trunk"))?"-trunk":"") + ".gif" + "\">";
		String redCross = imgRoot + "redcross.gif" + "\">";
		String strekVertical = imgRoot + "strek.gif" + "\">";
		String strekBoth = imgRoot + "strek_both.gif" + "\">";
		String strekBottom = imgRoot + "strek_bottom.gif" + "\">";
		String boxOpenBoth = imgRoot + "boxopen_both.gif" + "\">";
		String boxOpenBottom = imgRoot + "boxopen_bottom.gif" + "\">";
		String boxClosedBoth = imgRoot + "boxclosed_both.gif" + "\">";
		String boxClosedBottom = imgRoot + "boxclosed_bottom.gif" + "\">";

		String hubImg = imgRoot + "hub.gif" + "\">";
		String dumhubImg = imgRoot + "dumhub.gif" + "\">";
		String switchImg = imgRoot + "switch.gif" + "\">";
		String routerImg = imgRoot + "router.gif" + "\">";
		String serverImg = imgRoot + "server.gif" + "\">";
		String maskinImg = imgRoot + "maskin.gif" + "\">";
		String undefImg = imgRoot + "undef.gif" + "\">";

		String arrowIcon = imgRoot + "arrow.gif" + "\">";
		String arrowUpIcon = imgRoot + "arrow-up.gif" + "\">";
		String arrowDownIcon = imgRoot + "arrow-down.gif" + "\">";
		String arrowBlockIcon = imgRoot + "arrow-block.gif" + "\">";


		String strekIcon = "";
		String typeIcon = "";

		String fontBegin = "";
		String fontEnd = "";

		boolean box = false; boolean boxOpen = false;

		String nodeType = (String)swrec.get("nodeType");
		if (nodeType == null) nodeType = "default";

		String boksid = (String)swrec.get("netboxid");
		String boksbak = (String)swrec.get("to_netboxid");

		if (boksbak != null && boksbak.endsWith("r")) boksbak = boksbak.substring(0, boksbak.length()-1);

		String sysname = (String)sysnameMap.get(boksbak);
		String kat;
		if (swrec.containsKey("to_catid")) {
			kat = (String)swrec.get("to_catid");
		} else {
			if (boksbak != null && katMap.containsKey(boksbak)) kat = ((String)katMap.get(boksbak)).toLowerCase();
			else kat = "undef";
		}
		String parentBoksbak = (String)parentrec.get("to_netboxid");
		String parentVlan = (String)parentrec.get("vlan");

		String modul = (String)swrec.get("module");
		String port = (String)swrec.get("interface");
		String mp = (modul!=null?modul+"; ":"")+port;
		if (depth >= 2) mp = " [<b>"+mp+"</b>]";

		String modulbak = (String)swrec.get("to_module");
		String portbak = (String)swrec.get("to_interface");
		String mpBak;
		if (modulbak == null && portbak == null) mpBak = "";
		else mpBak = " [<b>"+(modulbak!=null?modulbak:"")+(portbak!=null?"; "+portbak:"")+"</b>]";

		String vlan = (String)swrec.get("vlan");
		String retning = (String)swrec.get("direction");
		typeIcon = imgRoot + kat + ".gif" + "\">";

		if (retning.charAt(0) == 'o') arrowIcon = arrowUpIcon;
		else if (retning.charAt(0) == 'b') arrowIcon = arrowBlockIcon;
		else arrowIcon = arrowDownIcon;

		String label = "<a name=\"" + boksbak+":"+vlan + "\"></a>";
		String linkLabel = "";
		String linkLabelExpand = boksbak+":"+vlan;

		switch (strekType)
		{
			case REDCROSS:
				strekIcon = redCross;
			break;

			case STREK_BOTTOM:
				strekIcon = strekBottom;
			break;

			case BOXOPEN_BOTH:
				strekIcon = boxOpenBoth;
				linkLabel = parentBoksbak+":"+parentVlan;
				box = true;
				boxOpen = true;
			break;

			case BOXOPEN_BOTTOM:
				strekIcon = boxOpenBottom;
				linkLabel = parentBoksbak+":"+parentVlan;
				box = true;
				boxOpen = true;
			break;

			case BOXCLOSED_BOTH:
				strekIcon = boxClosedBoth;
				linkLabel = boksbak+":"+vlan;
				box = true;
			break;

			case BOXCLOSED_BOTTOM:
				strekIcon = boxClosedBottom;
				linkLabel = boksbak+":"+vlan;
				box = true;
			break;

			default:
				strekIcon = strekBoth;
			break;
		}

		com.outl("  <tr>");

		printDepth(depth, strekVertical, searchHit);

		if (searchHit) {
			com.outl("<td bgcolor=\"#F0E18C\" colspan=\"50\" style=\"font-size: 13\">");
		} else {
			com.outl("<td colspan=\"50\" style=\"font-size: 13\">");
		}
		com.out(label);
		if (searchHit && !firstSearchHit) {
			firstSearchHit = true;
			com.out("\n<a name=\"searchtarget\">");
		}

		if (box)
		{
			com.out("<a href=\"");
			if (boxOpen)
			{
				link("link.ni.visTopologi.close." + boksbak);
			} else
			{
				link("link.ni.visTopologi.open." + boksbak);
			}
			com.out("&vlan="+vlan);
			com.out("#" + linkLabel);
			com.out("\">" + strekIcon + "</a>");

		} else
		{
			com.out(strekIcon);
		}

		// Expand ikon
		if (box) {
			com.out("<a href=\"");
			link("link.ni.visTopologi.expand." + boksbak);
			com.out("&vlan="+vlan);
			com.out("#" + linkLabelExpand);
			com.out("\">" + expandIcon + "</a>");
		} else {
			com.out(expandGrayIcon);
		}
		com.outl("&nbsp;");

		String netaddr = "";
		if (showdetails && swrec.containsKey("netaddr")) {
			String prefixLink = "/report/prefix?prefix.prefixid=" + swrec.get("prefixid");
			netaddr = " (<a target=\"_new\" href=\""+prefixLink+"\">"+swrec.get("netaddr")+"</a>, " + swrec.get("nettype") + ", " + swrec.get("netident")+")";
		}

		if (boksbak == null || boksbak.startsWith("cam")) sysname = (String)swrec.get("portname");
		if (sysname == null) sysname = "";
		if (sysname.length() > 0 && swrec.containsKey("up") && "n".equals(swrec.get("up")))
			sysname = "<font color=\"gray\">" + sysname + "</font>";

		String parentSysname = (String)parentrec.get("to_netboxid");
		parentSysname = (String)sysnameMap.get(parentSysname);
		if (nodeType.equals("cam")) parentSysname = (String)swrec.get("ip");

		// Add sysname links
		{
			String sysnameLink = "/browse/";
			parentSysname = "<a target=\"_new\" href=\""+sysnameLink+parentSysname+"\">"+parentSysname+"</a>";
			if (sysname.length() > 0) sysname = "<a target=\"_new\" href=\""+sysnameLink+sysname+"\">"+sysname+"</a>";
		}

		// Evt. modul/port
		if (!parentrec.containsKey("rootRec")) {
			if (depth >= 2) com.outl(parentSysname + " ");

			if (!nodeType.equals("service") && !nodeType.equals("cam")) {
				com.outl("      " + mp);
			}
			com.outl("      " + portIcon);
		}

		com.outl("&nbsp;&nbsp;" + arrowIcon + "&nbsp;");

		com.out(typeIcon);

		// Append service version information, if available
		if (nodeType.equals("service") && swrec.get("version") != null) {
			sysname += " (" + swrec.get("version") + ")";
		}

		com.outl("      " + fontBegin + "" + sysname + mpBak + netaddr + fontEnd);
		com.outl("    </td>");
		com.out("  </tr>");

	}

	private void printDepth(int depth, String strek, boolean searchHit)
	{
		for (int i = 0; i < depth; i++)
		{
			if (searchHit) {
				com.outl("<td bgcolor=\"#F0E18C\">" + strek + "</td>");
			} else {
				com.outl("<td>" + strek + "</td>");
			}
		}
	}


	private static HashMap getHashFromResultSet(ResultSet rs, ResultSetMetaData md, boolean convertNull) throws SQLException {
		HashMap hm = new HashMap();
		for (int i=md.getColumnCount(); i > 0; i--) {
			String val = rs.getString(i);
			hm.put(md.getColumnName(i), (convertNull&&val==null)?"":val);
		}
		return hm;
	}


	/************************************************************
	* End functions												*
	* admin.*													*
	************************************************************/





	public static String handle(Com com)
	{
		String html = null;
		String subSect = com.getReq().getParameter("func");

		if (subSect != null)
		{
			if (subSect.equals("avledVlan")) html = "html/ni/avledVlan.html";
			else if (subSect.equals("updateMac"))
			{
				html = "html/ni/updateMac.html";
			} else
			if (subSect.equals("updatePortBak"))
			{
				html = "html/ni/updatePortBak.html";
			} else
			if (subSect.equals("updateStatic"))
			{
				html = "html/ni/updateStatic.html";
			} else
			if (subSect.equals("visTopologi"))
			{
				if (com.getp("B1") != null) {
					String showdetails = com.getp("showdetails");
					com.set("ni.visTopologi.showdetails", (showdetails!=null ? "checked" : ""), true );

					String showempty = com.getp("showempty");
					com.set("ni.visTopologi.showempty", (showempty!=null ? "checked" : ""), true );

					String searchexact = com.getp("searchexact");
					com.set("ni.visTopologi.searchexact", (searchexact!=null ? "checked" : ""), true );

					String showpath = com.getp("showpath");
					com.set("ni.visTopologi.showpath", (showpath!=null ? "checked" : ""), true );

					String searchblocked = com.getp("searchblocked");
					com.set("ni.visTopologi.searchblocked", (searchblocked!=null ? "checked" : ""), true );

					String searchField = com.getp("searchField");
					com.set("ni.visTopologi.searchFieldNum", (searchField!=null ? searchField.substring(0, searchField.indexOf(".")) : ""), true );
				}

				String p1 = com.getp("p1");

				if (p1 != null && p1.equals("closeAll")) {
					HashMap trav;
					Object o = com.getUser().getData("traverseList");
					if (o != null) {
						trav = (HashMap)o;
						trav.clear();
					}
				} else
				if (p1 != null)
				{
					String p2 = com.getp("p2");
					String vlan = com.getp("vlan");
					if (p2 != null && vlan != null)
					{
						HashMap trav;
						Object o = com.getUser().getData("traverseList");
						if (o != null) trav = (HashMap)o;
						else trav = new HashMap();

						String key = p2+":"+vlan;
						if (p1.equals("open")) trav.put(key, new Boolean(false) );
						else if (p1.equals("close")) trav.remove(key);
						else if (p1.equals("expand")) trav.put(key, new Boolean(true) );
						com.getUser().setData("traverseList", trav);
					}
				}
				html = "html/ni/visTopologi.html";
			} else
			if (subSect.equals("checkError"))
			{
				html = "html/ni/checkError.html";

			} else
			if (subSect.equals("findMissingLinks"))
			{
				html = "html/ni/findMissingLinks.html";
			} else
			if (subSect.equals("updateCommunity"))
			{
				html = "html/ni/upcommunity.html";
			} else
			if (subSect.equals("listkant"))
			{
				html = "html/ni/listkant.html";
			} else
			if (subSect.equals("avledTopologi"))
			{
				html = "html/ni/topologi.html";
			}

		} else
		{
			html = "html/ni/main.html";
		}

		return html;
	}

	private void link(String s)
	{
		com.getHandler().handle(s);
	}




	// final ints
	final int UPDATE_DB = 0;
	final int PRINT = 1;

	final int STREK = 0;
	final int REDCROSS = 5;
	final int STREK_BOTH = 10;
	final int STREK_BOTTOM = 20;
	final int BOXOPEN_BOTH = 30;
	final int BOXOPEN_BOTTOM = 40;
	final int BOXCLOSED_BOTH = 50;
	final int BOXCLOSED_BOTTOM = 60;




	// klasse vars
	String[] s;
	Com com;
	int num;
	int tempNr;




}
