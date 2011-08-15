/*
 * $Id$
 *
 * Copyright 2004-2005 Norwegian University of Science and Technology
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
 *
 * Physical and vlan topology discovery
 * Authors: Kristian Eide <kreide@online.no>
 */

/*
 * Source code comments were translated from Norwegian to English by Morten
 * Brekkevold, on a best effort basis.  I do not know the code (yet), so I
 * can not guarantee that the translated comments make any sense. Some 
 * pointers:
 * 
 * - The Norwegian term "boks" means "box" or "netbox"
 * - The Norwegian term "avled" means "derive"
 * - The abbreviation "MP" refers to the combination "module+port"
 * - The Norwegian term "bak" means "behind"
 * 
 * So I guess the term "BoksMpBak" refers to finding out which module+port a
 * box is behind, i.e. is connected to.
 * 
 *   - Morten B.  2007-02-21
 */ 
 

import java.io.File;
import java.io.IOException;
import java.sql.ResultSet;
import java.sql.ResultSetMetaData;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collection;
import java.util.GregorianCalendar;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.StringTokenizer;

import no.ntnu.nav.Path;
import no.ntnu.nav.ConfigParser.ConfigParser;
import no.ntnu.nav.Database.Database;
import no.ntnu.nav.event.Event;
import no.ntnu.nav.event.EventQ;


class networkDiscovery
{
	public static final String scriptName = "networkDiscovery";

	private static String debugParam;

	public networkDiscovery() {

	}

	public static void main(String[] args) throws IOException
	{
		networkDiscovery nu = new networkDiscovery();

		if (args.length < 1)
		{
			nu.outl("Arguments: [configFile] <options>\n");
			nu.outl("Where options include:\n");
			nu.outl("   topology\tDiscover the network topology using data collected via SNMP.");
			nu.outl("   vlan\tDiscover which VLANs are running on each network link");
			nu.outl("   debug\tTurn on debugging output.");
			return;
		}

		int beginOptions = 0;
		String configFile = args[0];
		ConfigParser cp, dbCp;

		if (!Database.openConnection(scriptName, "nav")) {
			nu.outl("Error, could not connect to database!");
			return;
		}

		Set argSet = new HashSet();
		for (int i=beginOptions; i < args.length; i++) argSet.add(args[i]);

		if (argSet.contains("debug")) debugParam = "yes";

		try {
			String title;
			if (argSet.contains("topology")) title = "Network discovery report";
			else if (argSet.contains("vlan")) title = "Vlan discovery report";
			else title = "Argument is not valid";

			nu.outl("<html>");
			nu.outl("<head><title>"+title+"</title></head>");
			nu.outl("<body>");

			if (argSet.contains("topology")) nu.avledTopologi();
			else if (argSet.contains("vlan")) nu.avledVlan();
			else {
				nu.outl("Argument is not valid, start without arguments for help.");
			}

			nu.outl("</body>");
			nu.outl("</html>");

		} catch (SQLException e) {
			nu.errl("SQLException: " + e.getMessage());
			e.printStackTrace(System.err);
		}

	}

	/**
	 * avledTopologi means "derive topology", presumably the physical topology.
	 */
	public void avledTopologi() throws SQLException
	{
		boolean DEBUG_OUT = false;
		//String debugParam = com.getp("debug");
		if (debugParam != null && debugParam.equals("yes")) DEBUG_OUT = true;
		Boks.DEBUG_OUT = DEBUG_OUT;

		if (DEBUG_OUT) outl("Begin<br>");

		// Show date
		{
			java.util.Date currentTime = new GregorianCalendar().getTime();
			outl("Generated on: <b>" + currentTime + "</b><br>");
		}

		Map boksNavn = new HashMap();
		Map boksType = new HashMap();
		Map boksKat = new HashMap();
		ResultSet rs = Database.query("SELECT netboxid,sysName,typename,catid FROM netbox LEFT JOIN type USING(typeid)");
		while (rs.next()) {
			String sysname = rs.getString("sysName"); // Must be included as sysname can be null !!
			boksNavn.put(new Integer(rs.getInt("netboxid")), (sysname==null?"&lt;null&gt;":sysname) );
			boksType.put(new Integer(rs.getInt("netboxid")), rs.getString("typename"));
			boksKat.put(new Integer(rs.getInt("netboxid")), rs.getString("catid"));
		}
		Boks.boksNavn = boksNavn;
		Boks.boksType = boksType;

		Set gwUplink = new HashSet();
		rs = Database.query("SELECT DISTINCT ON (to_netboxid) to_netboxid FROM interface_gwport WHERE to_netboxid IS NOT NULL");
		while (rs.next()) {
			gwUplink.add(rs.getString("to_netboxid"));
		}

		rs = Database.query(
				"SELECT " +
				"  swp_netbox.netboxid," +
				"  catid," +
				"  swp_netbox.ifindex," +
				"  swp_netbox.to_netboxid," +
				"  swport.ifindex AS to_ifindex," +
				"  gwport.netboxid AS gwnetboxid " +
				"FROM " +
				"  swp_netbox " +
				"JOIN " +
				"  netbox USING (netboxid) " +
				"LEFT JOIN " +
				"  netboxprefix USING (netboxid) " +
				"LEFT JOIN " +
				"  gwportprefix" +
				"  ON (netboxprefix.prefixid = gwportprefix.prefixid AND " +
				"      (hsrp=true OR gwip::text IN (SELECT MIN(gwip::text) " +
				"                                   FROM gwportprefix " +
				"                                   GROUP BY prefixid " +
				"                                   HAVING COUNT(DISTINCT hsrp) = 1)" +
				"      )" +
				"     ) " +
				"LEFT JOIN " +
				"  interface_gwport AS gwport " +
				"  ON (gwport.interfaceid=gwportprefix.interfaceid) " +
				"LEFT JOIN " +
				"  interface_swport AS swport " +
				"  ON (swp_netbox.to_interfaceid = swport.interfaceid) " +
				"WHERE " +
				"  gwportprefix.interfaceid IS NOT NULL OR " +
				"  catid='GSW' " +
				"ORDER BY " +
				"  netboxid," +
				"  swp_netbox.ifindex"
				);




		Map bokser = new HashMap();
		List boksList = new ArrayList();
		List l = null;
		Set boksidSet = new HashSet();
		Set boksbakidSet = new HashSet();

		int previd = 0;
		while (rs.next()) {
			int boksid = rs.getInt("netboxid");
			if (boksid != previd) {
				// New box
				l = new ArrayList();
				boolean isSW = (rs.getString("catid").equals("SW") ||
												rs.getString("catid").equals("GW") ||
												rs.getString("catid").equals("GSW"));
				Boks b = new Boks(boksid, rs.getInt("gwnetboxid"), l, bokser, isSW, !gwUplink.contains(String.valueOf(boksid)) );
				boksList.add(b);
				previd = boksid;
			}
			String[] s = {
				rs.getString("ifindex"),
				rs.getString("to_netboxid"),
				rs.getString("to_ifindex")
			};
			l.add(s);

			boksidSet.add(new Integer(boksid));
			boksbakidSet.add(new Integer(rs.getInt("to_netboxid")));
		}

		int maxBehindMp=0;
		for (int i=0; i < boksList.size(); i++) {
			Boks b = (Boks)boksList.get(i);
			bokser.put(b.getBoksidI(), b);
			b.init();
			if (b.maxBehindMp() > maxBehindMp) maxBehindMp = b.maxBehindMp();
		}

		// Add all units we found only in boksbak (boxbehind)
		boksbakidSet.removeAll(boksidSet);
		Iterator iter = boksbakidSet.iterator();
		while (iter.hasNext()) {
			Integer boksbakid = (Integer)iter.next();

			String kat = (String)boksKat.get(boksbakid);
			if (kat == null) {
				errl("Error! kat not found for boksid: " + boksbakid);
			}
			boolean isSW = (kat.equals("SW") ||
							kat.equals("GW") ||
							kat.equals("GSW"));

			Boks b = new Boks(boksbakid.intValue(), 0, null, bokser, isSW, true);
			if (!bokser.containsKey(b.getBoksidI())) boksList.add(b);
			bokser.put(b.getBoksidI(), b);
			if (DEBUG_OUT) outl("Adding boksbak("+b.getBoksid()+"): <b>"+b.getName()+"</b><br>");
		}

		if (DEBUG_OUT) outl("Begin processing, maxBehindMp: <b>"+maxBehindMp+"</b><br>");

		for (int level=1; level <= maxBehindMp; level++) {
			boolean done = true;
			for (int i=0; i < boksList.size(); i++) {
				Boks b = (Boks)boksList.get(i);
				if (b.proc_mp(level)) done = false;
			}
			for (int i=0; i < boksList.size(); i++) {
				Boks b = (Boks)boksList.get(i);
				b.removeFromMp();
			}
			if (!done) {
				if (DEBUG_OUT) outl("Level: <b>"+level+"</b>, state changed.<br>");
			}
		}
		// Finally, we check the uplink ports, this will normally only be uplinks to -gw
		for (int i=0; i < boksList.size(); i++) {
			Boks b = (Boks)boksList.get(i);
			b.proc_mp(Boks.PROC_UPLINK_LEVEL);
		}

		if (DEBUG_OUT) outl("<b>BEGIN REPORT</b><br>");
		for (int i=0; i < boksList.size(); i++) {
			Boks b = (Boks)boksList.get(i);
			if (DEBUG_OUT) b.report();
			b.guess();
		}
		HashMap boksMp = new HashMap();
		for (int i=0; i < boksList.size(); i++) {
			Boks b = (Boks)boksList.get(i);
			b.addToMp(boksMp);
		}
		if (DEBUG_OUT) outl("Report done.<br>");

		// Now we loop through all the ports we've found boksbak (boxbehind) for, and update the table with these
		int newcnt=0,updcnt=0,resetcnt=0;
		ArrayList swport = new ArrayList();
		HashMap swrecMap = new HashMap();
		Map swrecSwportidMap = new HashMap();
		rs = Database.query("SELECT interfaceid,netboxid,link,speed,duplex,ifindex,ifalias as portname,to_netboxid,trunk,hexstring FROM interface_swport LEFT JOIN swportallowedvlan USING (interfaceid) ORDER BY netboxid,ifindex");
		ResultSetMetaData rsmd = rs.getMetaData();
		while (rs.next()) {
			HashMap hm = getHashFromResultSet(rs, rsmd);
			String link = rs.getString("link");
			if (link == null || link.toLowerCase().equals("y")) swport.add(hm);
			String key = rs.getString("netboxid")+":"+rs.getString("ifindex");
			swrecMap.put(key, hm);
			swrecSwportidMap.put(rs.getString("interfaceid"), hm);
		}

		if (DEBUG_OUT) outl("boksMp listing....<br>");
		iter = boksMp.entrySet().iterator();
		while (iter.hasNext()) {
			Map.Entry me = (Map.Entry)iter.next();
			String key = (String)me.getKey();
			//Integer boksbak = (Integer)me.getValue();
			BoksMpBak bmp = (BoksMpBak)me.getValue();

			StringTokenizer st = new StringTokenizer(key, ":");
			String boksid;
			String ifindex;
			try {
				boksid = st.nextToken();
				ifindex = st.nextToken();
			} catch (Exception e) {
				errl("Exception: " + e.getMessage() + " Key: " + key + " bmp: " + bmp);
				e.printStackTrace(System.err);
				return;
			}

			//outl(boksNavn.get(new Integer(boksid)) + " Modul: " + modul + " Port: " + port + " Link: " + boksNavn.get(boksbak) + "<br>");

			if (swrecMap.containsKey(key)) {
				// Record already exists, check if update is necessary
				HashMap swrec = (HashMap)swrecMap.get(key);
				//swrecMap.remove(key);
				swrec.put("deleted", null);

				String link = (String)swrec.get("link");
				if (link != null) link = link.toLowerCase();
				if ("n".equals(link)) continue; // Ignore non-up links

				String idbak = (String)swrec.get("to_netboxid");
				if (idbak == null || idbak != null && Integer.parseInt(idbak) != bmp.boksbak.intValue()) {
					// Update necessary
					updcnt++;
					// swport
					{
						String[] updateFields = {
							"to_netboxid", bmp.boksbak.toString()
						};
						String[] condFields = {
							"interfaceid", (String)swrec.get("interfaceid")
						};
						Database.update("interface", updateFields, condFields);
					}

					String vlan = "non-s";

					swrec.put("to_netboxid", bmp.boksbak.toString());
					swrec.put("change", "Updated ("+vlan+")");
				}

				// Then we must check whether swportbak (swportbehind) needs to be updated
				boolean swportbakOK = false;
				if (bmp.toIfindex != null) {
					// OK, look up in swportMap to find the correct swportid
					Map swrecBak = (Map)swrecMap.get(bmp.hashKey());
					if (swrecBak != null) {
						swportbakOK = true;
						String new_swportbak = (String)swrecBak.get("interfaceid");
						String cur_swportbak = (String)swrec.get("to_interfaceid");

						if (cur_swportbak == null || !cur_swportbak.equals(new_swportbak)) {
							String[] updateFields = {
								"to_interfaceid", new_swportbak
							};
							String[] condFields = {
								"interfaceid", (String)swrec.get("interfaceid")
							};
							Database.update("interface", updateFields, condFields);
						}
					} else {
						// Error!
						outl("<font color=\"red\">ERROR:</font> Could not find record in interface,  boks("+bmp.boksbak+"): <b>" + boksNavn.get(bmp.boksbak) + "</b> Ifindex: <b>" + bmp.toIfindex + "</b> boksbak: <b>" + boksNavn.get(new Integer(boksid)) + "</b> ("+bmp.hashKey()+")<br>");
					}
				}

				// Then we must check whether we have a trunk without allowedvlan
				if ("t".equals(swrec.get("trunk")) && (swrec.get("hexstring") == null || swrec.get("hexstring").equals("")) ) {
					// We have a trunk that is static or is missing hexstring, then we just grab and insert the hexstring from the other end

					Boks b = (Boks)bokser.get(bmp.boksbak);
					//Mp mpBak = b.getMpTo(Integer.parseInt(boksid), modul, port);
					String toIfindex = b.getIfindexTo(Integer.parseInt(boksid), ifindex);
					if (toIfindex != null) {
						// Port on the other end found, but does it exist in the table?
						String keyBak = bmp.boksbak+":"+toIfindex;
						if (swrecMap.containsKey(keyBak)) {
							// Exists, check whether it is a trunk port
							HashMap swrecBak = (HashMap)swrecMap.get(keyBak);
							if ("t".equals(swrecBak.get("trunk"))) {
								// Trunk, check if we need to update swportallowedvlan
								String allowedVlan = (String)swrec.get("hexstring");
								String allowedVlanBak = (String)swrecBak.get("hexstring");
								if (allowedVlan == null || allowedVlan.length() == 0) {
									if (allowedVlanBak == null || allowedVlanBak.length() == 0) {
										// Error! Now we are in big trouble, there's a static trunk on both ends...
										outl("<font color=\"red\">ERROR:</font> Link is trunk with no swportallowedvlan on either side! boks: " + boksNavn.get(new Integer(boksid)) + " Ifindex: " + ifindex+ " boksBak: " + boksNavn.get(bmp.boksbak) + " ToIfindex: " + swrecBak.get("ifindex") + "<br>");

									} else {
										// Now we must insert a new record into swportallowedvlan
										String[] fields = {
											"interfaceid", (String)swrec.get("interfaceid"),
											"hexstring", allowedVlanBak
										};
										if (DEBUG_OUT) outl("Inserting new record in swportallowedvlan, interfaceid: " + swrec.get("interfaceid") + " new hexstring: " + allowedVlanBak + "<br>");
										boolean update = false;
										try {
											Database.insert("swportallowedvlan", fields);
										} catch (SQLException e) {
											// Woops, try to update instead
											update = true;
										}
										if (update) try {
											outl("<font color=\"red\">ERROR:</font> swportallowedvlan seems to already have an empty record! Trying to update instead...<br>");
											Database.update("UPDATE swportallowedvlan SET hexstring='"+allowedVlanBak+"' WHERE interfaceid='"+swrec.get("interfaceid")+"'");
										} catch (SQLException e) {
											outl("<font color=\"red\">ERROR:</font> Cannot update swportallowedvlan, SQLException: " + e.getMessage() + "<br>");
										}
									}

								} else if (!allowedVlan.equals(allowedVlanBak)) {
									// Update necessary
									String[] updateFields = {
										"hexstring", allowedVlanBak
									};
									String[] condFields = {
										"interfaceid", (String)swrec.get("interfaceid")
									};
									Database.update("swportallowedvlan", updateFields, condFields);
									if (DEBUG_OUT) outl("Updated swportallowedvlan, interfaceid: " + condFields[0] + " old hexstring: " + allowedVlan + " new hexstring: " + allowedVlanBak + "<br>");
								}
							} else {
								// Error, trunk<->non-trunk!
								outl("<font color=\"red\">ERROR:</font> Link is trunk / non-trunk: boks: " + boksNavn.get(new Integer(boksid)) + " Ifindex: " + ifindex + " boksBak: " + boksNavn.get(bmp.boksbak) + " ToIfindex: " + swrecBak.get("ifindex") + "<br>");
							}
						}
					}
				}


			} else {
				// This is now an error which should not occur! :-)  (Wow, an eror that shouldn't occur, what a grand concept!)
				outl("<font color=\"red\">ERROR:</font> Could not find record for other side of link! boks("+boksid+"): <b>" + boksNavn.get(new Integer(boksid)) + "</b> Ifindex: <b>" + ifindex + "</b> boksBak: <b>" + boksNavn.get(bmp.boksbak) + "</b><br>");

			}

		}
		if (DEBUG_OUT) outl("boksMp listing done.<br>");

		iter = swrecMap.entrySet().iterator();
		while (iter.hasNext()) {
			Map.Entry me = (Map.Entry)iter.next();
			String key = (String)me.getKey();
			HashMap swrec = (HashMap)me.getValue();

			String swportid = (String)swrec.get("interfaceid");
			String boksbak = (String)swrec.get("to_netboxid");
			String swportbak = (String)swrec.get("to_interfaceid");

			if (swportbak != null && swportbak.length() > 0) {
				boolean reset = false;
				if (boksbak == null || boksbak.length() == 0) {
					reset = true;
				} else {
					Map swrecBak = (Map)swrecSwportidMap.get(swportbak);
					if (swrecBak == null || !boksbak.equals(swrecBak.get("netboxid"))) {
						reset = true;
					}
				}

				if (reset) {
					resetcnt++;
					// Set fields to null
					String[] updateFields = {
						"to_interfaceid", "null"
					};
					String[] condFields = {
						"interfaceid", swportid
					};
					Database.update("interface", updateFields, condFields);
					if (DEBUG_OUT) outl("Want to reset boxbehind(2) for interfaceid: " + swportid + "<br>");
					swportbak = null;
				}
			}

			if (swrec.containsKey("deleted")) continue;


			if (boksbak != null && boksbak.length() > 0) {
				// Set to null
				resetcnt++;
				String[] updateFields = {
					"to_netboxid", "null",
					"to_interfaceid", "null"
				};
				String[] condFields = {
					"interfaceid", swportid
				};
				Database.update("interface", updateFields, condFields);
				if (DEBUG_OUT) outl("Want to reset boxbehind for interfaceid: " + swportid + "<br>");
			}
			else if (swportbak != null && swportbak.length() > 0) {
				// Set fields to null
				resetcnt++;
				String[] updateFields = {
					"to_interfaceid", "null"
				};
				String[] condFields = {
					"interfaceid", swportid
				};
				Database.update("interface", updateFields, condFields);
				if (DEBUG_OUT) outl("Want to reset swportbehind for interfaceid: " + swportid + "<br>");
			}

		}

		outl("<table>");
		outl("  <tr>");
		outl("    <td><b>swpid</b></td>");
		outl("    <td><b>boksid</b></td>");
		outl("    <td><b>sysName</b></td>");
		outl("    <td><b>typeId</b></td>");
		outl("    <td><b>Speed</b></td>");
		outl("    <td><b>Duplex</b></td>");
		outl("    <td><b>Ifindex</b></td>");
		outl("    <td><b>Portnavn</b></td>");
		outl("    <td><b>Boksbak</b></td>");
		outl("    <td><b>Change (vlan)</b></td>");
		outl("  </tr>");

		int attCnt=0;
		for (int i=0; i < swport.size(); i++) {
			HashMap swrec = (HashMap)swport.get(i);
			String boksid = (String)swrec.get("netboxid");
			String ifindex = (String)swrec.get("ifindex");
			String portnavn = (String)swrec.get("portname");
			//boolean isStatic = swrec.get("static").equals("t");
			String change = (String)swrec.get("change");

			if (portnavn == null) portnavn = "";

			String boksbak = "";
			//Integer idbak = (Integer)boksMp.get(boksid+":"+modul+":"+port);
			BoksMpBak bmp = (BoksMpBak)boksMp.get(boksid+":"+ifindex);
			Integer idbak = (bmp != null) ? bmp.boksbak : null;
			if (idbak != null) boksbak = (String)boksNavn.get(idbak);
			if (boksbak == null) {
				outl("ERROR! boksbak is null for idbak: " + idbak + "<br>");
				continue;
			}

			String color = "gray";
			if (change != null && change.startsWith("Error")) {
				color = "red";
			} else
			if (portnavn.length() == 0 && boksbak.length()>0) {
				color = "blue";
			} else
			if (portnavn.length() > 0 && boksbak.length()==0) {
				if (portnavn.indexOf("-h") != -1 || portnavn.indexOf("-sw") != -1 || portnavn.indexOf("-gw") != -1) {
					color = "purple";
				}
			} else
			if (portnavn.length() > 0 && boksbak.length()>0 && portnavn.endsWith(boksbak) ) {
				color = "green";
			} else
			if (portnavn.length() > 0 && boksbak.length()>0 && !portnavn.endsWith(boksbak) ) {
				color = "red";
			}

			if (!color.equals("purple") && !color.equals("red")) continue;
			if (portnavn.length() > 2 && portnavn.charAt(0) == 'n' && portnavn.charAt(2) == ':') continue;

			attCnt++;
			String color1 = "<font color="+color+">";
			String color2 = "</font>";

			outl("<tr>");
			//outl("<td align=right>"+color1+ swrec.get("swportid") + color2+"</td>");
			outl("<td align=right><a href=\"#" + swrec.get("interfaceid") + "\">" + swrec.get("interfaceid") + "</a></td>");
			outl("<td align=right>"+color1+ swrec.get("netboxid") + color2+"</td>");
			outl("<td>"+color1+ boksNavn.get(new Integer((String)swrec.get("netboxid"))) + color2+"</td>");
			outl("<td>"+color1+ boksType.get(new Integer((String)swrec.get("netboxid"))) + color2+"</td>");
			outl("<td align=right>"+color1+ swrec.get("speed") + color2+"</td>");
			outl("<td align=right>"+color1+ swrec.get("duplex") + color2+"</td>");
			outl("<td align=right>"+color1+ swrec.get("ifindex") + color2+"</td>");
			outl("<td>"+color1+ portnavn + color2+"</td>");
			outl("<td>"+color1+ boksbak + color2+"</td>");

			if (change != null) outl("<td><b>"+change+"</b></td>");

			outl("</tr>");
		}
		outl("</table>");
		outl("Found <b>" + attCnt + "</b> rows in need of attention.<br>");

		outl("<h2>swport:</h2>");
		outl("<table>");
		outl("  <tr>");
		outl("    <td><b>swpid</b></td>");
		outl("    <td><b>boksid</b></td>");
		outl("    <td><b>sysName</b></td>");
		outl("    <td><b>Speed</b></td>");
		outl("    <td><b>Duplex</b></td>");
		outl("    <td><b>Ifindex</b></td>");
		outl("    <td><b>Portnavn</b></td>");
		outl("    <td><b>Boksbak</b></td>");
		outl("    <td><b>Change (vlan)</b></td>");
		outl("  </tr>");

		for (int i=0; i < swport.size(); i++) {
			HashMap swrec = (HashMap)swport.get(i);
			String boksid = (String)swrec.get("netboxid");
			String ifindex = (String)swrec.get("ifindex");
			String portnavn = (String)swrec.get("portname");
			//boolean isStatic = swrec.get("static").equals("t");
			String change = (String)swrec.get("change");

			if (portnavn == null) portnavn = "";

			String boksbak = "";
			BoksMpBak bmp = (BoksMpBak)boksMp.get(boksid+":"+ifindex);
			Integer idbak = (bmp != null) ? bmp.boksbak : null;
			if (idbak != null) boksbak = (String)boksNavn.get(idbak);
			if (boksbak == null) {
				outl("ERROR! boksbak is null for idbak: " + idbak + "<br>");
				continue;
			}

			// Because of too high volume, EDGE equipment with empty portnames and boksbak (boxbehind) are not included in the list
			if (boksKat.get(new Integer(boksid)) == null) {
				System.err.println("ERROR, boksKat is null for boksid: " + boksid);
				continue;
			}
			if (((String)boksKat.get(new Integer(boksid))).equalsIgnoreCase("edge") && portnavn.length() == 0 && boksbak.length() == 0) continue;

			String color = "gray";
			if (change != null && change.startsWith("Error")) {
				color = "red";
			} else
			if (portnavn.length() == 0 && boksbak.length()>0) {
				color = "blue";
			} else
			if (portnavn.length() > 0 && boksbak.length()==0) {
				if (portnavn.indexOf("-h") != -1 || portnavn.indexOf("-sw") != -1 || portnavn.indexOf("-gw") != -1) {
					color = "purple";
				}
			} else
			if (portnavn.length() > 0 && boksbak.length()>0 && portnavn.endsWith(boksbak) ) {
				color = "green";
			} else
			if (portnavn.length() > 0 && boksbak.length()>0 && !portnavn.endsWith(boksbak) ) {
				color = "red";
			}

			String color1 = "<font color="+color+">";
			String color2 = "</font>";

			outl("<tr><a name=\"" + swrec.get("interfaceid") + "\">");
			outl("<td align=right>"+color1+ swrec.get("interfaceid") + color2+"</td>");
			outl("<td align=right>"+color1+ swrec.get("netboxid") + color2+"</td>");
			outl("<td>"+color1+ boksNavn.get(new Integer((String)swrec.get("netboxid"))) + color2+"</td>");
			outl("<td align=right>"+color1+ swrec.get("speed") + color2+"</td>");
			outl("<td align=right>"+color1+ swrec.get("duplex") + color2+"</td>");
			outl("<td align=right>"+color1+ swrec.get("ifindex") + color2+"</td>");
			outl("<td>"+color1+ portnavn + color2+"</td>");
			outl("<td>"+color1+ boksbak + color2+"</td>");

			if (change != null) outl("<td><b>"+change+"</b></td>");

			outl("</tr>");
		}
		outl("</table>");

		//outl("New rows: <b>" + newcnt + "</b> Updated rows: <b>" + updcnt + "</b> Removed rows: <b>"+remcnt+"</b><br>");
		outl("New rows: <b>" + newcnt + "</b> Updated rows: <b>" + updcnt + "</b><br>");
		outl("Sum rows: <b>" + swport.size() + "</b><br>");


		outl("All done.<br>");

	}

	private HashMap getHashFromResultSet(ResultSet rs, ResultSetMetaData md) throws SQLException
	{
		HashMap hm = new HashMap();
		for (int i=md.getColumnCount(); i > 0; i--) {
			hm.put(md.getColumnName(i), rs.getString(i));
		}
		return hm;
	}

	/**
	 * avledVlan means "derive vlan"
	 */
	public void avledVlan() throws SQLException
	{
		boolean DB_UPDATE = true;
		boolean DB_COMMIT = true;
		boolean DEBUG_OUT = false;
		boolean TIME_OUT = true;

		long beginTime;

		//String debugParam = com.getp("debug");
		if (debugParam != null && debugParam.equals("yes")) DEBUG_OUT = true;
		if (DEBUG_OUT) outl("Begin<br>");

		// Show date
		{
			java.util.Date currentTime = new GregorianCalendar().getTime();
			outl("Generated on: <b>" + currentTime + "</b><br>");
		}

		// We start by setting boksbak (boxbehind) to null everywhere status='down', so we avoid loops
		{
			Database.update("UPDATE interface SET to_netboxid = NULL, to_interfaceid = NULL WHERE ifoperstatus <> 1 AND to_netboxid IS NOT NULL");
		}

		// Find mapping for firewalled VLANs
		Map fwVlanMap = new HashMap();
		{
			beginTime = System.currentTimeMillis();
			ResultSet rs = Database.query("select vlan,netaddr from vlan join prefix using(vlanid) where vlan not in (select vlan from interface where vlan is not null) and nettype='lan' and prefixid in (select prefixid from arp where end_time='infinity' and mac not in (select mac from netboxmac))", true);
			while (rs.next()) {
				String vlan = rs.getString("vlan");
				String netaddr = rs.getString("netaddr");
				ResultSet rs2 = Database.query("select cam.sysname,cam.netboxid,cam.ifindex,vlan from arp join cam using(mac) join interface_swport AS swport on (swport.netboxid=cam.netboxid AND swport.ifindex=cam.ifindex) where ip << '" + netaddr + "' and cam.end_time='infinity' and arp.end_time='infinity' and (trunk=false or trunk is null) and vlan > 1");
				if (rs2.next()) {
					fwVlanMap.put(vlan, rs2.getString("vlan"));
				}
			}
			Database.free(rs);
			if (TIME_OUT) outl("Spent " + (System.currentTimeMillis()-beginTime) + " ms finding firewalled VLAN mappings (found " + fwVlanMap.size() + " mappings: " + fwVlanMap + ")<br>");
		}

		beginTime = System.currentTimeMillis();

		Map dataStructs = new HashMap();

		// This is really only necessary for debugging
		HashMap boksName = new HashMap();
		ResultSet rs = Database.query("SELECT netboxid,sysname FROM netbox");
		while (rs.next()) boksName.put(rs.getString("netboxid"), rs.getString("sysname"));

		Map vlanidVlan = new HashMap();
		Map vlanidNettype = new HashMap();
		rs = Database.query("SELECT vlanid,vlan,nettype FROM vlan");
		while (rs.next()) {
			if (rs.getString("vlan") != null) vlanidVlan.put(rs.getString("vlanid"), rs.getString("vlan"));
			vlanidNettype.put(rs.getString("vlanid"), rs.getString("nettype"));
		}

		// Need to know what boxes are GW, all links to these are 'o', and those are not to be traversed
		HashSet boksGwSet = new HashSet();
		rs = Database.query("SELECT netboxid FROM netbox WHERE catid IN ('GW', 'v6GW')");
		while (rs.next()) boksGwSet.add(rs.getString("netboxid"));

		// Overview of which vlans are active on a swport connected to a gw
		Map swportGwVlanMap = new HashMap();
		rs = Database.query("SELECT DISTINCT to_interfaceid,vlan.vlan,interfaceid FROM interface JOIN gwportprefix USING(interfaceid) JOIN prefix USING(prefixid) JOIN vlan USING(vlanid) WHERE to_interfaceid IS NOT NULL AND vlan.vlan IS NOT NULL");
		while (rs.next()) swportGwVlanMap.put(rs.getString("to_interfaceid")+":"+rs.getString("vlan"), rs.getString("interfaceid"));

		// Mapping from gwportid to the running vlanid and prefixid (needed for updating)
		Map gwportVlanidMap = new HashMap();
		rs = Database.query("SELECT DISTINCT interfaceid,vlanid,netboxid FROM interface JOIN gwportprefix USING(interfaceid) JOIN prefix USING(prefixid) JOIN vlan USING(vlanid) WHERE to_interfaceid IS NOT NULL");
		while (rs.next()) gwportVlanidMap.put(rs.getString("interfaceid"), new String[] { rs.getString("vlanid"), rs.getString("netboxid") } );

		// Overview of which links:vlan are blocked by spanning tree
		HashSet spanTreeBlocked = new HashSet();
		rs = Database.query("SELECT interfaceid,vlan FROM swportblocked");
		while (rs.next()) spanTreeBlocked.add(rs.getString("interfaceid")+":"+rs.getString("vlan"));

		// Overview of non-trunks going out from each box, per vlan
		HashMap nontrunkVlan = new HashMap();
		rs = Database.query("SELECT interfaceid,netboxid,to_netboxid,to_interfaceid,COALESCE(vlan,1) AS vlan FROM interface_swport WHERE (trunk='f' OR trunk IS NULL) AND to_netboxid IS NOT NULL");
		while (rs.next()) {
			HashMap nontrunkMap;
			String key = rs.getString("netboxid")+":"+rs.getString("vlan");
			if ( (nontrunkMap = (HashMap)nontrunkVlan.get(key)) == null) {
				nontrunkMap = new HashMap();
				nontrunkVlan.put(key, nontrunkMap);
			}
			HashMap hm = new HashMap();
			hm.put("interfaceid", rs.getString("interfaceid"));
			hm.put("netboxid", rs.getString("netboxid"));
			hm.put("to_netboxid", rs.getString("to_netboxid"));
			String toid = rs.getString("to_interfaceid") != null ? rs.getString("to_interfaceid") : rs.getString("to_netboxid");
			nontrunkMap.put(toid, hm);
		}

		// First, we need to retrieve an overview of which VLANs are allowed on each port
		HashMap allowedVlan = new HashMap();
		rs = Database.query("SELECT interface_swport.netboxid,interfaceid,module.name as module_name,baseport,to_netboxid,hexstring FROM interface_swport LEFT JOIN module USING(moduleid) JOIN swportallowedvlan USING (interfaceid) WHERE to_netboxid IS NOT NULL ORDER BY to_netboxid");

		while (rs.next()) {
			HashMap boksAllowedMap;
			String boksid = rs.getString("netboxid");
			if ( (boksAllowedMap = (HashMap)allowedVlan.get(boksid)) == null) {
				boksAllowedMap = new HashMap();
				allowedVlan.put(boksid, boksAllowedMap);
			}
			HashMap hm = new HashMap();
			hm.put("interfaceid", rs.getString("interfaceid"));
			hm.put("netboxid", rs.getString("netboxid"));
			hm.put("module", rs.getString("module_name"));
			hm.put("port", rs.getString("baseport"));
			hm.put("to_netboxid", rs.getString("to_netboxid"));
			hm.put("hexstring", rs.getString("hexstring"));

			String boksbak = rs.getString("to_netboxid");
			if (boksAllowedMap.containsKey(boksbak)) outl("<font color=red>WARNING</font>: Multiple trunks between <b>"+boksName.get(boksid)+"</b> and <b>"+boksName.get(boksbak)+"</b><br>");
			boksAllowedMap.put(boksbak, hm);
		}

		// We need to know which VLANs go out on non-trunk ports from a given box
		// We use a HashMap of HashSets
		HashMap activeVlan = new HashMap();
		// VLAN is active on port, even if port is down, and we must include the VLAN of the IP address of the box itself 
		rs = Database.query("SELECT DISTINCT interfaceid,netboxid,COALESCE(vlan,1) AS vlan FROM interface_swport WHERE (trunk='f' OR trunk IS NULL) AND to_netboxid IS NULL");
		while (rs.next()) {
			Map m;
			String netboxid = rs.getString("netboxid");
			if ((m = (Map)activeVlan.get(netboxid)) == null) activeVlan.put(netboxid, m = new HashMap());
			
			Set s;
			if ((s = (Set)m.get(new Integer(rs.getInt("vlan")))) == null) m.put(new Integer(rs.getInt("vlan")), s = new HashSet());
			s.add(rs.getString("interfaceid"));
		}

		// The VLAN of the netbox' IP should also be added to activeVlan
		rs = Database.query("SELECT netboxid,vlan FROM netbox LEFT JOIN netboxprefix USING (netboxid) JOIN prefix USING(prefixid) JOIN vlan USING(vlanid) WHERE vlan IS NOT NULL");
		while (rs.next()) {
			Map m;
			String netboxid = rs.getString("netboxid");
			if ((m = (Map)activeVlan.get(netboxid)) == null) activeVlan.put(netboxid, m = new HashMap());

			Integer vl = new Integer(rs.getInt("vlan"));
			if (!m.containsKey(vl)) m.put(vl, new HashSet());
		}

		// Mapping of which swport is connected to another swport
		HashMap swportidMap = new HashMap();
		rs = Database.query("SELECT interfaceid,COALESCE(vlan,1) AS vlan,to_interfaceid FROM interface_swport WHERE (trunk='f' OR trunk IS NULL) AND to_interfaceid IS NOT NULL");
		while (rs.next()) {
			HashMap hm = new HashMap();
			hm.put("vlan", rs.getString("vlan"));
			hm.put("to_interfaceid", rs.getString("to_interfaceid"));
			swportidMap.put(rs.getString("interfaceid"), hm);
		}

		// Mapping of which VLAN that runs between two boxes where we do not have to_interfaceid
		Map nbvlanMap = new HashMap();
		dataStructs.put("nbvlanMap", nbvlanMap);
		rs = Database.query("SELECT netboxid,to_netboxid,COALESCE(vlan,1) AS vlan FROM interface_swport WHERE (trunk='f' OR trunk IS NULL) AND to_netboxid IS NOT NULL AND to_interfaceid IS NULL ORDER BY netboxid");
		while (rs.next()) {
			String key = rs.getString("netboxid")+":"+rs.getString("to_netboxid");
			if (nbvlanMap.containsKey(key)) {
				outl("<font color=red>WARNING</font>: Multiple links between <b>"+boksName.get(rs.getString("netboxid"))+"</b> and <b>"+boksName.get(rs.getString("to_netboxid"))+" without exact swport knowledge (interfaceid)</b><br>");
			} else {
				nbvlanMap.put(key, rs.getString("vlan"));
			}
		}


		// Using cam/arp to check VLAN behind a netbox/ifindex (when we come from trunk)
		Map swportidVlanMap = new HashMap();
		Set swportidVlanDupeSet = new HashSet();
		dataStructs.put("swportidVlanMap", swportidVlanMap);
		rs = Database.query("SELECT interfaceid,vlanid,COUNT(*) AS count FROM interface_swport AS swport JOIN cam ON (swport.netboxid = cam.netboxid AND swport.ifindex = cam.ifindex and cam.end_time = 'infinity') JOIN arp ON (cam.mac = arp.mac AND arp.end_time = 'infinity') JOIN prefix ON (arp.prefixid = prefix.prefixid) JOIN vlan USING(vlanid) WHERE (trunk='f' OR trunk IS NULL) GROUP BY interfaceid,vlanid ORDER BY interfaceid,count DESC");
		while (rs.next()) {
			String key = rs.getString("interfaceid")+":"+rs.getString("vlanid");
			if (swportidVlanDupeSet.add(key)) {
				swportidVlanMap.put(rs.getString("interfaceid"), rs.getString("vlanid"));
			} else {
				outl("<font color=red>WARNING</font>: Multiple VLANs detected behind non-trunk port (interfaceid="+rs.getString("interfaceid")+", vlanid="+rs.getString("vlanid")+")<br>");
			}
		}

		if (TIME_OUT) outl("Spent " + (System.currentTimeMillis()-beginTime) + " ms fetching data from db<br>");

		// Then we retrieve all VLANs and which switch the VLAN "starts at"
		outl("<pre>");

		beginTime = System.currentTimeMillis();
		rs = Database.query("SELECT DISTINCT netbox.netboxid,vlanid,vlan.vlan,sysname,gwport.interfaceid,gwport.to_netboxid,gwport.to_interfaceid,swport.trunk,hexstring FROM prefix JOIN vlan USING(vlanid) JOIN gwportprefix ON (prefix.prefixid = gwportprefix.prefixid AND (hsrp='t' OR gwip::text IN (SELECT MIN(gwip::text) FROM gwportprefix GROUP BY prefixid HAVING COUNT(DISTINCT hsrp) = 1))) JOIN interface_gwport AS gwport USING(interfaceid) JOIN netbox USING (netboxid) LEFT JOIN interface_swport AS swport ON (gwport.to_interfaceid=swport.interfaceid) LEFT JOIN swportallowedvlan ON (swport.interfaceid = swportallowedvlan.interfaceid) WHERE (gwport.to_netboxid IS NOT NULL OR catid='GSW') AND vlan.vlan IS NOT NULL ORDER BY vlan.vlan");

		Set vlansWithRouter = new HashSet();
		while (rs.next()) {
			vlansWithRouter.add(rs.getString("vlan"));
		}
		rs.beforeFirst();

		ArrayList trunkVlan = new ArrayList();
		Set doneVlan = new HashSet();
		Set visitedNodeSet = new HashSet(); // The set of nodes we've visited; reset for each VLAN
		Set foundGwSet = new HashSet();
		// ***** BEGIN DEPTH FIRST SEARCH ***** //
		while (rs.next()) {
			int vlan = rs.getInt("vlan");
			if (fwVlanMap.containsKey(""+vlan) && !vlansWithRouter.contains(fwVlanMap.get(""+vlan))) {
				if (DEBUG_OUT) outl("Mapping vlan " + vlan + " to " + fwVlanMap.get(""+vlan));
				vlan = Integer.parseInt((String)fwVlanMap.get(""+vlan));
			}
			int vlanid = rs.getInt("vlanid");
 			String boksid = rs.getString("netboxid");
			String nettype = (String)vlanidNettype.get(""+vlanid);
			doneVlan.add(""+vlan);

			visitedNodeSet.clear();

			String netaddr = "NA";
			String boksbak = rs.getString("to_netboxid");
			if (boksbak == null || boksbak.length() == 0) boksbak = boksid; // Spesialtilfelle for GSW enheter
			String swportbak = rs.getString("to_interfaceid");
			boolean cameFromTrunk = rs.getBoolean("trunk");
			String hexstring = rs.getString("hexstring");
			if (DEBUG_OUT) outl("\n<b>NEW VLAN: " + vlan + "</b> (netaddr: <b>"+netaddr+"</b>)<br>");

			// Check whether there is a trunk or non-trunk down to the GW
			if (cameFromTrunk) {
				// Now we expect a hexstring to be in place
				if (hexstring == null) {
					if (DEBUG_OUT) outl("\n<b>AllowedVlan hexstring for trunk down to switch is missing, skipping...</b><br>");
					continue;
				}
				// Verify that the VLAN is actually are allowed on the trunk
				if (!isAllowedVlan(hexstring, vlan)) {
					if (DEBUG_OUT) outl("\n<b>Vlan is not allowed on trunk down to switch, and there is no non-trunk, skipping...</b><br>");
					continue;
				}
			}
			
			// List of gwports we have uplink to
			List foundGwports = new ArrayList();

			if (vlanTraverseLink(vlan, vlanid, boksid, boksbak, cameFromTrunk, true, nontrunkVlan, allowedVlan, activeVlan, swportidMap, spanTreeBlocked, trunkVlan, dataStructs, foundGwports, visitedNodeSet, 0, DEBUG_OUT, boksGwSet, swportGwVlanMap, boksName)) {

				// The vlan is active on this unit, so we add it
				if (swportbak != null) {
					String[] tvlan = {
						swportbak,
						String.valueOf(vlanid),
						"o"
					};
					trunkVlan.add(tvlan);
				}

				// If any gwports use a different vlanid we must change it to the current one
				for (Iterator it = foundGwports.iterator(); it.hasNext();) {
					String gwportid = (String)it.next();
					String[] vlanPrefix = (String[])gwportVlanidMap.get(gwportid);
					String oldVlanid = vlanPrefix[0];
					String gwNetboxid = vlanPrefix[1];
					foundGwSet.add(gwNetboxid+":"+vlanid);
					if (vlanid != Integer.parseInt(oldVlanid)) {
						// Swap in prefix
						Database.update("UPDATE prefix SET vlanid="+vlanid+" WHERE prefixid IN (SELECT prefixid FROM gwportprefix WHERE interfaceid="+gwportid+")");
					}
				}
			}


		}
		outl("</pre>");

		if (TIME_OUT) outl("Spent " + (System.currentTimeMillis()-beginTime) + " ms traversing VLANs from router<br>");

		// XXX: The below commented out code is an attempt at support for private (i.e. non-routed) VLANs.
		//      Unfortunately it does not work at all and has an ugly tendency to mess up people's NAV installs,
		//      thus its current commented out state. May be cleaned up at some future date.
		/*
		outl("\n<b>VLANs with no router to start from:</b><br>");
		outl("<pre>");

		updateVlanDb(trunkVlan, vlanidVlan, allowedVlan, boksName, false);

		beginTime = System.currentTimeMillis();

		// All VLANs we cannot find a starting point for, where we actually need to start everywhere to be sure we find everything
		// SELECT DISTINCT ON (vlan,boksid) boksid,modul,port,boksbak,vlan,trunk FROM swport NATURAL JOIN swportvlan WHERE vlan NOT IN (SELECT DISTINCT vlan FROM (prefiks JOIN gwport USING (prefiksid)) JOIN boks USING (boksid) WHERE boksbak IS NOT NULL AND vlan IS NOT NULL) AND boksbak IS NOT NULL ORDER BY vlan,boksid
		if (DEBUG_OUT) outl("\n<b><h3>VLANs with no router to start from:</h3></b><br>");
		{
			// Delete mismatching ports
			// DELETE FROM swport WHERE swportid IN (SELECT swportid FROM swport JOIN swportvlan USING(swportid) JOIN vlan USING(vlanid) WHERE vlan.vlan != swport.vlan AND direction IN ('x','u'))
			String[] vlansDone = util.stringArray(doneVlan);
			String vlansDoneS = "";
			if (vlansDone.length > 0) {
				Arrays.sort(vlansDone);
				vlansDoneS = "AND vlan NOT IN (" + util.join(vlansDone, ",") + ")";
			}
			//String sql = "SELECT swportid,vlan,vlanid,sysname,to_netboxid,to_swportid,trunk FROM swport JOIN module USING(moduleid) JOIN netbox ON (to_netboxid=netbox.netboxid) LEFT JOIN swportvlan USING(swportid) WHERE vlan NOT IN (" + util.join(vlansDone, ",") + ") AND to_netboxid IS NOT NULL AND vlan IS NOT NULL AND (direction IS NULL OR direction IN ('x','u')) ORDER BY vlan, vlanid";
			String sql = "SELECT DISTINCT netboxid,vlan,vlanid,sysname FROM swport JOIN module USING(moduleid) JOIN netbox USING (netboxid) LEFT JOIN swportvlan USING(swportid) WHERE vlan IS NOT NULL " + vlansDoneS + " AND link='y' AND trunk!=TRUE AND (direction IS NULL OR direction IN ('x','u')) ORDER BY vlan DESC, vlanid";
			rs = Database.query(sql);
			outl("SQL: " + sql);
			int prevvlan=-1;
			int vlanid = -1;
			HashSet visitNode = null;
			while (rs.next()) {
				int vlan = rs.getInt("vlan");
				if (vlan != prevvlan) {
					visitNode = new HashSet();
					prevvlan = vlan;
					vlanid = rs.getInt("vlanid");
					if (vlanid == 0) {
						String[] ins = new String[] {
							"vlanid", "",
							"vlan", ""+vlan,
							"nettype", "lan"
						};
						vlanid = Integer.parseInt(Database.insert("vlan", ins, null));
						vlanidVlan.put(""+vlanid, ""+vlan);
						outl("\n<b>CREATE NEW VLAN: " + vlan + "</b>, vlanid="+vlanid+", starting from <b>"+rs.getString("sysname")+"</b><br>");
					} else {
						outl("\n<b>NEW VLAN: " + vlan + "</b>, vlanid="+vlanid+", starting from <b>"+rs.getString("sysname")+"</b><br>");
					}
				}
				if (visitNode.contains(rs.getString("netboxid"))) continue;
				vlanTraverseLink(vlan, vlanid, null, rs.getString("netboxid"), false, false, nontrunkVlan, allowedVlan, activeVlan, swportidMap, spanTreeBlocked, trunkVlan, dataStructs, new ArrayList(), visitNode, 0, DEBUG_OUT, boksGwSet, swportGwVlanMap, boksName);


			}
		}

		outl("</pre>");
		if (TIME_OUT) outl("Spent " + (System.currentTimeMillis()-beginTime) + " ms traversing VLANs with no router<br>");
		*/
		
		Map activeOnTrunk = updateVlanDb(trunkVlan, vlanidVlan, allowedVlan, boksName, true);

		// Then we report mismatches between swportallowedvlan and what is actually active
		outl("<h2>Allowed, but non-active VLANs:</h2>");
		outl("<h4>(<i><b>Note</b>: VLANs 1 and 1000-1005 are for interswitch control traffic and are always allowed</i>)</h4>");
		int allowedcnt=0, totcnt=0;
		Iterator iter = allowedVlan.values().iterator();
		while (iter.hasNext()) {
			HashMap boksAllowedMap = (HashMap)iter.next();
			Iterator iter2 = boksAllowedMap.values().iterator();
			while (iter2.hasNext()) {
				HashMap hm = (HashMap)iter2.next();
				String swportid = (String)hm.get("interfaceid");
				String hexstring = (String)hm.get("hexstring");

				HashSet activeVlanOnTrunk = (HashSet)activeOnTrunk.get(swportid);
				if (activeVlanOnTrunk == null) {
					//outl("ERROR, swrecTrunk is missing for swportid: " + swportid + "<br>");
					continue;
				}
				totcnt++;

				String boksid = (String)hm.get("netboxid");
				String modul = (String)hm.get("module");
				String port = (String)hm.get("port");
				String boksbak = (String)hm.get("to_netboxid");
				boolean printMsg = false;

				int startRange=0;
				boolean markLast=false;
				int MIN_VLAN = 2;
				int MAX_VLAN = 999;
				for (int i=MIN_VLAN; i <= MAX_VLAN+1; i++) {
					if (isAllowedVlan(hexstring, i) && !activeVlanOnTrunk.contains(String.valueOf(i)) && i != MAX_VLAN+1 ) {
						if (!markLast) {
							startRange=i;
							markLast = true;
						}
					} else {
						if (markLast) {
							String range = (startRange==i-1) ? String.valueOf(i-1) : startRange+"-"+(i-1);
							if (!printMsg) {
								allowedcnt++;
								outl("Working with trunk From("+boksid+"): <b>"+boksName.get(boksid)+"</b>, Modul: <b>"+modul+"</b> Port: <b>"+port+"</b> To("+boksbak+"): <b>"+boksName.get(boksbak)+"</b><br>");
								// Print aktive VLANs
								out("&nbsp;&nbsp;Active VLANs: <b>");
								Iterator vlanIter = activeVlanOnTrunk.iterator();
								int[] vlanA = new int[activeVlanOnTrunk.size()];
								int vlanAi=0;
								while (vlanIter.hasNext()) vlanA[vlanAi++] = Integer.parseInt((String)vlanIter.next());
								Arrays.sort(vlanA);
								boolean first=true;
								for (vlanAi=0; vlanAi < vlanA.length; vlanAi++) {
									if (!first) out(", "); else first=false;
									out(String.valueOf(vlanA[vlanAi]));
								}
								outl("</b><br>");
								//outl("&nbsp;&nbsp;The following VLANs are allowed on the trunk, but does not seem to be active:<br>");
								printMsg = true;
								out("&nbsp;&nbsp;Excessive VLANs: <b>"+range+"</b>");
							} else {
								out(", <b>"+range+"</b>");
							}
							markLast=false;
						}
						//startRange=i+1;
					}
				}
				if (printMsg) outl("<br><br>");
			}
		}

		outl("A total of <b>"+allowedcnt+"</b> / <b>"+totcnt+"</b> trunks have allowed VLANs that are not active.<br>");

		// Send event to eventengine
		Map varMap = new HashMap();
		varMap.put("command", "updateFromDB");
		EventQ.createAndPostEvent("getDeviceData", "eventEngine", 0, 0, 0, "notification", Event.STATE_NONE, 0, 0, varMap);

		outl("All done.<br>");

	}

	public Map updateVlanDb(List trunkVlan, Map vlanidVlan, Map allowedVlan, Map boksName, boolean deleteNoDirection) throws SQLException {
		HashMap swportvlan = new HashMap();
		HashMap swportvlanNontrunk = new HashMap();
		HashMap swportvlanDupe = new HashMap();
		String sql = "SELECT swportvlanid,interfaceid,vlanid,direction,trunk FROM swportvlan JOIN interface_swport USING (interfaceid)";
		ResultSet rs = Database.query(sql);
		HashSet reportMultipleVlan = new HashSet();
		while (rs.next()) {
			String swportid = rs.getString("interfaceid");
			String key = swportid+":"+rs.getString("vlanid");
			swportvlanDupe.put(key, rs.getString("direction") );
			swportvlan.put(key, rs.getString("swportvlanid") );

			if (!rs.getBoolean("trunk")) {
				if (swportvlanNontrunk.containsKey(swportid)) {
					if (!reportMultipleVlan.contains(swportid)) {
						outl("<font color=\"red\">ERROR!</font> Multiple vlans for non-trunk port, interfaceid: " + key + "<br>");
						reportMultipleVlan.add(swportid);
					}
					continue;
				}
				swportvlanNontrunk.put(swportid, rs.getString("swportvlanid") );
			}
		}

		outl("<br><b>Report:</b> (found "+trunkVlan.size()+" records)<br>");

		HashMap activeOnTrunk = new HashMap(); // This is used to verify swportallowedvlan against what is actually active

		int newcnt=0,updcnt=0,dupcnt=0,remcnt=0,renamecnt=0;
		for (int i=0; i < trunkVlan.size(); i++) {
			String[] s = (String[])trunkVlan.get(i);
			String swportid = s[0];
			String vlanid = s[1];
			String vlan = (String)vlanidVlan.get(vlanid);
			String direction = s[2];
			String key = swportid+":"+vlanid;

			if (swportvlanDupe.containsKey(key)) {
				// The element already exists in the database, so we do not insert it
				// Check if we should update
				String dbRetning = (String)swportvlanDupe.get(key);
				if (!dbRetning.equals(direction)) {
					// Update necessary
					String[] updateFields = {
						"direction", direction
					};
					String[] condFields = {
						"interfaceid", swportid,
						"vlanid", vlanid
					};
					Database.update("swportvlan", updateFields, condFields);
					outl("[UPD] interfaceid: " + swportid + " vlan: <b>"+ vlan +"</b> Direction: <b>" + direction + "</b> (old: "+dbRetning+")<br>");
					updcnt++;
				} else {
					dupcnt++;
				}
				// We are not to delete this record now
				swportvlan.remove(key);


			} else {
				// This could be a non-trunk port where we've rewritten/translated the VLAN value
				if (swportvlanNontrunk.containsKey(swportid)) {
					// Yep, let's just update
					updcnt++;
					outl("[UPD] interfaceid: " + swportid + " vlan: <b>"+ vlan +"</b> Direction: <b>" + direction + "</b> (renamed)<br>");

					String swportvlanid = (String)swportvlanNontrunk.get(swportid);
					String[] updateFields = {
						"vlanid", vlanid,
						"direction", direction
					};
					String[] condFields = {
						"swportvlanid",
						swportvlanid
					};
					Database.update("swportvlan", updateFields, condFields);

				} else {
					// swportvlan does not already contain this entry, so we must insert it. 
					newcnt++;
					swportvlanDupe.put(key, direction);
					outl("[NEW] interfaceid: " + swportid + " vlan: <b>"+ vlan +"</b> Retning: <b>" + direction + "</b><br>");

					// Insert into swportvlan
					String[] fields = {
						"interfaceid", swportid,
						"vlanid", vlanid,
						"direction", direction,
					};
					Database.insert("swportvlan", fields);
				}
			}

			// Then add to activeOnTrunk
			//HashMap swrecTrunk;
			HashSet activeVlanOnTrunk;
			if ( (activeVlanOnTrunk = (HashSet)activeOnTrunk.get(swportid)) == null) {
				activeVlanOnTrunk = new HashSet();
				activeOnTrunk.put(swportid, activeVlanOnTrunk);
			}
			if (vlan == null) {
				System.err.println("WARNING: vlan is null for vlanid: " + vlanid);
				vlan = "-1";
			}
			activeVlanOnTrunk.add(vlan);
		}

		// Now we can iterate swportvlan and delete those entries that no longer exist.
		Iterator iter = swportvlan.entrySet().iterator();
		while (iter.hasNext()) {
			remcnt++;
			Map.Entry me = (Map.Entry)iter.next();
			String key = (String)me.getKey();
			String swportvlanid = (String)me.getValue();
				
			StringTokenizer st = new StringTokenizer(key, ":");
			String swportid = st.nextToken();
			String vlanid = st.nextToken();
			String vlan = (String)vlanidVlan.get(vlanid);

			if (!deleteNoDirection) {
				String direction = (String) swportvlanDupe.get(key);
				if ("x".equals(direction) || "u".equals(direction)) continue;
			}
			
			outl("[REM] interfaceid: " + swportid + " vlan: <b>"+ vlan +"</b> ("+swportvlanid+")<br>");
			Database.update("DELETE FROM swportvlan WHERE swportvlanid = '"+swportvlanid+"'");
		}

		// Then we delete all vlans without either prefices or swports
		int delPrefix = Database.update("DELETE FROM prefix WHERE prefixid NOT IN (SELECT prefixid FROM gwportprefix) AND vlanid NOT IN (SELECT vlanid FROM vlan JOIN swportvlan USING(vlanid) UNION SELECT vlanid FROM vlan WHERE nettype='scope')");
		int delVlan = Database.update("DELETE FROM vlan WHERE vlanid NOT IN (SELECT vlanid FROM prefix UNION SELECT vlanid FROM swportvlan UNION SELECT vlanid FROM vlan WHERE nettype='scope')");
		outl("New count: <b>"+newcnt+"</b>, Update count: <b>"+updcnt+"</b> Dup count: <b>"+dupcnt+"</b>, Rem count: <b>"+remcnt+"</b> delPrefix: <b>"+delPrefix+"</b>, delVlan: <b>"+delVlan+"</b>, Rename vlan count: <b>"+renamecnt+"</b><br>");

		return activeOnTrunk;
	}

	private boolean vlanTraverseLink(int vlan,
																	 int vlanid,
																	 String fromid,
																	 String boksid,
																	 boolean cameFromTrunk,
																	 boolean setDirection,
																	 HashMap nontrunkVlan,
																	 HashMap allowedVlan,
																	 HashMap activeVlan,
																	 HashMap swportidMap,
																	 HashSet spanTreeBlocked,
																	 List trunkVlan,
																	 Map dataStructs,
																	 List foundGwports,
																	 Set visitedNodeSet,
																	 int level,
																	 boolean DEBUG_OUT,
																	 HashSet boksGwSet,
																	 Map swportGwVlanMap,
																	 HashMap boksName)
	{
		if (level > 60) {
			outl("<font color=\"red\">ERROR! Level is way too big...</font>");
			return false;
		}
		String pad = "";
		for (int i=0; i<level; i++) pad+="        ";

		if (DEBUG_OUT) outl(pad+"><font color=\"green\">[ENTER]</font> Now at node("+boksid+"): <b>" + boksName.get(boksid) + "</b>, came from("+fromid+"): " + boksName.get(fromid) + ", vlan: " + vlan + " cameFromTrunk: <b>"+cameFromTrunk+"</b> level: <b>" + level + "</b>");

		// Check for loops, we only need to traverse the same unit once
		if (visitedNodeSet.contains(boksid)) {
			if (DEBUG_OUT) outl(pad+"><font color=\"red\">[RETURN]</font> NOTICE: Found loop, from("+fromid+"): " + boksName.get(fromid) + ", boksid("+boksid+"): " + boksName.get(boksid) + ", vlan: " + vlan + ", level: " + level + "");
			return false;
		}
		visitedNodeSet.add(boksid);

		// Now we now this VLAN is active on this box, the first thing we do is to traverse each 
		// non-trunk port and mark the direction of the link.
		boolean isActiveVlan = false;
		if (nontrunkVlan.containsKey(boksid+":"+vlan)) {
			String key = boksid+":"+vlan;
			HashMap nontrunkMap = (HashMap)nontrunkVlan.get(key);
			
			Iterator iter = nontrunkMap.values().iterator();
			while (iter.hasNext()) {
				HashMap hm = (HashMap)iter.next();
				String toid = (String)hm.get("to_netboxid");
				String swportid = (String)hm.get("interfaceid");
				String swportidBack = null;
				
				// We're not going to follow the link back anyway
				if (toid.equals(fromid)) continue;
				
				if (boksGwSet.contains(toid)) {
					// Link to GW, we will not traverse, check if this VLAN is active on this swport
					if (swportGwVlanMap.containsKey(swportid+":"+vlan)) {
						// OK, the link now becomes 'o' (opp = up)
						String[] rVlan = {
							swportid,
							String.valueOf(vlanid),
							(setDirection)?"o":"u"
						};
						if (DEBUG_OUT) outl(pad+"--><b>[NON-TRUNK-GW]</b> Running on non-trunk, vlan: <b>" + vlan + "</b>, boksid("+boksid+"): <b>" + boksName.get(boksid) + "</b>, to("+toid+"): <b>" + boksName.get(toid) + "</b> level: <b>" + level + "</b> (<b>"+rVlan[0]+"</b>)");
						trunkVlan.add(rVlan);
						isActiveVlan = true;
						foundGwports.add(swportGwVlanMap.get(swportid+":"+vlan));
					}
					continue;
				}

				// Before we traverse the link down, we check which VLAN is on
				// the port on the other end.  If the VLAN on the other end is
				// not identical to the one we are traversing, this VLAN value
				// must be rewritten to the VLAN we are traversing at the
				// moment.  This goes for all ports we find below this level.
				String vlanBack = null;
				Map nbvlanMap = (Map)dataStructs.get("nbvlanMap"); // Maps id:toid -> vlan

				if (swportidMap.containsKey(swportid)) {
					// Get the swport record and extract the to_swportid field from it
					Map mySwrec = (Map)swportidMap.get(swportid);
					swportidBack = (String)mySwrec.get("to_interfaceid");
					Map swrecBack = (Map)swportidMap.get(swportidBack);
					if (swrecBack != null) {
						vlanBack = (String)swrecBack.get("vlan");
					}
				}

				if (vlanBack == null) {
					// Just use ids
					vlanBack = (String)nbvlanMap.get(toid+":"+boksid);
				}

				// It could be that the other end has a different VLAN on the port that leads back to this unit; then we will rewrite the VLAN value.
				// But only if we come from above, traversing downwards, i.e. if setDirection is true.
				if (setDirection && vlan != 1 && nontrunkVlan.containsKey(toid+":"+vlanBack)) {
					HashMap nontrunkMapBack = (HashMap)nontrunkVlan.get(toid+":"+vlanBack);
					String idBack = (nontrunkMapBack != null && nontrunkMapBack.containsKey(swportid)) ? swportid : boksid;
					if (nontrunkMapBack != null && nontrunkMapBack.containsKey(idBack)) {
						// We've found link back on VLAN (1 or vlanBack), then we just switch it
						nontrunkVlan.remove(toid+":"+vlanBack);
						nontrunkVlan.put(toid+":"+vlan, nontrunkMapBack);

						// Also switch it in activeVlan
						Map map = (Map)activeVlan.get(toid);
						if (map != null && map.containsKey(new Integer(vlanBack))) {
							Collection c;
							if ((c = (Collection)map.get(new Integer(vlan))) == null) map.put(new Integer(vlan), c = new HashSet());
							c.addAll((Collection)map.remove(new Integer(vlanBack)));
						}

						if (DEBUG_OUT) outl(pad+"--><b>[REPLACE]</b> Replaced vlan: <b>1</b> with vlan: <b>" + vlan + "</b>, for boks("+toid+"): <b>" + boksName.get(toid) + "</b> level: <b>" + level + "</b>");
					}
				}

				// Now we can at least add that the direction is down here.
				String[] rVlan = {
					swportid,
					String.valueOf(vlanid),
					(setDirection)?"n":"u" // n = ned = down
				};
				trunkVlan.add(rVlan);
				isActiveVlan = true;

				if (DEBUG_OUT) outl(pad+"--><b>[NON-TRUNK]</b> Running on non-trunk, vlan: <b>" + vlan + "</b>, boksid("+boksid+"): <b>" + boksName.get(boksid) + "</b>, to("+toid+"): <b>" + boksName.get(toid) + "</b> level: <b>" + level + "</b> (<b>"+rVlan[0]+"</b>)");

				// Then we traverse the link, the return value is of no importance here
				vlanTraverseLink(vlan, vlanid, boksid, toid, false, setDirection, nontrunkVlan, allowedVlan, activeVlan, swportidMap, spanTreeBlocked, trunkVlan, dataStructs, foundGwports, visitedNodeSet, level+1, DEBUG_OUT, boksGwSet, swportGwVlanMap, boksName);

				// Then check if we can find the link back, and if so it is marked with direction 'o' (up)
				if (swportidBack == null) {
					String keyBack = toid+":"+vlan;
					HashMap nontrunkMapBack = (HashMap)nontrunkVlan.get(keyBack);
					if (nontrunkMapBack == null) {
						// The box we are looking at has no non-trunk links, therefore we can move on
						if (DEBUG_OUT) outl(pad+"---->ERROR! No non-trunk links found for vlan: " + vlan + ", toid("+toid+"): " + boksName.get(toid) + ", level: " + level + "");
						continue;
					}
					
					HashMap hmBack = (HashMap)nontrunkMapBack.get(boksid);
					if (hmBack == null) {
						// The link back is missing
						if (DEBUG_OUT) outl(pad+"---->ERROR! Link back not found for vlan: " + vlan + ", toid("+toid+"): " + boksName.get(toid) + ", level: " + level + "");
						continue;
					}
					
					swportidBack = (String)hmBack.get("interfaceid");
				}
				
				// Now we can mark the VLAN as active also on the link back
				String[] rVlanBack = {
					swportidBack,
					String.valueOf(vlanid),
					(setDirection)?"o":"u"
				};
				trunkVlan.add(rVlanBack);
				if (DEBUG_OUT) outl(pad+"--><b>[NON-TRUNK]</b> Link back running on non-trunk OK (<b>"+rVlanBack[0]+"</b>)");
			}
		}

		// Check if the VLAN is active on any non-trunk ports; we must add them
		// without to_netboxid
		{
			Map map = (Map)activeVlan.get(boksid);
			if (map != null && map.containsKey(new Integer(vlan)) ) {
				isActiveVlan = true;
				// Create trunkVlan records for all ports
				for (Iterator it = ((Collection)map.get(new Integer(vlan))).iterator(); it.hasNext();) {
					String swportid = (String)it.next();
					String[] rVlan = {
						swportid,
						String.valueOf(vlanid),
						(setDirection)?"n":"u"
					};
					trunkVlan.add(rVlan);
				}
			}
		}

		// Check if there are any trunks on this unit that allow this VLAN
		HashMap boksAllowedMap = (HashMap)allowedVlan.get(boksid);
		if (boksAllowedMap == null) {
			if (cameFromTrunk) {
				if (fromid == null) {
					// This is the first unit, then this can actually happen
					if (DEBUG_OUT) outl(pad+">ERROR! AllowedVlan not found for vlan: " + vlan + ", boksid("+boksid+"): " + boksName.get(boksid) + ", level: " + level + "");
				} else {
					if (DEBUG_OUT) outl(pad+"><font color=\"red\">ERROR! Should not happen, AllowedVlan not found for vlan: " + vlan + ", boksid("+boksid+"): " + boksName.get(boksid) + ", level: " + level + "</font>");
				}
			}
			if (DEBUG_OUT) outl(pad+"><font color=\"red\">[RETURN]</font> from node("+boksid+"): " + boksName.get(boksid) + ", isActiveVlan: <b>" + isActiveVlan+"</b>, no trunks to traverse.");
			// Return true if there are non-trunks on this box
			// This should only matter if there is a non-trunk link up to the GW
			return isActiveVlan;
		}
		boolean isActiveVlanTrunk = false;
		Iterator iter = boksAllowedMap.values().iterator();
		while (iter.hasNext()) {
			HashMap hm = (HashMap)iter.next();
			String hexstr = (String)hm.get("hexstring");
			String toid = (String)hm.get("to_netboxid");
			String swportid = (String)hm.get("interfaceid");
			String swportidBack;

			// We're not following the link back anyway
			if (toid.equals(fromid)) continue;

			if (boksGwSet.contains(toid)) {
				if (swportGwVlanMap.containsKey(swportid+":"+vlan)) {
					if (!isAllowedVlan(hexstr, vlan)) {
						if (DEBUG_OUT) outl(pad+"--><font color=\"red\">ERROR, running on trunk to GW, but isAllowedVlan is false, vlan: <b>" + vlan + "</b>, boksid("+boksid+"): <b>" + boksName.get(boksid) + "</b>, to("+toid+"): <b>" + boksName.get(toid) + "</b> level: <b>" + level + "</b> (<b>"+swportid+"</b>)");
						continue;
					}

					// This is a link to a GW, it then becomes direction 'o' (up), and we don't traverse
					String[] tvlan = {
						swportid,
						String.valueOf(vlanid),
						"o"
					};

					if (DEBUG_OUT) outl(pad+"--><b>[TRUNK-GW]</b> Running on trunk, vlan: <b>" + vlan + "</b>, boksid("+boksid+"): <b>" + boksName.get(boksid) + "</b>, to("+toid+"): <b>" + boksName.get(toid) + "</b> level: <b>" + level + "</b> (<b>"+tvlan[0]+"</b>)");
					trunkVlan.add(tvlan);
					isActiveVlanTrunk = true;
					foundGwports.add(swportGwVlanMap.get(swportid+":"+vlan));
				}
				continue;
			}

			// Now we need the record for the link back
			{
				HashMap boksAllowedMapBack = (HashMap)allowedVlan.get(toid);
				if (boksAllowedMapBack == null) {
					if (DEBUG_OUT) outl(pad+">ERROR! AllowedVlan not found for vlan: " + vlan + ", toid("+toid+"): " + boksName.get(toid) + ", level: " + level + "");
					continue;
				}
				HashMap hmBack = (HashMap)boksAllowedMapBack.get(boksid);
				if (hmBack == null) {
					// Linken tilbake mangler
					if (DEBUG_OUT) outl(pad+"---->ERROR! Link back not found for vlan: " + vlan + ", toid("+toid+"): " + boksName.get(toid) + ", level: " + level + "");
					continue;
				}
				swportidBack = (String)hmBack.get("interfaceid");

				String hexstrBack = (String)hmBack.get("hexstring");
				if (hexstrBack == null) {
					// The link back is missing
					if (DEBUG_OUT) outl(pad+"---->ERROR! hexstring back not found for vlan: " + vlan + ", toid("+toid+"): " + boksName.get(toid) + ", level: " + level + "");
					continue;
				}
				if (hexstr == null) {
					// The link back is missing
					if (DEBUG_OUT) outl(pad+"---->ERROR! hexstring not found for vlan: " + vlan + ", toid("+toid+"): " + boksName.get(toid) + ", level: " + level + "");
					continue;
				}

				// If one of the link partners do not allow this VLAN, we don't follow this link
				if (!isAllowedVlan(hexstr, vlan) || !isAllowedVlan(hexstrBack, vlan)) {
					if (DEBUG_OUT) outl(pad+"----><b>NOT</b> allowed to("+toid+"): " + boksName.get(toid) + "");
					continue;
				}
			}

			if (DEBUG_OUT) outl(pad+"----><b>Allowed</b> to("+toid+"): " + boksName.get(toid) + ", visiting...");

			// Check whether the link has been blocked by spanning tree
			if (spanTreeBlocked.contains(swportid+":"+vlan) || spanTreeBlocked.contains(swportidBack+":"+vlan)) {
				// Yep, add the VLAN with blocking in both ends
				String[] tvlan = {
					swportid,
					String.valueOf(vlanid),
					"b"
				};
				String[] tvlanBack = {
					swportidBack,
					String.valueOf(vlanid),
					"b"
				};
				trunkVlan.add(tvlan);
				trunkVlan.add(tvlanBack);
				isActiveVlanTrunk = true;
				if (DEBUG_OUT) outl(pad+"------><font color=\"purple\">Link blocked by spanning tree, boksid("+boksid+"): <b>"+boksName.get(boksid)+"</b> toid:("+toid+"): <b>"+ boksName.get(toid) + "</b>, vlan: <b>" + vlan + "</b>, level: <b>" + level + "</b></font>");
				continue;
			}


			//if (DEBUG_OUT) outl(pad+"---->Visiting("+toid+"): " + boksName.get(toid) + "");

			// Used to avoid dupes
			//visitNode.add(boksid);

			if (vlanTraverseLink(vlan, vlanid, boksid, toid, true, setDirection, nontrunkVlan, allowedVlan, activeVlan, swportidMap, spanTreeBlocked, trunkVlan, dataStructs, foundGwports, visitedNodeSet, level+1, DEBUG_OUT, boksGwSet, swportGwVlanMap, boksName)) {
				// We now know that the VLAN runs on this trunk
				String[] tvlan = {
					swportid,
					String.valueOf(vlanid),
					(setDirection)?"n":"u"
				};
				String[] tvlanBack = {
					swportidBack,
					String.valueOf(vlanid),
					(setDirection)?"o":"u"
				};
				trunkVlan.add(tvlan);
				trunkVlan.add(tvlanBack);
				isActiveVlanTrunk = true;
				if (DEBUG_OUT) outl(pad+"---->Returned active on trunk, vlan: <b>" + vlan + "</b>, boksid("+boksid+"): <b>" + boksName.get(boksid) + "</b>, to("+toid+"): <b>" + boksName.get(toid) + "</b> level: <b>" + level + "</b> (<b>"+tvlan[0]+" '"+tvlan[2]+"' / "+tvlanBack[0]+" '"+tvlanBack[2]+"'</b>)");
			} else {
				if (DEBUG_OUT) outl(pad+"---->Returned NOT active on trunk, vlan: <b>" + vlan + "</b>, boksid("+boksid+"): <b>" + boksName.get(boksid) + "</b>, to("+toid+"): <b>" + boksName.get(toid) + "</b> level: <b>" + level + "</b>");
			}
			//visitNode.remove(boksid);


		}


		// We will return if the VLAN is active on this box
		// First we check if the VLAN is active on any of the trunks
		if (isActiveVlanTrunk) {
			if (DEBUG_OUT) outl(pad+"><font color=\"red\">[RETURN]</font> from node("+boksid+"): " + boksName.get(boksid) + ", <b>ActiveVlan on trunk</b>");
			return true;
		}

		// No, then we check whether it is active on any non-trunks
		if (isActiveVlan) {
			if (DEBUG_OUT) outl(pad+"><font color=\"red\">[RETURN]</font> from node("+boksid+"): " + boksName.get(boksid) + ", <b>ActiveVlan on NON-trunk</b>");
			return true;
		}

		if (DEBUG_OUT) outl(pad+"><font color=\"red\">[RETURN]</font> from node("+boksid+"): " + boksName.get(boksid) + ", <b>Not active</b>");
		return false;
	}

	private static boolean isAllowedVlan(String hexstr, int vlan)
	{
		hexstr = hexstr.replaceAll(":", "");
		// This code used to say:
		//   if (hexstr.length() == 256 || hexstr.length() == 254) {
		// I don't know why the hell 254 was considered a magic value here, as none of the other redundant pieces of NAV code seem to think so.
		if (hexstr.length() >= 256) {
			return isAllowedVlanFwd(hexstr, vlan);
		}
		return isAllowedVlanRev(hexstr, vlan);
	}

	private static boolean isAllowedVlanFwd(String hexstr, int vlan)
	{
		if (vlan < 0 || vlan > 4095) return false;
		int index = vlan / 4;
		if (index >= hexstr.length()) return false;

		int allowed = Integer.parseInt(String.valueOf(hexstr.charAt(index)), 16);
		return ((allowed & (1<<3-(vlan%4))) != 0);
	}

	private static boolean isAllowedVlanRev(String hexstr, int vlan)
	{
		if (vlan < 0 || vlan > 1023) return false;
		int index = hexstr.length() - (vlan / 4 + 1);
		if (index < 0) return false;

		int allowed = Integer.parseInt(String.valueOf(hexstr.charAt(index)), 16);
		return ((allowed & (1<<(vlan%4))) != 0);
	}



	private void outl(String s)
	{
		System.out.println(s);
	}
	private void out(String s)
	{
		System.out.print(s);
	}

	private void err(String s) { System.err.print(s); }
	private void errl(String s) { System.err.println(s); }
}
