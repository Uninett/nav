/*
 * HandlerVlanPlot.java
 *
 */

import no.ntnu.nav.Database.*;

import java.io.*;
import java.util.*;
import java.sql.*;

//import javax.servlet.*;
//import javax.servlet.http.*;

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

	public String begin() throws PError
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

			// identify sub-levels
			/*
			if (s[1].equals("updateMac"))
			{
				updateMac();
			} else
			if (s[1].equals("updatePortBak"))
			{
				updatePortBak();
			} else
			if (s[1].equals("updateStatic"))
			{
				updateStatic();
			} else
			if (s[1].equals("listSwport"))
			{
				listSwport();
			} else
			if (s[1].equals("checkError"))
			{
				checkError();
			} else
			if (s[1].equals("searchSwport"))
			{
				searchSwport();
			} else
			if (s[1].equals("findMissingLinks"))
			{
				findMissingLinks();
			} else
			if (s[1].equals("updateCommunity"))
			{
				updateCommunity();
			} else

			// handle functions on this level
			// (session)
			if (s[1].equals("antUserTreff"))
			{
				antUserTreff();
			} else
			{
			*/
				/*
				 * Kall opp metode med riktig navn
				 *
				 *
				 */
			try {
				//Object o=new Object();
				//java.lang.reflect.Method hashcode=o.getClass().getDeclaredMethod("hashCode" ,new Class[0]);
				java.lang.reflect.Method metode = this.getClass().getDeclaredMethod(s[1], new Class[0]);
				//Integer hc=(Integer)hashcode.invoke(o,new Object[0]);
				//System.out.println(hc);
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

/*
	private void presTemp()
	{
		if (s.length >= 3)
		{
			// identify sub-levels


			// handle functions on this level
			if (s[2].equals("list"))
			{
				list();
			}




		}
	}
*/


	/************************************************************
	* Level 1 functions											*
	* user.*													*
	************************************************************/

	private void ifRapporter()
	{
		String user = com.getUser().getLogin();
		if (user == null || !user.equals("kristian")) {
			if (s.length >= 3) com.outl("-->");
			else com.outl("<!--");
		}
	}

	private void fixPrefiks() throws SQLException
	{
		com.outl("Fixing prefiks...<br>");
		ResultSet rs = Database.query("SELECT prefiksid,nettadr FROM prefiks");
		HashMap prefiks = new HashMap();
		while (rs.next()) prefiks.put(rs.getString("nettadr"), rs.getString("prefiksid"));

		rs = Database.query("SELECT boksid,ip,prefiksid FROM boks ORDER BY boksid");

		String[] masker = {
			"255.255.255.255","255.255.255.254","255.255.255.252","255.255.255.248","255.255.255.240","255.255.255.224",
			"255.255.255.192","255.255.255.128","255.255.255.0","255.255.254.0","255.255.252.0"
		};

		while (rs.next()) {
			String prefiksid = rs.getString("prefiksid");
			//com.outl("Checking: " + prefiksid);
			if (prefiksid != null && prefiksid.length()>0) continue;

			//com.outl("-->Needs fixing<br>");

			String boksid = rs.getString("boksid");
			String ip = rs.getString("ip");

			for (int i=0;i<masker.length;i++) {
				String netadr = and_ip(ip, masker[i]);

				if (prefiks.containsKey(netadr)) {
					prefiksid = (String)prefiks.get(netadr);
					String sql = "UPDATE boks SET prefiksid = '"+prefiksid+"' WHERE boksid = '"+boksid+"'";

					String[] feltVerdi = {
						"prefiksid", prefiksid
					};
					String[] feltNavnVerdi = {
						"boksid", boksid
					};
					Database.update("boks", feltVerdi, feltNavnVerdi);
					Database.commit();
					com.outl("SQL: " + sql + "<br>");
					break;
				}
			}

		}
	}

	private String and_ip(String ip, String maske)
	{
		StringTokenizer a = new StringTokenizer(ip, ".");
		StringTokenizer b = new StringTokenizer(maske, ".");
		String and_ip = "";

		while (a.hasMoreTokens()) {
			and_ip += "."+(Integer.parseInt(a.nextToken())&Integer.parseInt(b.nextToken()));
		}
		return and_ip.substring(1, and_ip.length());
	}


	/* [/ni.avledTopologi]
	 *
	 */
	private void avledTopologi() throws SQLException
	{
		NavUtils nu = new NavUtils(com);
		nu.avledTopologi();
	}

	/*
	private HashMap getHashFromResultSet(ResultSet rs, ResultSetMetaData md) throws SQLException
	{
		HashMap hm = new HashMap();
		for (int i=md.getColumnCount(); i > 0; i--) {
			hm.put(md.getColumnName(i), rs.getString(i));
		}
		return hm;
	}
	*/

	/* [/ni.avledVlan]
	 *
	 */
	private void avledVlan() throws SQLException
	{
		NavUtils nu = new NavUtils(com);
		nu.avledVlan();
	}

	private synchronized HashMap[] getPortMap() throws SQLException {
		HashMap portMap = null;
		HashMap rootMap = null;
		HashMap sysnameMap = null;
		HashMap katMap = null;

		//portMap = (HashMap)com.getUser().getData("portMap");
		//rootMap = (HashMap)com.getUser().getData("rootMap");
		if (portMap == null || rootMap == null) {
			portMap = new HashMap();
			rootMap = new HashMap();
			sysnameMap = new HashMap();
			katMap = new HashMap();

			// Hent gw'ene som danner røttene i treet
			ResultSet rs = Database.query("SELECT boksid,sysname,interf,vlan,boksbak,swportbak FROM boks JOIN gwport USING (boksid) JOIN prefiks ON (gwport.prefiksid=prefiks.prefiksid) WHERE boksbak IS NOT NULL ORDER BY sysname,vlan,interf");
			ResultSetMetaData rsmd = rs.getMetaData();
			while (rs.next()) {
				//HashMap hm = getHashFromResultSet(rs, rsmd, false);
				String boksid = rs.getString("boksid");
				String key = boksid+":0";
				List l;
				if ( (l=(List)portMap.get(key)) == null) portMap.put(key, l=new ArrayList());

				HashMap hm = new HashMap();
				hm.put("boksid", rs.getString("boksbak"));
				//hm.put("boksid", "gw"+rs.getString("gwportid"));
				hm.put("vlan", rs.getString("vlan"));
				hm.put("port", rs.getString("interf"));
				//hm.put("boksbak", rs.getString("boksbak"));
				l.add(hm);

				if (!rootMap.containsKey(boksid)) {
					hm = new HashMap();
					hm.put("vlan", "0");
					hm.put("boksid", boksid);
					rootMap.put(boksid, hm);
				}
			}

			// Hent hele swport
			rs = Database.query("SELECT swportid,boksid,modul,port,vlan,status,speed,duplex,media,trunk,portnavn,boksbak FROM swport JOIN swportvlan USING (swportid) ORDER BY boksid,modul,port");
			rsmd = rs.getMetaData();
			while (rs.next()) {
				String key = rs.getString("boksid")+":"+rs.getString("vlan");
				List l;
				if ( (l=(List)portMap.get(key)) == null) portMap.put(key, l=new ArrayList());

				HashMap hm = getHashFromResultSet(rs, rsmd, false);
				l.add(hm);
			}

			// Hent sysname,kat
			rs = Database.query("SELECT boksid,sysname,kat FROM boks");
			while (rs.next()) {
				String boksid = rs.getString("boksid");
				sysnameMap.put(boksid, rs.getString("sysname"));
				katMap.put(boksid, rs.getString("kat"));
			}

			//com.getUser().setData("portMap", portMap);
			//com.getUser().setData("rootMap", rootMap);
		}

		return new HashMap[] { portMap, rootMap, sysnameMap, katMap };
	}


	/* [/ni.visTopologi]
	 *
	 */
	private void visTopologi() throws SQLException
	{
		String name = "<b>NTNU network</b>";
		String imgRoot = "<img border=0 src=\"" + gfxRoot + "/";
		String ntnuImg = imgRoot + "ntnunet.gif" + "\">";
		String expandIcon = imgRoot + "expand.gif" + "\" alt=\"Expand entire branch\">";
		String label = "<a name=\"0\"></a>";

		com.out("<table border=0 cellspacing=0 cellpadding=0>\n");
		com.outl("  <tr>");
		com.outl("    <td>");
		com.outl("      " + label + ntnuImg);
		com.outl("    </td>");
		com.outl("    <td colspan=50>");

		com.out(      "<a href=\"");
		link("link.ni.listSwport.expand." + "0");
		com.out("#" + "0");
		com.outl("\">" + expandIcon + "</a>");

		com.outl("      <font color=black>" + name + "</font>");
		com.outl("    </td>");
		com.outl("  </tr>");

		//com.outl("Fetching rootMap...<br>");

		HashMap portMap;
		Map rootMap;
		HashMap sysnameMap;
		HashMap katMap;
		{
			HashMap[] hmA = getPortMap();
			portMap = hmA[0];
			rootMap = hmA[1];
			sysnameMap = hmA[2];
			katMap = hmA[3];
		}

		//com.outl("rootMap.size: " + rootMap.size() + "<br>");

		HashMap travMap = (HashMap)com.getUser().getData("traverseList");
		if (travMap == null) {
			travMap = new HashMap();
		}
		travMap.put("589:0", new Boolean(true) );
		travMap.put("589:128", new Boolean(true) );
		travMap.put("271:128", new Boolean(true) );

		// sjekk om vi skal traverese hele ntnunet
		Boolean b = (Boolean)travMap.get("0");
		if (b == null)
		{
			b = new Boolean(false);
		}



		com.out("<table border=0 cellspacing=0 cellpadding=0>\n");
		for (Iterator iter=rootMap.values().iterator(); iter.hasNext();) {
			HashMap swrec = (HashMap)iter.next();
			swportExpand(swrec, 0, !iter.hasNext(), portMap, travMap, sysnameMap, katMap);
		}
		/*
		for (int i = 0; i < swId.length; i++)
		{
			swportExpand(swId[i], swName[i], null, "0", null, null, 0, trav, b.booleanValue() );
		}
		*/

		com.out("</table>\n");

	}

	private void swportExpand(HashMap swrec, int depth, boolean lastPort, HashMap portMap, HashMap travMap, HashMap sysnameMap, HashMap katMap)
	{
		int strekType = (lastPort ? BOXOPEN_BOTTOM : BOXOPEN_BOTH);

		if (depth > 5) {
			com.outl("<tr><td colspan=50>ERROR, depth too large, return.</td></tr>");
			return;
		}

		String boksid = (String)swrec.get("boksid");
		String vlan = (String)swrec.get("vlan");
		String key = boksid+":"+vlan;


		// sjekk om vi skal traverse videre
		boolean traverse = false;
		{
			Boolean b = (Boolean)travMap.get(key);
			if (b != null) traverse = b.booleanValue();
		}

		// Skriv ut denne noden
		if (!traverse) strekType = (lastPort ? BOXCLOSED_BOTTOM : BOXCLOSED_BOTH);
		printNode(swrec, swrec, depth, strekType, sysnameMap, katMap);
		if (!traverse) return;

		//com.outl("swportExpand called, boksid: " + boksid + " vlan: "+ vlan + " depth: " + depth + "<br>");

		// Hent ut listen over porter tilhørende denne enheten
		List portList = (List)portMap.get(key);
		if (portList == null)
		{
			//printNode(id, swName, port, findPortBak(swName, null, parentName, false), parentId, parentName, depth, "n", "sw", REDCROSS, true);
			//printNode(id, parentName, swName, port, parentPort, depth, "sw", false, true);
			com.outl("  ERROR! portList not found! return<br>");
			return;
		}

		// hent ut navn fra portname
		/*
		String[] typeBak = new String[portname.length];
		String[] nameBak = new String[portname.length];
		for (int i = 0; i < portname.length; i++)
		{
			String[] pn = misc.tokenizel(portname[i], ":");
			typeBak[i] = pn[0];
			nameBak[i] = pn[1];
		}
		*/

		//printNode(id, swName, port, findPortBak(swName, null, parentName, false), parentId, parentName, depth, "n", "sw", strekType, false);
		//printNode(id, parentName, swName, port, parentPort, depth, "sw", strekType, false);

		//if (portList.size()>1) com.outl("portList.size(): " + portList.size());

		for (int i = 0; i < portList.size(); i++) {
			HashMap port = (HashMap)portList.get(i);

			//if (i == portList.size()-1) strekType = STREK_BOTTOM;
			swportExpand(port, depth+1, (i == portList.size()-1), portMap, travMap, sysnameMap, katMap);


			//printNode(port, swrec, depth+1, strekType, sysnameMap, katMap);



			/*
			// default
			strekType = STREK_BOTH;
			if (j == portname.length-1) strekType = STREK_BOTTOM;

			String[] type = misc.tokenize(nameBak[j], ",");
			if (type.length > 1)
			{
				// portnavn etter konvensjon for ikke-snmp hub
				printNode(idbak[j], nameBak[j], mp[j], portBak[j], parentId, swName, depth+1, "n", "dumhub", strekType, false);
			} else
			{
				type = misc.tokenizel(portname[j], "-");
				if (type.length == 1)
				{
					// annen type uten konvensjon
					printNode(idbak[j], nameBak[j], mp[j], portBak[j], parentId, swName, depth+1, "n", typeBak[j], strekType, false);

				} else
				if (type[1].charAt(0) == 's' && type[0].charAt(0) == 'n')
				{
					// downlink til switch, sjekk om vi skal traverse
					if (trav.get(id) != null || traverse)
					{
						swportExpand(idbak[j], nameBak[j], mp[j], id, swName, portBak[j], depth+1, trav, traverse);
					} else
					{
						strekType = BOXCLOSED_BOTH;
						if (j == portname.length-1) strekType = BOXCLOSED_BOTTOM;

						//printNode(idbak[j], nameBak[j], mp[j], findPortBak(nameBak[j], null, swName, false), parentId, swName, depth+1, "n", "sw", strekType, false);
						printNode(idbak[j], nameBak[j], mp[j], portBak[j], parentId, swName, depth+1, "n", "sw", strekType, false);
					}
				} else
				if (type[1].charAt(0) == 's')
				{
					// up/hz link til sw, bare print ut
					//printNode(idbak[j], nameBak[j], mp[j], findPortBak(nameBak[j], null, swName, false), parentId, swName, depth+1, typeBak[j], "sw", strekType, false);
					printNode(idbak[j], nameBak[j], mp[j], portBak[j], parentId, swName, depth+1, typeBak[j], "sw", strekType, false);

				} else
				if (type[1].charAt(0) == 'g')
				{
					// up/hz/dn link til gw, bare print ut
					//printNode(idbak[j], nameBak[j], mp[j], findPortBak(nameBak[j], null, swName, false), parentId, swName, depth+1, typeBak[j], "gw", strekType, false);
					printNode(idbak[j], nameBak[j], mp[j], portBak[j], parentId, swName, depth+1, typeBak[j], "gw", strekType, false);

				} else
				if (type[1].charAt(0) == 'h')
				{
					// dn link til hub, bare print ut
					//printNode(idbak[j], nameBak[j], mp[j], findPortBak(nameBak[j], null, swName, false), parentId, swName, depth+1, typeBak[j], "hub", strekType, false);
					printNode(idbak[j], nameBak[j], mp[j], portBak[j], parentId, swName, depth+1, typeBak[j], "hub", strekType, false);

				} else
				{
					// dn link til annen type, bare print ut
					printNode(idbak[j], nameBak[j], mp[j], portBak[j], parentId, swName, depth+1, "n", typeBak[j], strekType, false);

				}

			}
			*/
		}
	}

	//private void printNode(String id, String name, String port, String portBak, String parentId, String parentName, int depth, String direct, String type, int strekType, boolean missing)
	private void printNode(HashMap swrec, HashMap parentrec, int depth, int strekType, HashMap sysnameMap, HashMap katMap)
	{
		String imgRoot = "<img border=0 src=\"" + gfxRoot + "/";
		String expandIcon = imgRoot + "expand.gif" + "\" alt=\"Expand entire branch\">";
		String portIcon = imgRoot + "porticon.gif" + "\">";
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


		String label = "";
		String linkLabel = "";
		String strekIcon = "";
		String typeIcon = "";

		String fontBegin = "";
		String fontEnd = "";

		boolean box = false; boolean boxOpen = false;

		String boksid = (String)swrec.get("boksid");
		String sysname = (String)sysnameMap.get(boksid);
		String kat = ((String)katMap.get(boksid)).toLowerCase();
		String parentBoksid = (String)parentrec.get("boksid");

		String modul = (String)swrec.get("modul");
		String port = (String)swrec.get("port");
		String mp = (modul!=null?modul+".":"")+port;
		String vlan = (String)swrec.get("vlan");
		//typeIcon = undefImg;
		typeIcon = imgRoot + kat + ".gif" + "\">";

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
				linkLabel = parentBoksid;
				box = true;
				boxOpen = true;
			break;

			case BOXOPEN_BOTTOM:
				strekIcon = boxOpenBottom;
				linkLabel = parentBoksid;
				box = true;
				boxOpen = true;
			break;

			case BOXCLOSED_BOTH:
				strekIcon = boxClosedBoth;
				linkLabel = boksid;
				box = true;
			break;

			case BOXCLOSED_BOTTOM:
				strekIcon = boxClosedBottom;
				linkLabel = boksid;
				box = true;
			break;

			default:
				strekIcon = strekBoth;
			break;
		}


		//com.outl("Got: " + swrec.get("boksid"));

		//if (portBak.equals("Not found")) portBak = "NA";

		String katItalic = "<i>" + kat + ": </i>";

		com.out("  <tr>\n");

		printDepth(depth, strekVertical);

		// print table
		com.out("    <td>");

		if (box)
		{
			com.out(      "<a href=\"");
			if (boxOpen)
			{
				link("link.ni.visTopologi.close." + boksid);
			} else
			{
				link("link.ni.visTopologi.open." + boksid);
			}
			com.out("&vlan="+vlan);
			com.out("#" + linkLabel);
			com.out("\">" + strekIcon + "</a>");

		} else
		{
			com.out("      " + strekIcon);
		}

		com.outl("</td>");
		com.out("    <td>");
		//com.outl("      " + typeIcon + label);
		com.out(label + typeIcon);
		com.outl("</td>");
		if (!kat.equals("gw")) {
			com.outl("    <td align=\"right\">");
			com.outl("      " + mp);
			com.outl("    </td>");
			com.outl("    <td align=\"center\">");
			com.outl("      " + portIcon);
			com.outl("    </td>");
			com.outl("    <td align=\"left\">");
			com.outl("      " + "1.1");
			com.outl("    </td>");
		}

		com.outl("    <td colspan=50>");

		if (box)
		{
			com.out(      "&nbsp;<a href=\"");
			link("link.ni.listSwport.expand." + boksid);
			com.out("&vlan="+vlan);
			com.out("#" + boksid);
			com.outl("\">" + expandIcon + "</a>");
		}

		com.outl("      " + katItalic + fontBegin + "" + sysname + "" + fontEnd);
		com.outl("    </td>");
		com.out("  </tr>\n\n\n");

		/*
		if (portBak.equals("Not found")) portBak = "NA";

		direct = "<i>" + direct + ": </i>";

		//com.out("<table>\n");
		com.out("  <tr>\n");
		//com.out("    <td>\n");

		printDepth(depth, strekVertical);
		if (port != null)
		{
			if (missing)
			{
				strekIcon = redCross;
				typeIcon = switchImg;;

				fontBegin = "<font color=red>";
				fontEnd = "</font>";

			} else
			if (type.equals("sw"))
			{
				typeIcon = switchImg;
				label = "<a name=\"" + id + "\"></a>";

			} else
			if (type.equals("hub")) typeIcon = hubImg; else
			if (type.equals("dumhub")) typeIcon = dumhubImg; else
			if (type.equals("gw")) typeIcon = routerImg; else
			if (type.equals("srv")) typeIcon = serverImg; else
			if (type.equals("mas")) typeIcon = maskinImg; else
			typeIcon = undefImg;


			if (portBak.equals("NA"))
			{
				fontBegin = "<font color=red>";
				fontEnd = "</font>";
			}

			// print table
			com.outl("    <td>");

			if (box)
			{
				com.out(      "<a href=\"");
				if (boxOpen)
				{
					link("link.ni.listSwport.close." + id);
				} else
				{
					link("link.ni.listSwport.open." + id);
				}
				com.out("#" + linkLabel);
				com.outl("\">" + strekIcon + "</a>");

			} else
			{
				com.outl("      " + strekIcon);
			}

			com.outl("    </td>");
			com.outl("    <td>");
			//com.outl("      " + typeIcon + label);
			com.outl("      " + label + typeIcon);
			com.outl("    </td>");
			com.outl("    <td align=\"right\">");
			com.outl("      " + port);
			com.outl("    </td>");
			com.outl("    <td align=\"center\">");
			com.outl("      " + portIcon);
			com.outl("    </td>");
			com.outl("    <td align=\"left\">");
			com.outl("      " + portBak);
			com.outl("    </td>");

			com.outl("    <td colspan=50>");

			if (box)
			{
				com.out(      "&nbsp;<a href=\"");
				link("link.ni.listSwport.expand." + id);
				com.out("#" + id);
				com.outl("\">" + expandIcon + "</a>");
			}

			com.outl("      " + direct + fontBegin + "" + name + "" + fontEnd);
			com.outl("    </td>");

		} else
		{
			// root-sw
			com.outl("    <td>");

			if (box)
			{
				label = "<a name=\"" + id + "\"></a>";

				com.out(      "<a href=\"");
				if (boxOpen)
				{
					link("link.ni.listSwport.close." + id );
				} else
				{
					link("link.ni.listSwport.open." + id );
				}
				com.out("#" + linkLabel);
				com.outl("\">" + strekIcon + "</a>");

			} else
			{
				com.outl("      " + strekIcon);
			}

			com.outl("    </td>");
			com.outl("    <td>");
			com.outl("      " + label + switchImg);
			com.outl("    </td>");
			com.outl("    <td colspan=50>");

			if (box)
			{
				com.out(      "&nbsp;<a href=\"");
				link("link.ni.listSwport.expand." + id);
				com.out("#" + id);
				com.outl("\">" + expandIcon + "</a>");
			}

			com.outl("      <font color=blue>" + name + "</font>");
			com.outl("    </td>");
		}

		//com.out("    </td>\n");
		com.out("  </tr>\n");
		//com.out("</table>\n");
		*/
	}
	private void printDepth(int depth, String strek)
	{
		for (int i = 0; i < depth; i++)
		{
			com.outl("   <td>");
			com.outl("    " + strek);
			com.outl("   </td>");
		}
	}


	/* [/ni.checkError]
	 * Finner feil i swport/subnet
	 */

	/*
	private void checkError()
	{
		String level = (com.getp("level") == null) ? "Warning" : com.getp("level");

		if (s.length >= 3)
		{
			if (s[2].equals("level"))
			{
				String sel1 = (level.equals("Fatal")) ? " selected" : "";
				String sel2 = (level.equals("Error")) ? " selected" : "";
				String sel3 = (level.equals("Warning")) ? " selected" : "";
				String sel4 = (level.equals("Notice")) ? " selected" : "";
				com.outl("<option"+sel1+">Fatal</option>");
				com.outl("<option"+sel2+">Error</option>");
				com.outl("<option"+sel3+">Warning</option>");
				com.outl("<option"+sel4+">Notice</option>");
			}
			return;
		}

		// Get begin time
		long beginTime = new GregorianCalendar().getTime().getTime();
		long startTime = beginTime;

		Vector nettelError = new Vector();
		Vector swportError = new Vector();
		Vector subnetError = new Vector();
		HashMap nettel = new HashMap();
		HashSet swportIds = new HashSet();
		HashMap swport = new HashMap();
		HashSet subnetIds = new HashSet();
		HashMap subnet = new HashMap();

		// dump nettel
		String[][] data = db.exece("select id,sysName,kat from nettel where kat!='TS';");
		String[] n_id = data[0];
		String[] n_sysName = data[1];
		String[] n_kat = data[2];
		for (int i = 0; i < data[0].length; i++)
		{
			String[] s = new String[data.length];
			for (int j = 0; j < data.length; j++) s[j] = data[j][i];
			nettel.put(s[0], s);
		}

		// dump swport
		data = db.exece("select id,swid,mp,vlan,portname,status,duplex,speed,porttype,idbak,portBak from swport;");
		for (int i = 0; i < data[0].length; i++)
		{
			String[] s = new String[data.length];
			for (int j = 0; j < data.length; j++) s[j] = data[j][i];
				// spesialtilfelle hvis portname=udef og status=down så leggers det ikke til
				if ( (s[4].toLowerCase().equals("udef") || s[4].toLowerCase().equals("undef")) && s[5].toLowerCase().equals("down") ) continue;
			swport.put(s[1]+":"+s[4], s);
			swportIds.add(s[1]);
		}
		String[][] swtree = new String[3][];
		swtree[0] = data[1];
		swtree[1] = data[9];
		swtree[2] = data[4];

		// dump subnet
		data = db.exece("select id,ruter,interf,speed,gwip,tilruter from subnet where type!='lan';");
		for (int i = 0; i < data[0].length; i++)
		{
			String[] s = new String[data.length];
			for (int j = 0; j < data.length; j++) s[j] = data[j][i];
			subnet.put(s[1]+":"+s[5], s);
			subnetIds.add(s[1]);
		}
		// Get dumptime
		long dumpTime = new GregorianCalendar().getTime().getTime() - beginTime; beginTime += dumpTime;


		// Gå gjennom nettel først
		for (int i = 0; i < n_id.length; i++)
		{
			// sjekk for feil i selve nettel
			{
				swError.defTable("nettel");
				swError.defErrType("Fatal");
				swError.defSysName(n_sysName[i]);
				swError.defMp("");
				swError.defIdBak("");
				swError.defNameBak("");
				swError.defPortBak("");

				if (n_sysName[i] == null || n_sysName[i].equals("NULL") || n_sysName[i].equals(""))
				{
					swError err = new swError(n_id[i]);
					err.setDesc("sysName er null eller blank");
					nettelError.addElement(err);
				} else
				if (n_kat[i] == null || n_kat[i].equals("NULL") || n_kat[i].equals(""))
				{
					swError err = new swError(n_id[i]);
					err.setDesc("kat er null eller blank");
					nettelError.addElement(err);
				} else
				if (n_kat[i].toUpperCase().equals("SRV"))
				{
					// Ikke ta med type SRV
					continue;

				} else
				if (!n_kat[i].equals("GW") && !swportIds.contains(n_id[i]))
				{
					swError err = new swError(n_id[i]);
					err.setDesc("Oppf&oslash;ring i swport tabellen mangler");
					if (n_kat[i] != null && n_kat[i].equals("HUB")) err.setErrType("Notice");
					nettelError.addElement(err);
				} else
				// Sjekk om oppføring i swport er tilstedet
				if (n_kat[i].equals("GW") && !subnetIds.contains(n_id[i]))
				{
					swError err = new swError(n_id[i]);
					err.setDesc("Oppf&oslash;ring i subnet tabellen mangler");
					nettelError.addElement(err);
				}
			}
		}
		// get time to process nettel
		long nettelTime = new GregorianCalendar().getTime().getTime() - beginTime; beginTime += nettelTime;



		// Gå gjennom swport
		Iterator iter = swport.values().iterator();
		while (iter.hasNext())
		{
			String[] s = (String[])iter.next();
			// id,swid,mp,vlan,portname,status,duplex,speed,porttype,idbak,portBak
			String swid = s[1];
			String mp = s[2];
			String vlan = s[3];
			String portname = s[4];
			String status = s[5];
			String duplex = s[6];
			String speed = s[7];
			String porttype = s[8];
			String idbak = s[9];
			String portBak = s[10];


			//if (portname.equals("udef") && status.toLowerCase().equals("up"))
			{
				//com.outl("<tr><td>("+t+")swid: " + swid + " portname: " + portname + " status: " + status + "</td></tr><br>");
			}


			swError err = new swError(swid);
			err.reset();
			err.setTable("swport");
			err.setMp(mp);
			err.setIdBak(idbak);
			err.setNameBak("");
			err.setPortBak(portBak);

			// sjekk om denne enheten fins i nettel
			if (!nettel.containsKey(swid))
			{
				err.setErrType("Fatal");
				err.setDesc("Enheten eksisterer i swport, men ikke i nettel");
				swportError.add(err); continue;
			}

			String sysName = ((String[])nettel.get(swid))[1];
			err.setSysName(sysName);

			// først sjekker vi om porten er udef og nede
			if ((portname.toLowerCase().equals("udef") || portname.toLowerCase().equals("undef")) && status.toLowerCase().equals("down")) continue;
			if ((portname.toLowerCase().equals("udef") || portname.toLowerCase().equals("undef")) && status.toLowerCase().equals("up"))
			{
				// up, men udef eller undef, Warning
				err.setErrType("Warning");
				err.setDesc("Porten er oppe, men portname er udef eller undef");
				swportError.add(err); continue;
			} else
			if (status.toLowerCase().equals("down"))
			{
				// down, men ikke udef eller undef, kun Notice
				err.setErrType("Notice");
				err.setDesc("Porten er nede, men portname er ikke udef eller undef: " + portname);
				swportError.add(err); continue;
			}

			// så sjekker vi om portname følger ?: konvensjonen
			String[] type = misc.tokenizel(portname, ":");
			if (type.length <= 1)
			{
				// nope, ingen konvensjon
				err.setErrType("Notice");
				err.setDesc("Portname f&oslash;lger ikke konvensjonen med kolon: " + portname);
				swportError.add(err); continue;
			}

			// sjekk om name følger *,* konvensjonen
			String[] nameBak = misc.tokenize(type[1], ",");
			if (nameBak.length > 1)
			{
				// ja, idbak MÅ nå være 0
				if (!idbak.equals("0"))
				{
					err.setErrType("Error");
					err.setDesc("Portname bruker komma-konvensjon, men idbak er " + idbak + " (ikke 0)");
					swportError.add(err); continue;
				}
			} else
			{
				String[] info;
				// nei, sjekk hvilken type link vi har
				if (type[0].charAt(0) != 'n' && !type[0].equals("h") && !type[0].equals("link") && type[0].charAt(0) != 'o')
				{
					// nå må idbak være 0
					if (!idbak.equals("0"))
					{
						// finn nameBak
						//String[] info = db.exec("select sysName from nettel where id='" + idbak + "';");
						info = (String[])nettel.get(idbak);

						err.setErrType("Error");
						err.setNameBak(info[1]);
						err.setDesc("Linktype er ikke n, h, o eller link, men idbak er " + idbak + " (ikke 0)");
						swportError.add(err); continue;
					}
					// all ok, return
					continue;
				}

				// nå kan ikke idbak være 0
				if (idbak.equals("0"))
				{
					err.setErrType("Error");
					err.setDesc("Linktype er n, h, o eller link, men idbak=0. Portname: " + portname);
					swportError.add(err); continue;
				}

				// sjekk om det er en gw på andre siden
				nameBak = misc.tokenizel(portname, "-");
				if (nameBak.length <= 1)
				{
					err.setErrType("Fatal");
					err.setDesc("Feil i portname: " + portname);
					swportError.add(err); continue;
				} else
				if (nameBak[1].charAt(0) == 'g')
				{
					// link til gw, alt ok
					continue;
				}

				// konstruer motsatt portname
				String portnameBak;
				type = misc.tokenize(portname, ":");
				if (type[0].charAt(0) == 'n')
				{
					portnameBak = type[0].replace('n', 'o');
				} else
				if (type[0].charAt(0) == 'o')
				{
					portnameBak = type[0].replace('o', 'n');
				} else
				{
					portnameBak = type[0];
				}
				portnameBak += ":" + sysName;

				// hent record fra 'andre siden'
				String msysName = ((String[])nettel.get(idbak))[1];
				if (!swport.containsKey(idbak+":"+portnameBak))
				{
					// record fra 'andre siden' eksisterer ikke
					err.setErrType("Fatal");
					err.setNameBak(msysName);
					err.setDesc("Det fins ingen komplement&aelig;r-oppf&oslash;ring i tabellen");
					swportError.add(err); continue;
				}

				//String[][] data = db.exece("select mp,portname,status,duplex,speed,porttype,idbak,portBak,sysName from swport,nettel where swid=nettel.id and swid='" + idbak + "' and idbak='" + swid + "' and portname='" + portnameBak + "' and (status='Up' or status='up');");
				info = (String[])swport.get(idbak+":"+portnameBak);
				// id,swid,mp,vlan,portname,status,duplex,speed,porttype,idbak,portBak
				String mport = info[2];
				String mvlan = info[3];
				String mportname = info[4];
				String mstatus = info[5];
				String mduplex = info[6];
				String mspeed = info[7];
				String mporttype = info[8];
				String midbak = info[9];
				String mportBak = info[10];



				// sjekk om data fra 'andre siden' stemmer overens
				err.setNameBak(msysName);
				err.setErrType("Error");
				if (!duplex.toLowerCase().equals(mduplex.toLowerCase() )) { err.setDesc("Duplex stemmer ikke overens: "+duplex+" / "+mduplex); swportError.add(err); continue; }
				if (!mp.equals(mportBak)) { err.setDesc("port (mp) stemmer ikke med portBak: "+mp+" / "+mportBak); swportError.add(err); continue; }

				err.setErrType("Warning");
				if (!vlan.toLowerCase().equals("trunk") && !mvlan.toLowerCase().equals("trunk") )
					if (!vlan.toLowerCase().equals(mvlan.toLowerCase() )) { err.setDesc("Vlan stemmer ikke overens: "+vlan+" / "+mvlan); swportError.add(err); continue; }
				if (!status.toLowerCase().equals(mstatus.toLowerCase() )) { err.setDesc("Status stemmer ikke overens: "+status+" / "+mstatus); swportError.add(err); continue; }
				if (!speed.equals(mspeed)) { err.setDesc("Speed stemmer ikke overens: "+speed+" / "+mspeed); swportError.add(err); continue; }
				//if (!porttype.equals(mporttype)) { err.setDesc("Porttype-felt stemmer ikke overens"); swportError.add(err); continue; }

				err.setErrType("Notice");
				if (duplex.indexOf("?") != -1 || mduplex.indexOf("?") != -1) { err.setDesc("?-tegn i duplex felt: "+duplex+" / "+mduplex); swportError.add(err); continue; }




			}
		}
		// get time to process swport
		long swportTime = new GregorianCalendar().getTime().getTime() - beginTime; beginTime += swportTime;


		// Gå gjennom subnet
		iter = subnet.values().iterator();
		while (iter.hasNext())
		{
			String[] s = (String[])iter.next();
			// id,ruter,interf,speed,gwip,tilruter

			String ruter = s[1];
			String interf = s[2];
			String speed = s[3];
			String gwip = s[4];
			String tilruter = s[5];

			swError err = new swError(ruter);
			err.reset();
			err.setTable("subnet");

			err.setMp(interf);
			err.setIdBak(tilruter);

			// sjekk om denne enheten fins i nettel
			if (!nettel.containsKey(ruter))
			{
				err.setErrType("Fatal");
				err.setDesc("Enheten eksisterer i subnet, men ikke i nettel");
				subnetError.add(err); continue;
			}
			String sysName = ((String[])nettel.get(ruter))[1];
			err.setSysName(sysName);

			// Sjekk om enhet i 'andre enden' eksistarer
			if (!nettel.containsKey(tilruter)) continue;
			String msysName = ((String[])nettel.get(tilruter))[1];
			err.setNameBak(msysName);
			if (!subnet.containsKey(tilruter+":"+ruter))
			{
				err.setErrType("Fatal");
				err.setNameBak(msysName);
				err.setDesc("Det fins ingen komplement&aelig;r-oppf&oslash;ring i tabellen");
				subnetError.add(err); continue;
			}

			String[] info = (String[])subnet.get(tilruter+":"+ruter);
			String minterf = s[2];
			String mspeed = s[3];
			String mgwip = s[4];

			// sjekk om data fra 'andre siden' stemmer overens
			err.setErrType("Warning");
			err.setNameBak(msysName);
			err.setPortBak(minterf);
			if (!speed.toLowerCase().equals(mspeed.toLowerCase() )) { err.setDesc("Speed-felt stemmer ikke overens"); subnetError.add(err); continue; }
			if (!gwip.toLowerCase().equals(mgwip.toLowerCase() )) { err.setDesc("Gwip-felt stemmer ikke overens"); subnetError.add(err); continue; }

		}
		// get time to process subnet
		long subnetTime = new GregorianCalendar().getTime().getTime() - beginTime; beginTime += subnetTime;


		//////////////////////////////////////////////////////////////////////////////////
		//com.outl("<pre>");
		//com.outl("Starter å bygge tre");
		// Sjekk for løkker i tre-strukturen i swport
		// Først lag en tre-struktur
		String[] high = db.exec("select id from nettel order by id desc limit 1;");
		int ant = (high[0] != null) ? Integer.parseInt(high[0]) : 0;
		ArrayList[] vertex = new ArrayList[ant];
		boolean[] node = new boolean[ant];
		for (int i = 0; i < vertex.length; i++) vertex[i] = new ArrayList();

		for (int i = 0; i < swtree[0].length; i++)
		{
			if (swtree[1][i].equals("0")) continue;
			String pn = swtree[2][i];
			if (pn.length() < 3 || pn.charAt(0) != 'n' || pn.substring(0, 3).indexOf(":") == -1 )
			{
				//com.outl("Ikke godkjent");
				continue;
			}
			int from = Integer.parseInt(swtree[0][i]);
			int to = Integer.parseInt(swtree[1][i]);
			//com.outl("Edge from "+from+" to "+to);

			//if (vertex[from-1].indexOf(new Integer(to)) == -1 && vertex[to-1].indexOf(new Integer(from)) == -1)
			if (vertex[from-1].indexOf(new Integer(to)) == -1)
			{
				//com.outl("Edge from "+from+" to "+to);
				vertex[from-1].add(new Integer(to));
				node[from-1] = true;
			}


			//if (vertex[to-1].indexOf(new Integer(from)) == -1)
			//	vertex[to-1].add(new Integer(from));


			//node[to-1] = true;
		}
		//vertex[76-1].add(new Integer(365));
		long treeTime = new GregorianCalendar().getTime().getTime() - beginTime; beginTime += treeTime;

		// Kjør algoritme for å finne løkke
		//com.outl("Kjører algoritme");
		final int BFS_WHITE = 0;
		final int BFS_GRAY = 1;
		final int BFS_BLACK = 2;
		int[] color = new int[vertex.length];
		int[] parent = new int[vertex.length];
		int[] d = new int[vertex.length];
		//int startVertex = 121;
		//int startVertex = 109;

		// hent root-switcher
		String[][] rootsw = getRootSwitches();
		String[] rootswId = rootsw[0];

		long rootswTime = new GregorianCalendar().getTime().getTime() - beginTime; beginTime += rootswTime;

		for (int i = 0; i < rootswId.length; i++)
		{
			int startVertex = Integer.parseInt(rootswId[i]);
			//com.outl("Running BFS from sw: " + startVertex);

			// init the queue
			ArrayList q = new ArrayList();

			for (int j = 0; j < vertex.length; j++)
			{
				color[j] = BFS_WHITE;
				parent[j] = -1;
				d[j] = -1;
			}

			//if (!node[startVertex-1]) continue;
			//if (color[startVertex-1] != BFS_WHITE) continue;

			color[startVertex-1] = BFS_GRAY;
			parent[startVertex-1] = -1;
			d[startVertex-1] = 0;

			q.add(new Integer(startVertex));

			while (!q.isEmpty())
			{
				int u = ((Integer)q.get(0)).intValue();

				//while(vertex[u-1].size() > 0)
				for (int j = 0; j < vertex[u-1].size(); j++)
				{
					//int adj = ((Integer)vertex[u-1].pop()).intValue();
					int adj = ((Integer)vertex[u-1].get(j)).intValue();
					if (color[adj-1] == BFS_WHITE)
					{
						color[adj-1] = BFS_GRAY;
						d[adj-1] = d[u-1]+1;
						parent[adj-1] = u;
						q.add(new Integer(adj));
					} else
					{
						//if (vertex[adj-1].indexOf(new Integer(u)) != -1) continue;
						com.outl("*********CYCLE FOUND*********, swid: " + u + " til " + adj + " hopp fra root-switch: " + (d[u-1]+1) + "<br>");
					}
				}
				q.remove(0);
				color[u-1] = BFS_BLACK;
			}

			//if (startVertex == 71) break;
		}


		/*
		com.outl("Number of vertices: " + vertex.length);

		com.outl("+---------------------------------+");
		com.outl("|  Node | Foreldrenode |  Avstand |");
		com.outl("+---------------------------------+");

		for (int i = 0; i < vertex.length; i++)
		{
			//if (color[i] == BFS_WHITE) continue;
			if (parent[i] == -1 && d[i] == -1) continue;
			com.out("| ");

			for (int j = 5; j > (""+(i+1)).length(); j--) com.out(" ");
			com.out("" + (i+1) + " | ");

			String forelder;
			if (parent[i] == -1) forelder = "NIL"; else forelder = ""+parent[i];
			for (int j = 12; j > (forelder).length(); j--) com.out(" ");
			com.out(forelder + " | ");

			String avstand;
			if (d[i] == -1) avstand = "Uendelig"; else avstand = ""+d[i];
			for (int j = 8; j > (avstand).length(); j--) com.out(" ");
			com.out(avstand);

			com.outl(" |");
		}
		com.outl("+---------------------------------+");
		*/


/*
		//com.outl("</pre>");
		long bfsTime = new GregorianCalendar().getTime().getTime() - beginTime; beginTime += bfsTime;
		//////////////////////////////////////////////////////////////////////////////////

		// hent inn level vi skal vise
		//String level = (com.getp("level") == null) ? "Warning" : com.getp("level");

		// tell opp antall av de forskjellige feilene
		int fatal = 0,error = 0,warning = 0,notice = 0;
		for (int i = 0; i < nettelError.size(); i++)
		{
			swError err = (swError)nettelError.elementAt(i);
			err.setLevel(level);
			if (err.getErrType().equals("Fatal")) fatal++;
			if (err.getErrType().equals("Error")) error++;
			if (err.getErrType().equals("Warning")) warning++;
			if (err.getErrType().equals("Notice")) notice++;
		}
		for (int i = 0; i < swportError.size(); i++)
		{
			swError err = (swError)swportError.elementAt(i);
			err.setLevel(level);
			if (err.getErrType().equals("Fatal")) fatal++;
			if (err.getErrType().equals("Error")) error++;
			if (err.getErrType().equals("Warning")) warning++;
			if (err.getErrType().equals("Notice")) notice++;
		}
		for (int i = 0; i < subnetError.size(); i++)
		{
			swError err = (swError)subnetError.elementAt(i);
			err.setLevel(level);
			if (err.getErrType().equals("Fatal")) fatal++;
			if (err.getErrType().equals("Error")) error++;
			if (err.getErrType().equals("Warning")) warning++;
			if (err.getErrType().equals("Notice")) notice++;
		}
		// skriv ut antall feil
		com.outl("<table>");
		com.outl(" <tr>");
		com.outl("  <td colspan=50>Fatal errors: <b>" + fatal + "</b> Errors: <b>" + error + "</b> Warnings: <b>" + warning + "</b> Notices: <b>" + notice + "</b></td>");
		com.outl(" </tr>");

		// print header
		com.outl(" <tr>");
		com.outl("  <td><b>Tabell</b></td>");
		com.outl("  <td><b>Type</b></td>");
		com.outl("  <td><b>swid</b></td>");
		com.outl("  <td><b>sysName</b></td>");
		com.outl("  <td><b>mp</b></td>");
		com.outl("  <td><b>idBak</b></td>");
		com.outl("  <td><b>nameBak</b></td>");
		com.outl("  <td><b>portBak</b></td>");
		com.outl("  <td><b>Tekst</b></td>");
		com.outl(" </tr>");

		// Sortering
		Collections.sort(nettelError);
		Collections.sort(swportError);
		Collections.sort(subnetError);

		// print feil fra nettel
		for (int i = 0; i < nettelError.size(); i++) printError((swError)nettelError.elementAt(i));

		// print feil fra swport
		if (swportError.size() > 0) com.outl("  <tr><td colspan=50><b>Errors in swport</b></td></tr>");
		for (int i = 0; i < swportError.size(); i++) printError((swError)swportError.elementAt(i));

		// print feil fra subnet
		if (subnetError.size() > 0) com.outl("  <tr><td colspan=50><b>Errors in subnet</b></td></tr>");
		for (int i = 0; i < subnetError.size(); i++) printError((swError)subnetError.elementAt(i));

		com.outl("</table>");


		// Get end time
		long usedTime = new GregorianCalendar().getTime().getTime() - startTime;
		com.out("<br>\n");
		com.out("Total processing time: <b>" + usedTime + " ms</b><br>\n");
		com.out("Database dump time: <b>" + dumpTime + " ms</b><br>\n");
		com.out("Time to process nettel: <b>" + nettelTime + " ms</b><br>\n");
		com.out("Time to process swport: <b>" + swportTime + " ms</b><br>\n");
		com.out("Time to process subnet: <b>" + subnetTime + " ms</b><br>\n");
		com.out("Time to build tree: <b>" + treeTime + " ms</b><br>\n");
		com.out("Time to find root-switches: <b>" + rootswTime + " ms</b><br>\n");
		com.out("Time to run (BFS) cycle check: <b>" + bfsTime + " ms</b><br>\n");

	}
	private void printError(swError err)
	{
		if (err.show())
		{
			String font1 = "<font color=\"" + err.getColor() + "\">";
			String font2 = "</font>";

			com.outl(" <tr>");
			com.outl("  <td>" + font1 + err.getTable() + font2 + "</td>");
			com.outl("  <td>" + font1 + err.getErrType() + font2 + "</td>");
			com.outl("  <td>" + font1 + err.getId() + font2 + "</td>");
			com.outl("  <td>" + font1 + err.getSysName() + font2 + "</td>");
			com.outl("  <td>" + font1 + err.getMp() + font2 + "</td>");
			com.outl("  <td>" + font1 + err.getIdBak() + font2 + "</td>");
			com.outl("  <td>" + font1 + err.getNameBak() + font2 + "</td>");
			com.outl("  <td>" + font1 + err.getPortBak() + font2 + "</td>");
			com.outl("  <td>" + font1 + err.getDesc() + font2 + "</td>");
			com.outl(" </tr>");
		}
	}
	*/


	/* [/ni.checkError]
	 * Finner feil i swport/subnet
	 */
	/*
	private void checkError2()
	{
		Vector swError = new Vector();
		Vector portError = new Vector();

		String updateDb = com.getp("updateDb");

		if (updateDb != null || com.getData("checkErrorSwError") == null || com.getData("checkErrorPortError") == null || ((Vector)com.getData("checkErrorSwError")).size() <= 0 )
		{
			// Start feil-søk
			// først henter vi ut hele nettel og sjekker om alle enheter har tilsvarende gyldig oppføring i swport
			String[][] data = db.exece("select id,sysName,kat from nettel order by id;");
			String[] id = data[0];
			String[] sysName = data[1];
			String[] kat = data[2];

			for (int i = 0; i < id.length; i++)
			{
				// sjekk for feil i selve nettel
				if (sysName[i] == null || sysName[i].equals("NULL") || sysName[i].equals(""))
				{
					swError err = new swError(id[i]);
					err.setTable("nettel");
					err.setErrType("Fatal");
					err.setSysName(sysName[i]);
					err.setMp("");
					err.setIdBak("");
					err.setNameBak("");
					err.setPortBak("");
					err.setDesc("sysName er null eller blank");
					swError.addElement(err);
				}
				if (kat[i] == null || kat[i].equals("NULL") || kat[i].equals(""))
				{
					swError err = new swError(id[i]);
					err.setTable("nettel");
					err.setErrType("Fatal");
					err.setSysName(sysName[i]);
					err.setMp("");
					err.setIdBak("");
					err.setNameBak("");
					err.setPortBak("");
					err.setDesc("kat er null eller blank");
					swError.addElement(err);
				}

				// sjekk om oppføring i swport er riktig
				data = db.exece("select mp,portname,status,duplex,speed,porttype,idbak,portBak from swport where swid='" + id[i] + "';");
				String[] port = data[0];
				String[] portname = data[1];
				String[] status = data[2];
				String[] duplex = data[3];
				String[] speed = data[4];
				String[] porttype = data[5];
				String[] idbak = data[6];
				String[] portBak = data[7];

				if (port[0] == null)
				{
					swError err = new swError(id[i]);
					err.setTable("swport");
					err.setErrType("Fatal");
					err.setSysName(sysName[i]);
					err.setMp("");
					err.setIdBak("");
					err.setNameBak("");
					err.setPortBak("");
					err.setDesc("Oppf&oslash;ring i tabellen mangler");
					//swError.addElement(err);
				} else
				{
					// oppføring funnet, sjekk om det stemmer
					for (int j = 0; j < port.length; j++)
					{
						swError portErr = verifySwRecord(id[i], sysName[i], port[j], portname[j], status[j], duplex[j], speed[j], porttype[j], idbak[j], portBak[j]);
						//swError portErr = null;

						if (portErr != null)
						{
							portError.addElement(portErr);
						}


					}
				}
			}

			com.setData("checkErrorSwError", swError);
			com.setData("checkErrorPortError", portError);

		} else
		{
			swError = (Vector)com.getData("checkErrorSwError");
			portError = (Vector)com.getData("checkErrorPortError");
		}

		// hent inn level vi skal vise
		String level = "Warning";
		if (com.getp("level") != null)
		{
			level = com.getp("level");
		}

		// tell opp antall av de forskjellige feilene
		int fatal = 0;
		int error = 0;
		int warning = 0;
		int notice = 0;
		for (int i = 0; i < swError.size(); i++)
		{
			swError err = (swError)swError.elementAt(i);
			err.setLevel(level);
			if (err.getErrType().equals("Fatal")) fatal++;
			if (err.getErrType().equals("Error")) error++;
			if (err.getErrType().equals("Warning")) warning++;
			if (err.getErrType().equals("Notice")) notice++;
		}
		for (int i = 0; i < portError.size(); i++)
		{
			swError err = (swError)portError.elementAt(i);
			err.setLevel(level);
			if (err.getErrType().equals("Fatal")) fatal++;
			if (err.getErrType().equals("Error")) error++;
			if (err.getErrType().equals("Warning")) warning++;
			if (err.getErrType().equals("Notice")) notice++;
		}
		// skriv ut antall feil
		com.outl("<table>");
		com.outl(" <tr>");
		com.outl("  <td colspan=50>Fatal errors: <b>" + fatal + "</b> Errors: <b>" + error + "</b> Warnings: <b>" + warning + "</b> Notices: <b>" + notice + "</b></td>");
		com.outl(" </tr>");

		com.outl(" <tr>");
		com.outl("  <td><b>Tabell</b></td>");
		com.outl("  <td><b>Type</b></td>");
		com.outl("  <td><b>swid</b></td>");
		com.outl("  <td><b>sysName</b></td>");
		com.outl("  <td><b>mp</b></td>");
		com.outl("  <td><b>idBak</b></td>");
		com.outl("  <td><b>nameBak</b></td>");
		com.outl("  <td><b>portBak</b></td>");
		com.outl("  <td><b>Tekst</b></td>");
		com.outl(" </tr>");


		for (int i = 0; i < swError.size(); i++)
		{
			swError err = (swError)swError.elementAt(i);
			if (err.show())
			{
				String font1 = "<font color=\"" + err.getColor() + "\">";
				String font2 = "</font>";

				com.outl(" <tr>");
				com.outl("  <td>" + font1 + err.getTable() + font2 + "</td>");
				com.outl("  <td>" + font1 + err.getErrType() + font2 + "</td>");
				com.outl("  <td>" + font1 + err.getId() + font2 + "</td>");
				com.outl("  <td>" + font1 + err.getSysName() + font2 + "</td>");
				com.outl("  <td>" + font1 + err.getMp() + font2 + "</td>");
				com.outl("  <td>" + font1 + err.getIdBak() + font2 + "</td>");
				com.outl("  <td>" + font1 + err.getNameBak() + font2 + "</td>");
				com.outl("  <td>" + font1 + err.getPortBak() + font2 + "</td>");
				com.outl("  <td>" + font1 + err.getDesc() + font2 + "</td>");
				com.outl(" </tr>");
			}
		}

		if (portError.size() > 0)
		{
			com.outl("  <tr><td colspan=50><b>Errors in swport</b></td></tr>");
		}

		for (int i = 0; i < portError.size(); i++)
		{
			swError err = (swError)portError.elementAt(i);
			if (err.show())
			{
				String font1 = "<font color=\"" + err.getColor() + "\">";
				String font2 = "</font>";

				com.outl(" <tr>");
				com.outl("  <td>" + font1 + err.getTable() + font2 + "</td>");
				com.outl("  <td>" + font1 + err.getErrType() + font2 + "</td>");
				com.outl("  <td>" + font1 + err.getId() + font2 + "</td>");
				com.outl("  <td>" + font1 + err.getSysName() + font2 + "</td>");
				com.outl("  <td>" + font1 + err.getMp() + font2 + "</td>");
				com.outl("  <td>" + font1 + err.getIdBak() + font2 + "</td>");
				com.outl("  <td>" + font1 + err.getNameBak() + font2 + "</td>");
				com.outl("  <td>" + font1 + err.getPortBak() + font2 + "</td>");
				com.outl("  <td>" + font1 + err.getDesc() + font2 + "</td>");
				com.outl(" </tr>");
			}
		}


		com.outl("</table>");





	}
	private swError verifySwRecord(String swid, String sysName, String port, String portname, String status, String duplex, String speed, String porttype, String idbak, String portBak)
	{
		swError err = new swError(swid);
		err.setTable("swport");

		err.setSysName(sysName);
		err.setMp(port);
		err.setIdBak(idbak);
		err.setNameBak("");
		err.setPortBak(portBak);

		// først sjekker vi om porten er udef og nede
		if ((portname.toLowerCase().equals("udef") || portname.toLowerCase().equals("undef")) && status.toLowerCase().equals("down"))
		{
			// alt ok
			return null;
		} else
		if ((portname.toLowerCase().equals("udef") || portname.toLowerCase().equals("undef")) && status.toLowerCase().equals("up"))
		{
			// up, men udef eller undef, Warning
			err.setErrType("Warning");
			err.setDesc("Porten er oppe, men portname er udef eller undef");
			return err;
		} else
		if (status.toLowerCase().equals("down"))
		{
			// down, men ikke udef eller undef, kun Notice
			err.setErrType("Notice");
			err.setDesc("Porten er nede, men portname er ikke udef eller undef: " + portname);
			return err;
		}


		// så sjekker vi om portname følger ?: konvensjonen
		String[] type = misc.tokenizel(portname, ":");
		if (type.length <= 1)
		{
			// nope, ingen konvensjon
			err.setErrType("Notice");
			err.setDesc("Portname f&oslash;lger ikke konvensjonen med kolon: " + portname);
			return err;
		}

		// sjekk om name følger *,* konvensjonen
		String[] nameBak = misc.tokenize(type[1], ",");
		if (nameBak.length > 1)
		{
			// ja, idbak MÅ nå være 0
			if (!idbak.equals("0"))
			{
				err.setErrType("Error");
				err.setDesc("Portname bruker komma-konvensjon, men idbak er " + idbak + " (ikke 0)");
				return err;
			}

		} else
		{
			// nei, sjekk hvilken type link vi har
			if (type[0].charAt(0) != 'n' && !type[0].equals("h") && !type[0].equals("link") && type[0].charAt(0) != 'o')
			{
				// nå må idbak være 0
				if (!idbak.equals("0"))
				{
					// finn nameBak
					String[] info = db.exec("select sysName from nettel where id='" + idbak + "';");

					err.setErrType("Error");
					err.setNameBak(info[0]);
					err.setDesc("Linktype er ikke n, h, o eller link, men idbak er " + idbak + " (ikke 0)");
					return err;
				}
				// all ok, return
				return null;
			}

			// nå kan ikke idbak være 0
			if (idbak.equals("0"))
			{
				err.setErrType("Error");
				err.setDesc("Linktype er n, h, o eller link, men idbak=0. Portname: " + portname);
				return err;
			}

			// sjekk om det er en gw på andre siden
			nameBak = misc.tokenizel(portname, "-");
			if (nameBak.length <= 1)
			{
				err.setErrType("Fatal");
				err.setDesc("Feil i portname: " + portname);
				return err;
			} else
			if (nameBak[1].charAt(0) == 'g')
			{
				// link til gw, alt ok
				return null;
			}

			// konstruer motsatt portname
			String portnameBak;
			type = misc.tokenize(portname, ":");
			if (type[0].charAt(0) == 'n')
			{
				portnameBak = type[0].replace('n', 'o');
			} else
			if (type[0].charAt(0) == 'o')
			{
				portnameBak = type[0].replace('o', 'n');
			} else
			{
				portnameBak = type[0];
			}
			portnameBak += ":" + sysName;

			// hent record fra 'andre siden'
			String[][] data = db.exece("select mp,portname,status,duplex,speed,porttype,idbak,portBak,sysName from swport,nettel where swid=nettel.id and swid='" + idbak + "' and idbak='" + swid + "' and portname='" + portnameBak + "' and (status='Up' or status='up');");
			String[] mport = data[0];
			String[] mportname = data[1];
			String[] mstatus = data[2];
			String[] mduplex = data[3];
			String[] mspeed = data[4];
			String[] mporttype = data[5];
			String[] midbak = data[6];
			String[] mportBak = data[7];
			String[] msysName = data[8];

			if (mport[0] == null)
			{
				// record fra 'andre siden' eksisterer ikke

				// finn nameBak
				String[] info = db.exec("select sysName from nettel where id='" + idbak + "';");

				err.setErrType("Fatal");
				err.setNameBak(info[0]);
				err.setDesc("Det fins ingen komplement&aelig;r-oppf&oslash;ring i tabellen");
				return err;
			}

			// sjekk om data fra 'andre siden' stemmer overens

			err.setErrType("Warning");
			err.setNameBak(msysName[0]);
			if (!status.toLowerCase().equals(mstatus[0].toLowerCase() )) { err.setDesc("Status-felt stemmer ikke overens"); return err; }
			if (!duplex.toLowerCase().equals(mduplex[0].toLowerCase() )) { err.setDesc("Duplex-felt stemmer ikke overens"); return err; }
			if (!speed.equals(mspeed[0])) { err.setDesc("Speed-felt stemmer ikke overens"); return err; }
			if (!porttype.equals(mporttype[0])) { err.setDesc("Porttype-felt stemmer ikke overens"); return err; }

			err.setErrType("Error");
			if (!port.equals(mportBak[0])) { err.setDesc("port-feltet (mp) stemmer ikke med portBak-feltet"); return err; }


			return null;


		}

		return null;


	}
	*/



	/* [/ni.listSwport]
	 * Skriv ut swport
	 */

	/*
	private void listSwport()
	{
		String name = "<b>NTNU network</b>";
		String imgRoot = "<img border=0 src=\"" + gfxRoot + "/";
		String ntnuImg = imgRoot + "ntnunet.gif" + "\">";
		String expandIcon = imgRoot + "expand.gif" + "\" alt=\"Expand entire branch\">";
		String label = "<a name=\"0\"></a>";
		com.outl("    <td>");
		com.outl("      " + label + ntnuImg);
		com.outl("    </td>");
		com.outl("    <td colspan=50>");

		com.out(      "<a href=\"");
		link("link.ni.listSwport.expand." + "0");
		com.out("#" + "0");
		com.outl("\">" + expandIcon + "</a>");

		com.outl("      <font color=black>" + name + "</font>");
		com.outl("    </td>");


		String[][] data = getRootSwitches();

		String[] swId = data[0];
		String[] swName = data[1];

		HashMap trav;
		Object o = com.getUser().getData("traverseList");
		if (o != null)
		{
			trav = (HashMap)o;
		} else
		{
			trav = new HashMap();
		}

		// sjekk om vi skal traverese hele ntnunet
		Boolean b = (Boolean)trav.get("0");
		if (b == null)
		{
			b = new Boolean(false);
		}

		com.out("<table border=0 cellspacing=0 cellpadding=0>\n");
		for (int i = 0; i < swId.length; i++)
		{
			swportExpand(swId[i], swName[i], null, "0", null, null, 0, trav, b.booleanValue() );
		}
		com.out("</table>\n");

	}

	private void swportExpand(String id, String swName, String port, String parentId, String parentName, String parentPort, int depth, HashMap trav, boolean traverse)
	{
		//String[][] data = db.exece("select portname,mp,idbak,sysName,portBak from swport,nettel where idbak=nettel.id and swid='" + id + "' and portname like 'n%:%' and idbak!='null';");
		String[][] data = db.exece("select portname,mp,status,idbak,portBak from swport where swid='" + id + "' and portname like '%:%';");
		String[] portname = data[0];
		String[] mp = data[1];
		String[] status = data[2];
		String[] idbak = data[3];
		String[] portBak = data[4];

		int strekType = BOXOPEN_BOTH;

		if (portname[0] == null)
		{
			printNode(id, swName, port, findPortBak(swName, null, parentName, false), parentId, parentName, depth, "n", "sw", REDCROSS, true);
			//printNode(id, parentName, swName, port, parentPort, depth, "sw", false, true);
			return;
		}

		// sjekk om vi skal traverse videre
		{
			Object o = trav.get(id);
			if (o != null)
			{
				Boolean b = (Boolean)o;
				traverse = b.booleanValue();
			}
		}

		if (trav.get(id) == null && !traverse)
		{
			// ikke traverse denne greinen
			strekType = BOXCLOSED_BOTH;
			printNode(id, swName, port, findPortBak(swName, null, parentName, false), parentId, parentName, depth, "n", "sw", strekType, false);
			return;
		}

		// hent ut navn fra portname
		String[] typeBak = new String[portname.length];
		String[] nameBak = new String[portname.length];
		for (int i = 0; i < portname.length; i++)
		{
			String[] pn = misc.tokenizel(portname[i], ":");
			typeBak[i] = pn[0];
			nameBak[i] = pn[1];
		}

		printNode(id, swName, port, findPortBak(swName, null, parentName, false), parentId, parentName, depth, "n", "sw", strekType, false);
		//printNode(id, parentName, swName, port, parentPort, depth, "sw", strekType, false);

		for (int j = 0; j < portname.length; j++)
		{
			// default
			strekType = STREK_BOTH;
			if (j == portname.length-1) strekType = STREK_BOTTOM;

			String[] type = misc.tokenize(nameBak[j], ",");
			if (type.length > 1)
			{
				// portnavn etter konvensjon for ikke-snmp hub
				printNode(idbak[j], nameBak[j], mp[j], portBak[j], parentId, swName, depth+1, "n", "dumhub", strekType, false);
			} else
			{
				type = misc.tokenizel(portname[j], "-");
				if (type.length == 1)
				{
					// annen type uten konvensjon
					printNode(idbak[j], nameBak[j], mp[j], portBak[j], parentId, swName, depth+1, "n", typeBak[j], strekType, false);

				} else
				if (type[1].charAt(0) == 's' && type[0].charAt(0) == 'n')
				{
					// downlink til switch, sjekk om vi skal traverse
					if (trav.get(id) != null || traverse)
					{
						swportExpand(idbak[j], nameBak[j], mp[j], id, swName, portBak[j], depth+1, trav, traverse);
					} else
					{
						strekType = BOXCLOSED_BOTH;
						if (j == portname.length-1) strekType = BOXCLOSED_BOTTOM;

						//printNode(idbak[j], nameBak[j], mp[j], findPortBak(nameBak[j], null, swName, false), parentId, swName, depth+1, "n", "sw", strekType, false);
						printNode(idbak[j], nameBak[j], mp[j], portBak[j], parentId, swName, depth+1, "n", "sw", strekType, false);
					}
				} else
				if (type[1].charAt(0) == 's')
				{
					// up/hz link til sw, bare print ut
					//printNode(idbak[j], nameBak[j], mp[j], findPortBak(nameBak[j], null, swName, false), parentId, swName, depth+1, typeBak[j], "sw", strekType, false);
					printNode(idbak[j], nameBak[j], mp[j], portBak[j], parentId, swName, depth+1, typeBak[j], "sw", strekType, false);

				} else
				if (type[1].charAt(0) == 'g')
				{
					// up/hz/dn link til gw, bare print ut
					//printNode(idbak[j], nameBak[j], mp[j], findPortBak(nameBak[j], null, swName, false), parentId, swName, depth+1, typeBak[j], "gw", strekType, false);
					printNode(idbak[j], nameBak[j], mp[j], portBak[j], parentId, swName, depth+1, typeBak[j], "gw", strekType, false);

				} else
				if (type[1].charAt(0) == 'h')
				{
					// dn link til hub, bare print ut
					//printNode(idbak[j], nameBak[j], mp[j], findPortBak(nameBak[j], null, swName, false), parentId, swName, depth+1, typeBak[j], "hub", strekType, false);
					printNode(idbak[j], nameBak[j], mp[j], portBak[j], parentId, swName, depth+1, typeBak[j], "hub", strekType, false);

				} else
				{
					// dn link til annen type, bare print ut
					printNode(idbak[j], nameBak[j], mp[j], portBak[j], parentId, swName, depth+1, "n", typeBak[j], strekType, false);

				}

			}
		}
	}

	private void printNode(String id, String name, String port, String portBak, String parentId, String parentName, int depth, String direct, String type, int strekType, boolean missing)
	{
		String imgRoot = "<img border=0 src=\"" + gfxRoot + "/";
		String expandIcon = imgRoot + "expand.gif" + "\" alt=\"Expand entire branch\">";
		String portIcon = imgRoot + "porticon.gif" + "\">";
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


		String label = "";
		String linkLabel = "";
		String strekIcon = "";
		String typeIcon = "";

		String fontBegin = "";
		String fontEnd = "";

		boolean box = false; boolean boxOpen = false;

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
				linkLabel = parentId;
				box = true;
				boxOpen = true;
			break;

			case BOXOPEN_BOTTOM:
				strekIcon = boxOpenBottom;
				linkLabel = parentId;
				box = true;
				boxOpen = true;
			break;

			case BOXCLOSED_BOTH:
				strekIcon = boxClosedBoth;
				linkLabel = id;
				box = true;
			break;

			case BOXCLOSED_BOTTOM:
				strekIcon = boxClosedBottom;
				linkLabel = id;
				box = true;
			break;

			default:
				strekIcon = strekBoth;
			break;
		}

		if (portBak.equals("Not found")) portBak = "NA";

		direct = "<i>" + direct + ": </i>";

		//com.out("<table>\n");
		com.out("  <tr>\n");
		//com.out("    <td>\n");

		printDepth(depth, strekVertical);
		if (port != null)
		{
			if (missing)
			{
				strekIcon = redCross;
				typeIcon = switchImg;;

				fontBegin = "<font color=red>";
				fontEnd = "</font>";

			} else
			if (type.equals("sw"))
			{
				typeIcon = switchImg;
				label = "<a name=\"" + id + "\"></a>";

			} else
			if (type.equals("hub")) typeIcon = hubImg; else
			if (type.equals("dumhub")) typeIcon = dumhubImg; else
			if (type.equals("gw")) typeIcon = routerImg; else
			if (type.equals("srv")) typeIcon = serverImg; else
			if (type.equals("mas")) typeIcon = maskinImg; else
			typeIcon = undefImg;


			if (portBak.equals("NA"))
			{
				fontBegin = "<font color=red>";
				fontEnd = "</font>";
			}

			// print table
			com.outl("    <td>");

			if (box)
			{
				com.out(      "<a href=\"");
				if (boxOpen)
				{
					link("link.ni.listSwport.close." + id);
				} else
				{
					link("link.ni.listSwport.open." + id);
				}
				com.out("#" + linkLabel);
				com.outl("\">" + strekIcon + "</a>");

			} else
			{
				com.outl("      " + strekIcon);
			}

			com.outl("    </td>");
			com.outl("    <td>");
			//com.outl("      " + typeIcon + label);
			com.outl("      " + label + typeIcon);
			com.outl("    </td>");
			com.outl("    <td align=\"right\">");
			com.outl("      " + port);
			com.outl("    </td>");
			com.outl("    <td align=\"center\">");
			com.outl("      " + portIcon);
			com.outl("    </td>");
			com.outl("    <td align=\"left\">");
			com.outl("      " + portBak);
			com.outl("    </td>");

			com.outl("    <td colspan=50>");

			if (box)
			{
				com.out(      "&nbsp;<a href=\"");
				link("link.ni.listSwport.expand." + id);
				com.out("#" + id);
				com.outl("\">" + expandIcon + "</a>");
			}

			com.outl("      " + direct + fontBegin + "" + name + "" + fontEnd);
			com.outl("    </td>");

		} else
		{
			// root-sw
			com.outl("    <td>");

			if (box)
			{
				label = "<a name=\"" + id + "\"></a>";

				com.out(      "<a href=\"");
				if (boxOpen)
				{
					link("link.ni.listSwport.close." + id );
				} else
				{
					link("link.ni.listSwport.open." + id );
				}
				com.out("#" + linkLabel);
				com.outl("\">" + strekIcon + "</a>");

			} else
			{
				com.outl("      " + strekIcon);
			}

			com.outl("    </td>");
			com.outl("    <td>");
			com.outl("      " + label + switchImg);
			com.outl("    </td>");
			com.outl("    <td colspan=50>");

			if (box)
			{
				com.out(      "&nbsp;<a href=\"");
				link("link.ni.listSwport.expand." + id);
				com.out("#" + id);
				com.outl("\">" + expandIcon + "</a>");
			}

			com.outl("      <font color=blue>" + name + "</font>");
			com.outl("    </td>");
		}

		//com.out("    </td>\n");
		com.out("  </tr>\n");
		//com.out("</table>\n");
	}
	private void printDepth(int depth, String strek)
	{
		for (int i = 0; i < depth; i++)
		{
			com.outl("   <td>");
			com.outl("    " + strek);
			com.outl("   </td>");
		}
	}
	*/

	/* [/ni.searchSwport]
	 * Søker etter nettel-enheter og viser dem via listSwport
	 */
	private void searchSwport()
	{




	}


	/************************************************************
	* Misc functions											*
	* 															*
	************************************************************/

	/*
	 * Finner alle root-switcher
	 */
	/*
	private String[][] findRootSwitches()
	{
		ResultSet rs = Database.query("SELECT DISTINCT boksid,sysName FROM swport JOIN boks USING (boksid) WHERE portnavn LIKE 'o:%-gw%'");


	}
	*/

	/*
	 * Finner alle root-switcher
	 */
	/*
	private String[][] getRootSwitches()
	{
		// finn alle root-switcher
		HashMap hm = new HashMap();
		String[][] data = db.exece("select swid,sysName from swport,nettel where swid=nettel.id and portname like 'o:%-gw%' group by swid;");
		String[] swid = data[0];
		String[] swName = data[1];
		for (int i = 0; i < swid.length; i++)
		{
			hm.put(swid[i], swName[i]);
		}

		data = db.exece("select swid,sysName from swport,nettel where swid=nettel.id and portname like 'h:%-sw' group by swid;");
		swid = data[0];
		swName = data[1];
		for (int i = 0; i < swid.length; i++)
		{
			if (hm.get(swid[i]) == null)
			{
				// sjekk om denne er en root-switch
				String[] info = db.exec("select swid from swport where swid='" + swid[i] + "' and portname like 'o:%';");
				if (info[0] == null)
				{
					// jepp, root-switch
					hm.put(swid[i], swName[i]);
				}
			}
		}

		String[][] sw = new String[2][hm.size()];
		int i = 0;
		Set entries = hm.entrySet();
		Iterator iter = entries.iterator();
		while (iter.hasNext())
		{
			Map.Entry entry = (Map.Entry)iter.next();
			String key = (String)entry.getKey();
			String value = (String)entry.getValue();

			sw[0][i] = key;
			sw[1][i] = value;

			i++;
		}
		return sw;
	}
	*/



	/*
	 * Finner gw for en gitt ip
	 */
	/*
	private String findGwIp(String ip)
	{
		FindGateway fg = findGw();
		return fg.findGw(ip);
	}

	private String findGwBits(String ip)
	{
		FindGateway fg = findGw();
		fg.findGw(ip);

		return fg.getLastBits();
	}

	private FindGateway findGw()
	{
		FindGateway fg;
		fg = (FindGateway)com.getData("FindGateway");

		if (fg == null)
		{
			String[][] data = db.exece("select gwip,bits from subnet;");
			fg = new FindGateway(data[0], data[1]);
			com.setData("FindGateway", fg, false);
		}
		return fg;
	}
	*/

	/*
	 * Finner gw-ip for en gitt ip
	 */
/*
	private String findGwIp(String ip)
	{
		String[] oct = misc.tokenize(ip, ".");

		String[][] info = db.exece("select gwip,bits from subnet where gwip like '" + oct[0]+"."+oct[1]+"."+oct[2] + ".%';");
		String[] gw = info[0];
		String[] bits = info[1];

		if (gw[0] != null)
		{
			// funnet >23 bits maske
			if (gw.length > 1)
			{
				//funnet >24 bits maske
				int lastgw = 1;
				int oct3 = Integer.parseInt(oct[3]);

				for (int i = 0; i < gw.length; i++)
				{
					String[] gwoct = misc.tokenize(gw[i], ".");

					if (Integer.parseInt(gwoct[3]) > oct3)
					{
						return oct[0] + "." + oct[1] + "." + oct[2] + "." + lastgw;
					}

					if (Integer.parseInt(gwoct[3]) > lastgw)
					{
						lastgw = Integer.parseInt(gwoct[3]);
					}

				}
				return oct[0] + "." + oct[1] + "." + oct[2] + "." + lastgw;

			} else
			{
				// funnet 24 bits maske
				return gw[0];
			}

		} else
		{
			// 23 bits maske
			String gwip = oct[0] + "." + oct[1] + ".";

			int oct2 = Integer.parseInt(oct[2]);
			oct2--;

			gwip += oct2 + ".1";

			return gwip;
		}
	}
*/

	/*
	 * Finner port i andre enden
	 */

	/*
	private String findPortBak(String name, String ip, String nameFra, boolean useSnmp)
	{
		// wrapper
		return findPortBak(name, ip, nameFra, useSnmp, 0);
	}

	private String findPortBak(String name, String ip, String nameFra, boolean useSnmp, int downlink)
	{
		if (ip != null && useSnmp)
		{
			String[][] data = db.exece("select ro,type from community,nettel where nettelid=nettel.id and ip='" + ip + "';");

			String[] community = data[0];
			String[] type = data[1];

			String portBak = "Not found";
			if (community[0] != null)
			{
				// finn gwmac
				String gwip = findGwIp(ip);
				String[] gwmac = db.exec("select mac from arp where ip='" + gwip + "';");

				com.outl("gwip: " + gwip + " gwmac: " + gwmac[0]);

				if (gwmac[0] != null)
				{
					// fetch old unit/port
					int defUnit = 0;
					int defPort = 0;
					String[] oldPort = db.exec("select mp from swport,nettel where swid=nettel.id and sysName='" + name + "' and status='Up';");
					if (oldPort[0] != null && oldPort[0].length() > 0)
					{
						oldPort = misc.tokenize(oldPort[0], ".");
						defUnit = Integer.parseInt(oldPort[0]);
						defPort = Integer.parseInt(oldPort[1]);
					}

					// finn MIB
					String mib;
					HubPort hp;

					if (type[0].equals("SW3300") || type[0].equals("SW1100") || type[0].equals("PS40") )
					{
						mib = ".1.3.6.1.4.1.43.10.22.2.1.3";
						//Snmp snmp = new Snmp(ip, community[0], mib, com);
						//hp = snmp.findPort(gwmac[0], type[0], defUnit, defPort, com, downlink);

					} else
					if (type[0].equals("PS10") )
					{
						mib = ".1.3.6.1.4.1.43.10.9.5.1.6";
						//Snmp snmp = new Snmp(ip, community[0], mib, com);
						//hp = snmp.findPortGetNext(gwmac[0], com);
					} else
					if (type[0].equals("Off8") )
					{
						return "1.9"; // Office8 always use 1.9 as uplink-port

					} else
					{
						return "Unsupported type";
					}
					hp = null;

					//String[] stacs = db.exec("select id from nettel where sysName like '" + name + "%';");

					//Snmp snmp = new Snmp(ip, community[0], mib);

					//HubPort hp = snmp.findPort(gwmac[0], com);
					//HubPort hp = snmp.findPort(gwmac[0], stacs.length, com);
					if (hp != null && defUnit != 0 && defPort != 0)
					{
						if (hp.getUnit() == defUnit && hp.getPort() == defPort)
						{
							portBak = "No change";
						} else
						{
							portBak = hp.getUnit() + "." + hp.getPort();
						}
					} else
					{
						portBak = "Not found";
					}
				}
			}
			return portBak;

		} else
		{
			// hent portBak fra swport
			if (nameFra != null)
			{
				String[] portBak = db.exec("select mp from swport,nettel where swid=nettel.id and sysName='" + name + "' and portname like '%:" + nameFra + "';");
				if (portBak[0] != null)
				{
					return portBak[0];
				} else
				{
					return "Not found";
				}

			} else
			{
				String[] portBak = db.exec("select mp from swport,nettel where swid=nettel.id and sysName='" + name + "' and portname like 'o:%';");
				if (portBak[0] != null)
				{
					return portBak[0];
				} else
				{
					return "Not found";
				}
			}

		}

	}
	*/







	/************************************************************
	* Level 2 functions											*
	* user.<>.*													*
	************************************************************/

	/* [/admin.temp.list.*]
	 * Viser verdi fra felt i users-tabell
	 */

	/*
	private void list()
	{
		if (!com.cap("viewUsers")) { return; }

		if (s.length < 3)
		{
			return;
		}

		String field = com.getp("searchField");

		String[] info = (String[])com.getUser().getData("adminListUsers" + s[3]);
		if (info == null)
		{
			String tabell;

			if (s[3].equals("login"))
			{
				tabell = "users.login";
			} else
			{
				tabell = s[3];
			}

			if (field.equals("login"))
			{
				field = "users.login";
			}

			String search = com.getp("searchString");
			if (search == null)
			{
				search = "";
			}

			info = db.exec("select " + tabell + " from users left join personalia on users.login=personalia.login where " +
									field + " like '%" + search + "%';");

			com.getUser().setData("adminListUsers" + s[3], info, false);

		}

		if (info[0] != null)
		{
			com.out(info[tempNr-1]);
		}



	}
	*/



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
				String p1 = com.getp("p1");

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

						if (p1.equals("open")) trav.put(p2+":"+vlan, new Boolean(false) );
						else if (p1.equals("close")) trav.remove(p2);
						else if (p1.equals("expand")) trav.put(p2+":"+vlan, new Boolean(true) );
						com.getUser().setData("traverseList", trav);
					}
				}
				html = "html/ni/visTopologi.html";
			} else
			if (subSect.equals("checkError"))
			{
				html = "html/ni/checkError.html";

			} else
			if (subSect.equals("searchSwport"))
			{
				try
				{
					com.getHandler().handle("ni.searchSwport");
				} catch (PError e)
				{

				}

				html = "html/ni/listSwport.html";
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

			/*
			else
			if (subSect.equals("visUserEdit"))
			{
				if (!com.cap("viewUsers")) { return ""; }

				html = "html/admin/sokuser.htm";
			} else
			if (subSect.equals("visBillettservice"))
			{
				if (!com.cap("viewBillettservice")) { return ""; }

				html = "html/admin/sokbs.htm";
			} else
			if (subSect.equals("visInsertBillettservice"))
			{
				if (!com.cap("insertBillettservice")) { return ""; }

				html = "html/admin/insertbs.htm";
			} else
			if (subSect.equals("insertBillettservice"))
			{
				if (!com.cap("insertBillettservice")) { return ""; }

				try
				{
					com.getHandler().handle("admin.insertBillettservice");
					html = "html/admin/sokbs.htm";
				} catch (PError e)
				{
					if (e.msg().equals("ingenLedigPlasser") )
					{
						com.getUser().set("message", "Det er ingen ledige plasser p&aring; billetten.", false);
						html = "html/pres/main.htm";

					} else
					if (e.msg().equals("billettError") )
					{
						com.getUser().set("message", "Ugyldig billett-nummer", false);
						html = "html/pres/main.htm";
					}
				}
			} else
			if (subSect.equals("listUser"))
			{
				if (!com.cap("viewUsers")) { return ""; }

				html = "html/admin/listusers.htm";
			} else
			if (subSect.equals("presMail"))
			{
				if (!com.cap("presSendMail")) { return ""; }

				html = "html/admin/presmail.htm";
			} else
			if (subSect.equals("presSendMail"))
			{
				if (!com.cap("presSendMail")) { return ""; }

				html = "html/admin/sendpresmail.htm";
			}
			*/




		} else
		{
			html = "html/ni/main.html";
		}

		return html;
	}

	private void link(String s)
	{
		try
		{
			com.getHandler().handle(s);
		} catch (PError e)
		{
			com.outl("Error: " + e.getMessage() );
		}
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

/*
class swRecord
{
	String swid;
	String mp;
	String IfIndex;
	String vlan;
	String portname;
	String status;
	String duplex;
	String speed;
	String porttype;
	String idbak;
	String portBak;

	public swRecord(String Inswid, String Inmp, String InIfIndex, String Invlan, String Inportname, String Instatus, String Induplex, String Inspeed, String Inporttype, String Inidbak, String InportBak)
	{
		swid = Inswid;
		mp = Inmp;
		IfIndex = InIfIndex;
		vlan = Invlan;
		portname = Inportname;
		status = Instatus;
		duplex = Induplex;
		speed = Inspeed;
		porttype = Inporttype;
		idbak = Inidbak;
		portBak = InportBak;
	}

	public String getswid() { return swid; }
	public String getmp() { return mp; }
	public String getIfIndex() { return IfIndex; }
	public String getvlan() { return vlan; }
	public String getportname() { return portname; }
	public String getstatus() { return status; }
	public String getduplex() { return duplex; }
	public String getspeed() { return speed; }
	public String getporttype() { return porttype; }
	public String getidbak() { return idbak; }
	public String getportBak() { return portBak; }

}

class swError implements Comparable
{
	//public static final int

	String table;
	String errType;

	String id;
	String sysName;
	String mp;

	String idBak;
	String nameBak;
	String portBak;

	String desc;
	String level;

	static String defTable;
	static String defErrType;

	static String defSysName;
	static String defMp;

	static String defIdBak;
	static String defNameBak;
	static String defPortBak;

	static String defDesc;
	static String defLevel;


	public swError(String s)
	{
		id = s;

		table = defTable;
		errType = defErrType;

		sysName= defSysName;
		mp = defMp;

		idBak = defIdBak;
		nameBak = defNameBak;
		portBak =defPortBak;

		desc = defDesc;
		level = defLevel;
	}

	public int compareTo(Object o)
	{
		swError e = (swError)o;
		return new Integer(Integer.parseInt(id)).compareTo(new Integer(Integer.parseInt(e.getId())));
	}

	public void setTable(String s) { table = s; }
	public String getTable() { return table; }

	public void setErrType(String s) { errType = s; }
	public String getErrType() { return errType; }

	public String getId() { return id; }

	public void setSysName(String s) { sysName = s; }
	public String getSysName() { return sysName; }

	public void setMp(String s) { mp = s; }
	public String getMp() { return mp; }

	public void setIdBak(String s) { idBak = s; }
	public String getIdBak() { return idBak; }

	public void setNameBak(String s) { nameBak = s; }
	public String getNameBak() { return nameBak; }

	public void setPortBak(String s) { portBak = s; }
	public String getPortBak() { return portBak; }

	public void setDesc(String s) { desc = s; }
	public String getDesc() { return desc; }

	public void setLevel(String s) { level = s;	}

	// static default
	public static void defTable(String s) { defTable = s; }
	public static void defErrType(String s) { defErrType = s; }
	public static void defSysName(String s) { defSysName = s; }
	public static void defMp(String s) { defMp = s; }
	public static void defIdBak(String s) { defIdBak = s; }
	public static void defNameBak(String s) { defNameBak = s; }
	public static void defPortBak(String s) { defPortBak = s; }
	public static void defDesc(String s) { defDesc = s; }
	public static void defLevel(String s) { defLevel = s;	}

	public void reset()
	{
		table = "";
		errType = "";

		sysName = "";
		mp = "";

		idBak = "";
		nameBak = "";
		portBak = "";

		desc = "";
		level = "";
	}


	public String getColor()
	{
		if (errType.equals("Fatal"))
		{
			return "red";
		} else
		if (errType.equals("Error"))
		{
			//return "teal";
			//return "#B45A00";
			return "blue";
		} else
		if (errType.equals("Warning"))
		{
			//return "blue";
			return "teal";
		} else
		if (errType.equals("Notice"))
		{
			return "gray";
		}

		return "black";
	}

	public boolean show()
	{
		int err = 0;
		int lev = 0;

		if (errType.equals("Fatal")) err = 1;
		if (errType.equals("Error")) err = 2;
		if (errType.equals("Warning")) err = 3;
		if (errType.equals("Notice")) err = 4;

		if (level.equals("Fatal")) lev = 1;
		if (level.equals("Error")) lev = 2;
		if (level.equals("Warning")) lev = 3;
		if (level.equals("Notice")) lev = 4;

		if (lev >= err)
		{
			return true;
		}
		return false;
	}



	//public void setErrType(String s) { errType = s; }
	//public String getErrType() { return errType; }


}

*/


























