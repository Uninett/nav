/*
 * HandlerVlanPlot.java
 *
 */

import java.io.*;
import java.util.*;
import java.sql.*;

//import javax.servlet.*;
//import javax.servlet.http.*;

class HandlerNettinfo
{
	public HandlerNettinfo(String[] Is, Com Icom, int InNum, int InTempNr)
	{
		s = Is;
		com = Icom;
		db = com.getDb();
		tempNr = InTempNr;
		num = InNum;
	}

	public String begin() throws PError
	{
		/************************************************************
		* Level 1 handler											*
		* user.*													*
		************************************************************/

		if (s.length >= 2)
		{
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
	private void avledTopologi() throws SQLException
	{
		com.outl("Begin<br>");
		boolean DEBUG_OUT = false;
		String debugParam = com.getp("debug");
		if (debugParam != null && debugParam.equals("yes")) DEBUG_OUT = true;

		Boks.DEBUG_OUT = DEBUG_OUT;

		//fixPrefiks();
		//if (true) return;

		//String[][] data = db.exece("select nettelid,port,idbak,n1.via3,n1.sysName,n2.sysName from swp_nettel,nettel as n1,nettel as n2 where n1.id=nettelid and n2.id=idbak order by via3,n1.id;");
		//String[][] data = db.exece("select nettelid,port,idbak,n1.via3,n1.sysName,n2.sysName from swp_nettel,nettel as n1,nettel as n2 where n1.id=nettelid and n2.id=idbak and (n1.via3=8 or n1.via3=14 or n1.via3=19) order by via3,n1.id,port;");

		//String[][] data = db.exece("select nettelid,port,idbak,n1.via3,n1.sysName,n2.sysName from swp_nettel,nettel as n1,nettel as n2 where n1.id=nettelid and n2.id=idbak order by via3,n1.id,port;");

		//String[][] data = db.exece("");

		//SELECT nettelid,port,idbak,n1.via3,n1.sysName,n2.sysName from swp_nettel,nettel as n1,nettel as n2 where n1.id=nettelid and n2.id=idbak order by via3,n1.id,port

		//SELECT swp_boks.boksid,modul,port,boksbak,gwport.boksid AS via3,b1.sysName,b2.sysName FROM gwport,swp_boks,boks AS b1,boks AS b2 WHERE b1.boksid=swp_boks.boksid AND b2.boksid=boksbak AND b1.prefiksid=gwport.prefiksid AND gwport.hsrppri='1' ORDER BY b1.prefiksid,b1.boksid,modul,port;
		//String[][] data = db.exece("");

		HashMap boksNavn = new HashMap();
		HashMap boksType = new HashMap();
		ResultSet rs = Database.query("SELECT boksid,sysName,typeid FROM boks");
		while (rs.next()) {
			String sysname = rs.getString("sysName"); // Må være med da sysname kan være null !!
			boksNavn.put(new Integer(rs.getInt("boksid")), (sysname==null?"&lt;null&gt;":sysname) );
			boksType.put(new Integer(rs.getInt("boksid")), rs.getString("typeid"));
		}
		Boks.boksNavn = boksNavn;
		Boks.boksType = boksType;

		//SELECT boksid,sysname,typeid,kat FROM boks WHERE NOT EXISTS (SELECT boksid FROM swp_boks WHERE boksid=boks.boksid) AND (kat='KANT' or kat='SW') ORDER BY boksid

		//SELECT swp_boks.boksid,modul,port,boksbak,gwport.boksid AS gwboksid,b1.sysName,b2.sysName FROM gwport,swp_boks,boks AS b1,boks AS b2 WHERE b1.boksid=swp_boks.boksid AND b2.boksid=boksbak AND b1.prefiksid=gwport.prefiksid AND gwport.hsrppri='1' ORDER BY b1.prefiksid,b1.boksid,modul,port

		//SELECT DISTINCT ON (gwboksid) swp_boks.boksid,modul,port,boksbak,gwport.boksid AS gwboksid FROM (swp_boks JOIN boks USING(boksid)) JOIN gwport USING(prefiksid) WHERE gwport.hsrppri='1' ORDER BY gwboksid,boksid,modul,port
		//SELECT swp_boks.boksid,modul,port,boksbak,gwport.boksid AS gwboksid FROM (swp_boks JOIN boks USING(boksid)) JOIN gwport USING(prefiksid) WHERE gwport.hsrppri='1' ORDER BY boksid,modul,port

		//SELECT swp_boks.boksid,modul,port,boksbak,gwport.boksid AS gwboksid FROM ((swp_boks JOIN boks USING(boksid)) JOIN prefiks USING(prefiksid)) JOIN gwport ON rootgw=gwip ORDER BY boksid,modul,port

		HashSet gwUplink = new HashSet();
		rs = Database.query("SELECT DISTINCT ON (boksbak) boksid,boksbak FROM gwport WHERE boksbak IS NOT NULL");
		while (rs.next()) {
			gwUplink.add(rs.getString("boksbak"));
		}

		rs = Database.query("SELECT swp_boks.boksid,kat,modul,port,swp_boks.boksbak,gwport.boksid AS gwboksid FROM ((swp_boks JOIN boks USING(boksid)) JOIN prefiks USING(prefiksid)) JOIN gwport ON rootgwid=gwportid ORDER BY boksid,modul,port");

		HashMap bokser = new HashMap();
		ArrayList boksList = new ArrayList();
		ArrayList l = null;
		HashSet boksidSet = new HashSet();
		HashSet boksbakidSet = new HashSet();

		//int previd = rs.getInt("boksid");
		int previd = 0;
		while (rs.next()) {
			int boksid = rs.getInt("boksid");
			if (boksid != previd) {
				// Ny boks
				l = new ArrayList();
				Boks b = new Boks(com, boksid, rs.getInt("gwboksid"), l, bokser, rs.getString("kat").equals("SW"), !gwUplink.contains(String.valueOf(boksid)) );
				boksList.add(b);
				previd = boksid;
			}
			String[] s = {
				rs.getString("modul"),
				rs.getString("port"),
				rs.getString("boksbak")
			};
			l.add(s);

			boksidSet.add(new Integer(boksid));
			boksbakidSet.add(new Integer(rs.getInt("boksbak")));
		}

		int maxBehindMp=0;
		for (int i=0; i < boksList.size(); i++) {
			Boks b = (Boks)boksList.get(i);
			bokser.put(b.getBoksidI(), b);
			b.init();
			if (b.maxBehindMp() > maxBehindMp) maxBehindMp = b.maxBehindMp();
		}

		// Legg til alle enheter vi bare har funnet i boksbak
		boksbakidSet.removeAll(boksidSet);
		Iterator iter = boksbakidSet.iterator();
		while (iter.hasNext()) {
			Integer boksbakid = (Integer)iter.next();
			Boks b = new Boks(com, boksbakid.intValue(), 0, null, bokser, false, true);
			bokser.put(b.getBoksidI(), b);
			if (DEBUG_OUT) com.outl("Adding boksbak("+b.getBoksid()+"): <b>"+b.getName()+"</b><br>");
		}

		if (DEBUG_OUT) com.outl("Begin processing, maxBehindMp: <b>"+maxBehindMp+"</b><br>");

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
				if (DEBUG_OUT) com.outl("Level: <b>"+level+"</b>, state changed.<br>");
			}
		}
		// Til slutt sjekker vi uplink-portene, dette vil normalt kun gjelde uplink mot -gw
		for (int i=0; i < boksList.size(); i++) {
			Boks b = (Boks)boksList.get(i);
			b.proc_mp(Boks.PROC_UPLINK_LEVEL);
		}

		com.outl("<b>BEGIN REPORT</b><br>");
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
		com.outl("Report done.<br>");

		// Vi trenger en oversikt over hvilket vlan de forskjellige boksene er på
		HashMap boksVlan = new HashMap();
		rs = Database.query("SELECT boksid,vlan FROM boks JOIN prefiks USING (prefiksid) WHERE vlan IS NOT NULL");
		while (rs.next()) {
			boksVlan.put(rs.getString("boksid"), rs.getString("vlan"));
		}

		// Nå går vi gjennom alle portene vi har funnet boksbak for, og oppdaterer tabellen med dette
		int newcnt=0,updcnt=0,remcnt=0;
		ArrayList swport = new ArrayList();
		HashMap swrecMap = new HashMap();
		//rs = Database.query("SELECT swportid,boksid,status,speed,duplex,modul,port,portnavn,boksbak,static,trunk,hexstring FROM swport NATURAL LEFT JOIN swportallowedvlan WHERE status='up' ORDER BY boksid,modul,port");
		rs = Database.query("SELECT swportid,boksid,status,speed,duplex,modul,port,portnavn,boksbak,static,trunk,hexstring FROM swport NATURAL LEFT JOIN swportallowedvlan ORDER BY boksid,modul,port");
		ResultSetMetaData rsmd = rs.getMetaData();
		while (rs.next()) {
			HashMap hm = getHashFromResultSet(rs, rsmd);
			if (!rs.getString("status").toLowerCase().equals("down")) swport.add(hm);
			String key = rs.getString("boksid")+":"+rs.getString("modul")+":"+rs.getString("port");
			swrecMap.put(key, hm);
		}

		com.outl("boksMp listing....<br>");

		iter = boksMp.entrySet().iterator();
		while (iter.hasNext()) {
			Map.Entry me = (Map.Entry)iter.next();
			String key = (String)me.getKey();
			Integer boksbak = (Integer)me.getValue();

			StringTokenizer st = new StringTokenizer(key, ":");
			String boksid = st.nextToken();
			String modul = st.nextToken();
			String port = st.nextToken();

			//com.outl(boksNavn.get(new Integer(boksid)) + " Modul: " + modul + " Port: " + port + " Link: " + boksNavn.get(boksbak) + "<br>");

			if (swrecMap.containsKey(key)) {
				// Record eksisterer fra før, sjekk om oppdatering er nødvendig
				HashMap swrec = (HashMap)swrecMap.get(key);
				//swrecMap.remove(key);
				swrec.put("deleted", null);

				String status = (String)swrec.get("status");
				if (status.toLowerCase().equals("down")) continue;

				String idbak = (String)swrec.get("boksbak");
				if (idbak == null || idbak != null && Integer.parseInt(idbak) != boksbak.intValue()) {
					// Oppdatering nødvendig
					updcnt++;
					// swport
					{
						String[] updateFields = {
							"boksbak", boksbak.toString()
						};
						String[] condFields = {
							"swportid", (String)swrec.get("swportid")
						};
						Database.update("swport", updateFields, condFields);
					}

					String vlan = "non-s";
					if (swrec.get("static").equals("t")) {
						if (swrec.get("trunk").equals("t")) {
							// Mangler enda, men her må vi evt. oppdatere swportallowedvlan
							vlan = "trunk";

						} else {
							// swportvlan
							vlan = (String)boksVlan.get(boksbak.toString());
							if (vlan != null) {
								String[] updateFields = {
									"vlan", vlan,
									"retning", "s"
								};
								String[] condFields = {
									"swportid", (String)swrec.get("swportid")
								};
								Database.update("swportvlan", updateFields, condFields);
							}
						}
					}

					swrec.put("boksbak", boksbak.toString());
					swrec.put("change", "Updated ("+vlan+")");
				}
			} else {
				// Record eksister ikke, og må derfor settes inn

				// Først må vi sjekke om andre siden er en trunk
				String vlan;
				String trunk = "f";
				String allowedVlan = null;
				{
					Boks b = (Boks)bokser.get(boksbak);
					Mp uplinkMp = b.getMpTo(new Integer(boksid));
					if (uplinkMp != null) {
						// Port funnet, men eksisterer denne porten i tabellen fra før?
						String keyBak = boksbak+":"+uplinkMp;
						if (swrecMap.containsKey(keyBak)) {
							// Eksisterer fra før, sjekk om det er en trunk
							HashMap swrecBak = (HashMap)swrecMap.get(keyBak);
							if ("t".equals(swrecBak.get("trunk"))) {
								// Trunk, da må vi også sette inn i swportallowedvlan
								trunk = "t";
								allowedVlan = (String)swrecBak.get("hexstring");
							}
						}
					}

					vlan = (trunk.equals("t")) ? "t" : (String)boksVlan.get(boksbak.toString());

					if (vlan != null) {
						// Vi setter kun inn i swport hvis vi vet vlan eller det er en trunk det er snakk om
						// swport
						String[] insertFields = {
							"boksid", boksid,
							"ifindex", "",
							"status", "up",
							"trunk", trunk,
							"static", "t",
							"modul", modul,
							"port", port,
							"boksbak", boksbak.toString()
						};
						if (!Database.insert("swport", insertFields)) {
							com.outl("<font color=\"red\">Error with insert, boksid=" + boksid + " trunk="+trunk+" modul="+modul+" port="+port+" boksbak="+boksbak+"</font><br>");
						} else {
							if (DEBUG_OUT) com.outl("Inserted row, boksid=" + boksid + " trunk="+trunk+" modul="+modul+" port="+port+" boksbak="+boksbak+"<br>");
							//Database.commit();
							newcnt++;
						}

					}


				}

				// Hvis trunk setter vi inn i swportallowedvlan, ellers rett inn i swportvlan
				if (trunk.equals("t")) {
					// swportallowedvlan
					String sql = "INSERT INTO swportallowedvlan (swportid,hexstring) VALUES ("+
								 "(SELECT swportid FROM swport WHERE boksid='"+boksid+"' AND modul='"+modul+"' AND port='"+port+"' AND boksbak='"+boksbak+"'),"+
								 "'"+allowedVlan+"')";
					Database.update(sql);
					if (DEBUG_OUT) com.outl("swportallowedvlan: "+sql+"<br>");

				} else
				if (vlan != null) {
				// swportvlan
				// Hvilket vlan går over linken? Vi henter vlanet boksbak er på

					// Siden vi ikke vet fremmednøkkelen må vi bruke sub-select her
					String sql = "INSERT INTO swportvlan (swportid,vlan,retning) VALUES ("+
								 "(SELECT swportid FROM swport WHERE boksid='"+boksid+"' AND modul='"+modul+"' AND port='"+port+"' AND boksbak='"+boksbak+"'),"+
								 "'"+vlan+"',"+
								 "'s')";
					Database.update(sql);
					if (DEBUG_OUT) com.outl("swportvlan: "+sql+"<br>");
				}


				// Lag swrec
				HashMap swrec = new HashMap();
				swrec.put("swportid", "N/A");
				swrec.put("boksid", boksid);
				swrec.put("status", "up");
				swrec.put("speed", null);
				swrec.put("duplex", null);
				swrec.put("modul", modul);
				swrec.put("port", port);
				swrec.put("portnavn", null);
				swrec.put("boksbak", boksbak.toString());
				swrec.put("static", "t");
				if (vlan != null) {
					swrec.put("change", "Inserted ("+vlan+")");
				} else {
					swrec.put("change", "Error, vlan is null");
				}

				swport.add(swrec);
				//swrecMap.put(key, swrec);
			}

		}
		com.outl("boksMp listing done.<br>");

		iter = swrecMap.entrySet().iterator();
		while (iter.hasNext()) {
			Map.Entry me = (Map.Entry)iter.next();
			String key = (String)me.getKey();
			HashMap swrec = (HashMap)me.getValue();

			if (!swrec.get("static").equals("t")) continue;
			if (swrec.containsKey("deleted")) continue;

			remcnt++;

			StringTokenizer st = new StringTokenizer(key, ":");
			String boksid = st.nextToken();
			String modul = st.nextToken();
			String port = st.nextToken();

			String swportid = (String)swrec.get("swportid");

			// boksbak_s kan egentlig ikke være null, men for sikkerhets skyld
			String boksbak_s = (String)swrec.get("boksbak");
			Integer boksbak = (boksbak_s == null) ? new Integer(0-1) : new Integer((String)swrec.get("boksbak"));

			Database.update("DELETE FROM swport WHERE swportid='"+swportid+"'");
			if (DEBUG_OUT) com.outl("[DELETED] swportid: <b>"+swportid+"</b> sysName: <b>" + boksNavn.get(new Integer(boksid)) + "</b> Modul: <b>" + modul + "</b> Port: <b>" + port + "</b> Link: <b>" + boksNavn.get(boksbak) + "</b> Static: <b>" + swrec.get("static") + "</b><br>");
		}

		com.outl("<table>");
		com.outl("  <tr>");
		com.outl("    <td><b>swpid</b></td>");
		com.outl("    <td><b>boksid</b></td>");
		com.outl("    <td><b>sysName</b></td>");
		com.outl("    <td><b>typeId</b></td>");
		com.outl("    <td><b>Speed</b></td>");
		com.outl("    <td><b>Duplex</b></td>");
		com.outl("    <td><b>Modul</b></td>");
		com.outl("    <td><b>Port</b></td>");
		com.outl("    <td><b>Portnavn</b></td>");
		com.outl("    <td><b>Boksbak</b></td>");
		com.outl("    <td><b>Change (vlan)</b></td>");
		com.outl("  </tr>");

		int attCnt=0;
		for (int i=0; i < swport.size(); i++) {
			HashMap swrec = (HashMap)swport.get(i);
			String boksid = (String)swrec.get("boksid");
			String modul = (String)swrec.get("modul");
			String port = (String)swrec.get("port");
			String portnavn = (String)swrec.get("portnavn");
			boolean isStatic = swrec.get("static").equals("t");
			String change = (String)swrec.get("change");

			String boksbak = "";
			Integer idbak = (Integer)boksMp.get(boksid+":"+modul+":"+port);
			if (idbak != null) boksbak = (String)boksNavn.get(idbak);

			if (portnavn == null) portnavn = "";

			if (boksbak == null) {
				com.outl("ERROR! boksbak is null for idbak: " + idbak + "<br>");
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

			com.outl("<tr>");
			//com.outl("<td align=right>"+color1+ swrec.get("swportid") + color2+"</td>");
			com.outl("<td align=right><a href=\"#" + swrec.get("swportid") + "\">" + swrec.get("swportid") + "</a></td>");
			com.outl("<td align=right>"+color1+ swrec.get("boksid") + color2+"</td>");
			com.outl("<td>"+color1+ boksNavn.get(new Integer((String)swrec.get("boksid"))) + color2+"</td>");
			com.outl("<td>"+color1+ boksType.get(new Integer((String)swrec.get("boksid"))) + color2+"</td>");
			com.outl("<td align=right>"+color1+ swrec.get("speed") + color2+"</td>");
			com.outl("<td align=right>"+color1+ swrec.get("duplex") + color2+"</td>");
			com.outl("<td align=right>"+color1+ swrec.get("modul") + color2+"</td>");
			com.outl("<td align=right>"+color1+ swrec.get("port") + color2+"</td>");
			com.outl("<td>"+color1+ portnavn + color2+"</td>");
			com.outl("<td>"+color1+ boksbak + color2+"</td>");

			if (change != null) com.outl("<td><b>"+change+"</b></td>");

			com.outl("</tr>");
		}
		com.outl("</table>");
		com.outl("Found <b>" + attCnt + "</b> rows in need of attention.<br>");

		com.outl("<h2>swport:</h2>");
		com.outl("<table>");
		com.outl("  <tr>");
		com.outl("    <td><b>swpid</b></td>");
		com.outl("    <td><b>boksid</b></td>");
		com.outl("    <td><b>sysName</b></td>");
		com.outl("    <td><b>Speed</b></td>");
		com.outl("    <td><b>Duplex</b></td>");
		com.outl("    <td><b>Modul</b></td>");
		com.outl("    <td><b>Port</b></td>");
		com.outl("    <td><b>Portnavn</b></td>");
		com.outl("    <td><b>Boksbak</b></td>");
		com.outl("    <td><b>Change (vlan)</b></td>");
		com.outl("  </tr>");

		for (int i=0; i < swport.size(); i++) {
			HashMap swrec = (HashMap)swport.get(i);
			String boksid = (String)swrec.get("boksid");
			String modul = (String)swrec.get("modul");
			String port = (String)swrec.get("port");
			String portnavn = (String)swrec.get("portnavn");
			boolean isStatic = swrec.get("static").equals("t");
			String change = (String)swrec.get("change");

			String boksbak = "";
			Integer idbak = (Integer)boksMp.get(boksid+":"+modul+":"+port);
			if (idbak != null) boksbak = (String)boksNavn.get(idbak);

			if (portnavn == null) portnavn = "";

			if (boksbak == null) {
				com.outl("ERROR! boksbak is null for idbak: " + idbak + "<br>");
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

			String color1 = "<font color="+color+">";
			String color2 = "</font>";

			com.outl("<tr><a name=\"" + swrec.get("swportid") + "\">");
			com.outl("<td align=right>"+color1+ swrec.get("swportid") + color2+"</td>");
			com.outl("<td align=right>"+color1+ swrec.get("boksid") + color2+"</td>");
			com.outl("<td>"+color1+ boksNavn.get(new Integer((String)swrec.get("boksid"))) + color2+"</td>");
			com.outl("<td align=right>"+color1+ swrec.get("speed") + color2+"</td>");
			com.outl("<td align=right>"+color1+ swrec.get("duplex") + color2+"</td>");
			com.outl("<td align=right>"+color1+ swrec.get("modul") + color2+"</td>");
			com.outl("<td align=right>"+color1+ swrec.get("port") + color2+"</td>");
			com.outl("<td>"+color1+ portnavn + color2+"</td>");
			com.outl("<td>"+color1+ boksbak + color2+"</td>");

			if (change != null) com.outl("<td><b>"+change+"</b></td>");

			com.outl("</tr>");
		}
		com.outl("</table>");

		com.outl("New rows: <b>" + newcnt + "</b> Updated rows: <b>" + updcnt + "</b> Removed rows: <b>"+remcnt+"</b><br>");
		if (newcnt > 0 || updcnt > 0 || remcnt > 0) {
			if (DEBUG_OUT) com.outl("** COMMIT ON DATABASE **<br>");
			Database.commit();
		}
		//Database.rollback();


		com.outl("All done.<br>");

	}

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

	/*
	private void avledVlan() throws SQLException
	{
		com.outl("Begin<br>");
		boolean DB_UPDATE = true;
		boolean DB_COMMIT = true;
		boolean DEBUG_OUT = false;

		String debugParam = com.getp("debug");
		if (debugParam != null && debugParam.equals("yes")) DEBUG_OUT = true;

		// Vi starter med å sette boksbak til null alle steder hvor status='down', slik at vi unngår løkker
		{
			Database.update("UPDATE swport SET boksbak = NULL WHERE status='down' AND boksbak IS NOT NULL");
			Database.commit();
		}

		// Denne er egentlig bare nødvendig for debugging
		HashMap boksName = new HashMap();
		ResultSet rs = Database.query("SELECT boksid,sysname FROM boks");
		while (rs.next()) boksName.put(rs.getString("boksid"), rs.getString("sysname"));

		// Oversikt over hvilke linker:vlan som er blokkert av spanning tree
		HashSet spanTreeBlocked = new HashSet();
		rs = Database.query("SELECT swportid,vlan FROM swportblocked");
		while (rs.next()) spanTreeBlocked.add(rs.getString("swportid")+":"+rs.getString("vlan"));

		// Oversikt over ikke-trunker ut fra hver boks per vlan
		HashMap nontrunkVlan = new HashMap();
		rs = Database.query("SELECT swportid,boksid,boksbak,vlan FROM swport NATURAL JOIN swportvlan WHERE trunk='f' AND boksbak IS NOT NULL");
		while (rs.next()) {
			HashMap nontrunkMap;
			String key = rs.getString("boksid")+":"+rs.getString("vlan");
			if ( (nontrunkMap = (HashMap)nontrunkVlan.get(key)) == null) {
				nontrunkMap = new HashMap();
				nontrunkVlan.put(key, nontrunkMap);
			}
			HashMap hm = new HashMap();
			hm.put("swportid", rs.getString("swportid"));
			hm.put("boksid", rs.getString("boksid"));
			//hm.put("modul", rs.getString("modul"));
			//hm.put("port", rs.getString("port"));
			hm.put("boksbak", rs.getString("boksbak"));
			nontrunkMap.put(rs.getString("boksbak"), hm);
		}

		// Først må vi hente oversikten over hvilke vlan som kan kjøre på de forskjellige portene
		HashMap allowedVlan = new HashMap();
		//ResultSet rs = Database.query("SELECT boksid,modul,port,portnavn,boksbak,substring(hexstring from 250) FROM swport NATURAL JOIN swportallowedvlan WHERE boksbak IS NOT null");
		rs = Database.query("SELECT boksid,swportid,modul,port,boksbak,hexstring FROM swport NATURAL JOIN swportallowedvlan WHERE boksbak IS NOT null");

		while (rs.next()) {
			HashMap boksAllowedMap;
			String boksid = rs.getString("boksid");
			if ( (boksAllowedMap = (HashMap)allowedVlan.get(boksid)) == null) {
				boksAllowedMap = new HashMap();
				allowedVlan.put(boksid, boksAllowedMap);
			}
			HashMap hm = new HashMap();
			hm.put("swportid", rs.getString("swportid"));
			hm.put("boksid", rs.getString("boksid"));
			hm.put("modul", rs.getString("modul"));
			hm.put("port", rs.getString("port"));
			hm.put("boksbak", rs.getString("boksbak"));
			hm.put("hexstring", rs.getString("hexstring"));
			boksAllowedMap.put(rs.getString("boksbak"), hm);
		}

		// Vi trenger å vite hvilke vlan som går ut på ikke-trunk fra en gitt boks
		// Bruker da en HashMap av HashSets
		HashMap activeVlan = new HashMap();
		rs = Database.query("SELECT boksid,vlan FROM swport JOIN swportvlan USING (swportid) WHERE trunk='f' AND status='up'");
		while (rs.next()) {
			HashSet hs;
			String boksid = rs.getString("boksid");
			if ( (hs = (HashSet)activeVlan.get(boksid)) == null) {
				hs = new HashSet();
				activeVlan.put(boksid, hs);
			}
			hs.add(new Integer(rs.getInt("vlan")));
		}

		// Så henter vi ut alle vlan og hvilken switch vlanet "starter på"
		com.outl("<pre>");
		//rs = Database.query("SELECT DISTINCT ON (vlan) vlan,boks.sysname,swport.boksid,portnavn FROM ((prefiks JOIN gwport ON (rootgwid=gwportid)) JOIN boks USING (boksid)) JOIN swport ON (SUBSTRING(portnavn FROM 3)=sysname) WHERE portnavn LIKE 'o:%-gw%' AND vlan IS NOT null ORDER BY vlan");
		//rs = Database.query("SELECT DISTINCT ON (vlan) vlan,sysname,boksbak FROM (prefiks JOIN gwport USING (prefiksid)) JOIN boks USING (boksid) WHERE boksbak IS NOT NULL AND vlan IS NOT NULL ORDER BY vlan");
		rs = Database.query("SELECT DISTINCT ON (vlan) vlan,sysname,gwport.boksbak,swportid,hexstring FROM (prefiks JOIN gwport USING (prefiksid)) JOIN boks USING (boksid) JOIN swport ON (gwport.boksbak=swport.boksid AND swport.boksbak=gwport.boksid) JOIN swportallowedvlan USING (swportid) WHERE gwport.boksbak IS NOT NULL AND vlan IS NOT NULL ORDER BY vlan");
		ArrayList trunkVlan = new ArrayList();
		while (rs.next()) {
			int vlan = rs.getInt("vlan");
			if (DEBUG_OUT) com.outl("\n<b>NEW VLAN: " + vlan + "</b><br>");

			// Først sjekker vi at vlanet har lov til å kjøre
			if (!isAllowedVlan(rs.getString("hexstring"), vlan)) {
				if (DEBUG_OUT) com.outl("\n<b>Vlan is not allowed on trunk down to switch.</b><br>");
				continue;
			}

			if (vlanTraverseLink(vlan, null, rs.getString("boksbak"), true, true, nontrunkVlan, allowedVlan, activeVlan, spanTreeBlocked, trunkVlan, new HashSet(), 0, com, DEBUG_OUT, boksName)) {
				// Dette vlanet går på trunken opp til gw'en
				String[] tvlan = {
					rs.getString("swportid"),
					String.valueOf(vlan),
					"o"
				};
				trunkVlan.add(tvlan);
			}
		}
		// Alle vlan som vi ikke finner startpunkt på, hver må vi rett og slett starte alle andre steder for å være sikker på å få med alt
		// SELECT DISTINCT ON (vlan,boksid) boksid,modul,port,boksbak,vlan,trunk FROM swport NATURAL JOIN swportvlan WHERE vlan NOT IN (SELECT DISTINCT vlan FROM (prefiks JOIN gwport USING (prefiksid)) JOIN boks USING (boksid) WHERE boksbak IS NOT NULL AND vlan IS NOT NULL) AND boksbak IS NOT NULL ORDER BY vlan,boksid
		if (DEBUG_OUT) com.outl("\n<b>VLANs with no router to start from:</b><br>");
		rs = Database.query("SELECT DISTINCT ON (vlan,boksid) vlan,sysname,boksbak FROM swport NATURAL JOIN swportvlan JOIN boks USING (boksid) WHERE vlan NOT IN (SELECT DISTINCT vlan FROM (prefiks JOIN gwport USING (prefiksid)) JOIN boks USING (boksid) WHERE boksbak IS NOT NULL AND vlan IS NOT NULL) AND boksbak IS NOT NULL ORDER BY vlan");
		while (rs.next()) {
			int vlan = rs.getInt("vlan");
			if (DEBUG_OUT) com.outl("\n<b>NEW VLAN: " + vlan + "</b><br>");
			vlanTraverseLink(vlan, null, rs.getString("boksbak"), true, false, nontrunkVlan, allowedVlan, activeVlan, spanTreeBlocked, trunkVlan, new HashSet(), 0, com, DEBUG_OUT, boksName);
		}

		com.outl("</pre>");

		HashMap swportvlan = new HashMap();
		HashMap swportvlanDupe = new HashMap();
		//rs = Database.query("SELECT swportvlanid,swportid,vlan,retning FROM swportvlan JOIN swport USING (swportid) WHERE swport.trunk='t'");
		rs = Database.query("SELECT swportvlanid,swportid,vlan,retning,trunk FROM swportvlan JOIN swport USING (swportid)");
		while (rs.next()) {
			String key = rs.getString("swportid")+":"+rs.getString("vlan");
			swportvlanDupe.put(key, rs.getString("retning") );

			// Kun vlan som går over trunker skal evt. slettes
			if (rs.getBoolean("trunk")) swportvlan.put(key, rs.getString("swportvlanid") );

		}

		com.outl("<br><b>Report:</b> (found "+trunkVlan.size()+" records)<br>");

		HashMap activeOnTrunk = new HashMap(); // Denne brukes for å sjekke swportallowedvlan mot det som faktisk kjører

		int newcnt=0,updcnt=0,dupcnt=0,remcnt=0;
		for (int i=0; i < trunkVlan.size(); i++) {
			String[] s = (String[])trunkVlan.get(i);
			String swportid = s[0];
			String vlan = s[1];
			String retning = s[2];
			String key = swportid+":"+vlan;

			if (swportvlanDupe.containsKey(key)) {
				// Elementet eksisterer i databasen fra før, så vi skal ikke sette det inn
				// Sjekk om vi skal oppdatere
				String dbRetning = (String)swportvlanDupe.get(key);
				if (!dbRetning.equals(retning)) {
					// Oppdatering nødvendig
					String[] updateFields = {
						"retning", retning
					};
					String[] condFields = {
						"swportid", swportid,
						"vlan", vlan
					};
					Database.update("swportvlan", updateFields, condFields);
					com.outl("[UPD] swportid: " + swportid + " vlan: <b>"+ vlan +"</b> Retning: <b>" + retning + "</b> (old: "+dbRetning+")<br>");
					updcnt++;
				} else {
					dupcnt++;
				}
				// Vi skal ikke slette denne recorden nå
				swportvlan.remove(key);


			} else {
				// swportvlan inneholder ikke dette innslaget fra før, så vi må sette det inn
				newcnt++;
				swportvlanDupe.put(key, retning);
				com.outl("[NEW] swportid: " + swportid + " vlan: <b>"+ vlan +"</b> Retning: <b>" + retning + "</b><br>");

				// Sett inn i swportvlan
				String[] fields = {
					"swportid", swportid,
					"vlan", vlan,
					"retning", retning,
				};
				if (DB_UPDATE) Database.insert("swportvlan", fields);
			}

			// Så legger vi til i activeOnTrunk
			//HashMap swrecTrunk;
			HashSet activeVlanOnTrunk;
			if ( (activeVlanOnTrunk = (HashSet)activeOnTrunk.get(swportid)) == null) {
				activeVlanOnTrunk = new HashSet();
				activeOnTrunk.put(swportid, activeVlanOnTrunk);
			}
			activeVlanOnTrunk.add(vlan);
		}

		// Nå kan vi gå gjennom swportvlan og slette de innslagene som ikke lenger eksisterer
		Iterator iter = swportvlan.entrySet().iterator();
		while (iter.hasNext()) {
			remcnt++;
			Map.Entry me = (Map.Entry)iter.next();
			String key = (String)me.getKey();
			String swportvlanid = (String)me.getValue();

			StringTokenizer st = new StringTokenizer(key, ":");
			String swportid = st.nextToken();
			String vlan = st.nextToken();

			com.outl("[REM] swportid: " + swportid + " vlan: <b>"+ vlan +"</b> ("+swportvlanid+")<br>");
			if (DB_UPDATE) Database.update("DELETE FROM swportvlan WHERE swportvlanid = '"+swportvlanid+"'");
		}

		if (newcnt > 0 || updcnt > 0 || remcnt > 0) if (DB_COMMIT) Database.commit();
		com.outl("New count: <b>"+newcnt+"</b>, Update count: <b>"+updcnt+"</b> Dup count: <b>"+dupcnt+"</b>, Rem count: <b>"+remcnt+"</b><br>");

		if (!DB_COMMIT) Database.rollback();

		// Så skriver vi ut en rapport om mismatch mellom swportallowedvlan og det som faktisk kjører
		com.outl("<h2>Allowed VLANs that are not active:</h2>");
		com.outl("<h4>(<i><b>Note</b>: VLANs 1 and 1000-1005 are for interswitch control traffic and is always allowed</i>)</h4>");
		int allowedcnt=0, totcnt=0;
		iter = allowedVlan.values().iterator();
		while (iter.hasNext()) {
			HashMap boksAllowedMap = (HashMap)iter.next();
			Iterator iter2 = boksAllowedMap.values().iterator();
			while (iter2.hasNext()) {
				HashMap hm = (HashMap)iter2.next();
				String swportid = (String)hm.get("swportid");
				String hexstring = (String)hm.get("hexstring");

				HashSet activeVlanOnTrunk = (HashSet)activeOnTrunk.get(swportid);
				if (activeVlanOnTrunk == null) {
					//com.outl("ERROR, swrecTrunk is missing for swportid: " + swportid + "<br>");
					continue;
				}
				totcnt++;

				String boksid = (String)hm.get("boksid");
				String modul = (String)hm.get("modul");
				String port = (String)hm.get("port");
				String boksbak = (String)hm.get("boksbak");
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
								com.outl("Working with trunk From("+boksid+"): <b>"+boksName.get(boksid)+"</b>, Modul: <b>"+modul+"</b> Port: <b>"+port+"</b> To("+boksbak+"): <b>"+boksName.get(boksbak)+"</b><br>");
								// Skriv ut aktive vlan
								com.out("&nbsp;&nbsp;Active VLANs: <b>");
								Iterator vlanIter = activeVlanOnTrunk.iterator();
								int[] vlanA = new int[activeVlanOnTrunk.size()];
								int vlanAi=0;
								while (vlanIter.hasNext()) vlanA[vlanAi++] = Integer.parseInt((String)vlanIter.next());
								Arrays.sort(vlanA);
								boolean first=true;
								for (vlanAi=0; vlanAi < vlanA.length; vlanAi++) {
									if (!first) com.out(", "); else first=false;
									com.out(String.valueOf(vlanA[vlanAi]));
								}
								com.outl("</b><br>");
								//com.outl("&nbsp;&nbsp;The following VLANs are allowed on the trunk, but does not seem to be active:<br>");
								printMsg = true;
								com.out("&nbsp;&nbsp;Excessive VLANs: <b>"+range+"</b>");
							} else {
								com.out(", <b>"+range+"</b>");
							}
							markLast=false;
						}
						//startRange=i+1;
					}
				}
				if (printMsg) com.outl("<br><br>");
			}
		}

		com.outl("A total of <b>"+allowedcnt+"</b> / <b>"+totcnt+"</b> have allowed VLANs that are not active.<br>");
		com.outl("All done.<br>");
	}

	private boolean vlanTraverseLink(int vlan, String fromid, String boksid, boolean cameFromTrunk, boolean setDirection, HashMap nontrunkVlan, HashMap allowedVlan, HashMap activeVlan, HashSet spanTreeBlocked, ArrayList trunkVlan, HashSet visitNode, int level, Com com, boolean DEBUG_OUT, HashMap boksName)
	{
		if (level > 40) {
			com.outl("<font color=\"red\">ERROR! Level is way too big...</font>");
			return false;
		}
		String pad = "";
		for (int i=0; i<level; i++) pad+="        ";

		if (DEBUG_OUT) com.outl(pad+"><font color=\"green\">[ENTER]</font> Now at node("+boksid+"): <b>" + boksName.get(boksid) + "</b>, came from("+fromid+"): " + boksName.get(fromid) + ", vlan: " + vlan + " cameFromTrunk: <b>"+cameFromTrunk+"</b> level: <b>" + level + "</b>");

		if (visitNode.contains(boksid)) {
			if (DEBUG_OUT) com.outl(pad+"><font color=\"red\">[RETURN]</font> NOTICE: Found loop, from("+fromid+"): " + boksName.get(fromid) + ", boksid("+boksid+"): " + boksName.get(boksid) + ", vlan: " + vlan + ", level: " + level + "");
			return false;
		}

		// Vi vet nå at dette vlanet kjører på denne boksen, det første vi gjør da er å traversere videre
		// på alle ikke-trunker og markerer retningen
		if (nontrunkVlan.containsKey(boksid+":"+vlan)) {
			String key = boksid+":"+vlan;
			HashMap nontrunkMap = (HashMap)nontrunkVlan.get(key);

			Iterator iter = nontrunkMap.values().iterator();
			while (iter.hasNext()) {
				HashMap hm = (HashMap)iter.next();
				String toid = (String)hm.get("boksbak");
				String swportid = (String)hm.get("swportid");
				String swportidBack;

				// Linken tilbake skal vi ikke følge uansett
				if (toid.equals(fromid)) continue;

				// Vi kan nå legge til at retningen skal være ned her ihvertfall
				String[] rVlan = {
					swportid,
					String.valueOf(vlan),
					(setDirection)?"n":"u"
				};
				trunkVlan.add(rVlan);

				if (DEBUG_OUT) com.outl(pad+"--><b>[NON-TRUNK]</b> Running on non-trunk, vlan: <b>" + vlan + "</b>, boksid("+boksid+"): <b>" + boksName.get(boksid) + "</b>, to("+toid+"): <b>" + boksName.get(toid) + "</b> level: <b>" + level + "</b> (<b>"+rVlan[0]+"</b>)");

				// Så traverserer vi linken, return-verdien her er uten betydning
				vlanTraverseLink(vlan, boksid, toid, false, setDirection, nontrunkVlan, allowedVlan, activeVlan, spanTreeBlocked, trunkVlan, visitNode, level+1, com, DEBUG_OUT, boksName);

				// Så sjekker vi om vi finner linken tilbake, i så tilfellet skal den markeres med retning 'o'
				String keyBack = toid+":"+vlan;
				HashMap nontrunkMapBack = (HashMap)nontrunkVlan.get(keyBack);
				if (nontrunkMapBack == null) {
					// Boksen vi ser på har ingen non-trunk linker, og vi kan derfor gå videre
					if (DEBUG_OUT) com.outl(pad+"---->ERROR! No non-trunk links found for vlan: " + vlan + ", toid("+toid+"): " + boksName.get(toid) + ", level: " + level + "");
					continue;
				}

				HashMap hmBack = (HashMap)nontrunkMapBack.get(boksid);
				if (hmBack == null) {
					// Linken tilbake mangler
					if (DEBUG_OUT) com.outl(pad+"---->ERROR! Link back not found for vlan: " + vlan + ", toid("+toid+"): " + boksName.get(toid) + ", level: " + level + "");
					continue;
				}

				swportidBack = (String)hmBack.get("swportid");
				// Nå kan vi markere at vlanet kjører også på linken tilbake
				String[] rVlanBack = {
					swportidBack,
					String.valueOf(vlan),
					(setDirection)?"o":"u"
				};
				trunkVlan.add(rVlanBack);
				if (DEBUG_OUT) com.outl(pad+"--><b>[NON-TRUNK]</b> Link back running on non-trunk OK (<b>"+rVlanBack[0]+"</b>)");
			}
		}

		// OK, vi kom fra en trunk, sjekk om det er andre trunker vlanet vi er på har lov til å kjøre på
		HashMap boksAllowedMap = (HashMap)allowedVlan.get(boksid);
		if (boksAllowedMap == null) {
			if (cameFromTrunk) {
				if (fromid == null) {
					// Dette er første enhet, og da kan dette faktisk skje
					if (DEBUG_OUT) com.outl(pad+">ERROR! AllowedVlan not found for vlan: " + vlan + ", boksid("+boksid+"): " + boksName.get(boksid) + ", level: " + level + "");
				} else {
					if (DEBUG_OUT) com.outl(pad+"><font color=\"red\">ERROR! Should not happen, AllowedVlan not found for vlan: " + vlan + ", boksid("+boksid+"): " + boksName.get(boksid) + ", level: " + level + "</font>");
				}
			}
			if (DEBUG_OUT) com.outl(pad+"><font color=\"red\">[RETURN]</font> from node("+boksid+"): " + boksName.get(boksid) + "");
			return false;
		}
		boolean isActiveVlan = false;
		Iterator iter = boksAllowedMap.values().iterator();
		while (iter.hasNext()) {
			//HashMap hm = (HashMap)l.get(i);
			HashMap hm = (HashMap)iter.next();
			String hexstr = (String)hm.get("hexstring");
			String toid = (String)hm.get("boksbak");
			String swportid = (String)hm.get("swportid");
			String swportidBack;

			// Linken tilbake skal vi ikke følge uansett
			if (toid.equals(fromid)) continue;

			// Så trenger vi recorden for linken tilbake
			{
				HashMap boksAllowedMapBack = (HashMap)allowedVlan.get(toid);
				if (boksAllowedMapBack == null) {
					if (DEBUG_OUT) com.outl(pad+">ERROR! AllowedVlan not found for vlan: " + vlan + ", toid("+toid+"): " + boksName.get(toid) + ", level: " + level + "");
					continue;
				}
				HashMap hmBack = (HashMap)boksAllowedMapBack.get(boksid);
				swportidBack = (String)hmBack.get("swportid");

				String hexstrBack = (String)hmBack.get("hexstring");
				// Hvis en av dem ikke tillater dette vlanet å kjøre følger vi ikke denne linken
				if (!isAllowedVlan(hexstr, vlan) || !isAllowedVlan(hexstrBack, vlan)) {
					if (DEBUG_OUT) com.outl(pad+"----><b>NOT</b> allowed to("+toid+"): " + boksName.get(toid) + "");
					continue;
				}

			}

			if (DEBUG_OUT) com.outl(pad+"----><b>Allowed</b> to("+toid+"): " + boksName.get(toid) + ", visiting...");

			// Sjekk om linken er blokkert av spanning tree
			if (spanTreeBlocked.contains(swportid+":"+vlan) || spanTreeBlocked.contains(swportidBack+":"+vlan)) {
				// Jepp, da legger vi til vlanet med blokking i begge ender
				String[] tvlan = {
					swportid,
					String.valueOf(vlan),
					"b"
				};
				String[] tvlanBack = {
					swportidBack,
					String.valueOf(vlan),
					"b"
				};
				trunkVlan.add(tvlan);
				trunkVlan.add(tvlanBack);
				isActiveVlan = true;
				if (DEBUG_OUT) com.outl(pad+"------><font color=\"purple\">Link blocked by spanning tree, boksid("+boksid+"): <b>"+boksName.get(boksid)+"</b> toid:("+toid+"): <b>"+ boksName.get(toid) + "</b>, vlan: <b>" + vlan + "</b>, level: <b>" + level + "</b></font>");
				continue;
			}


			//if (DEBUG_OUT) com.outl(pad+"---->Visiting("+toid+"): " + boksName.get(toid) + "");

			// Brukes for å unngå dupes
			visitNode.add(boksid);

			if (vlanTraverseLink(vlan, boksid, toid, true, setDirection, nontrunkVlan, allowedVlan, activeVlan, spanTreeBlocked, trunkVlan, visitNode, level+1, com, DEBUG_OUT, boksName)) {
				// Vi vet nå at vlanet kjører på denne trunken
				String[] tvlan = {
					swportid,
					String.valueOf(vlan),
					(setDirection)?"n":"u"
				};
				String[] tvlanBack = {
					swportidBack,
					String.valueOf(vlan),
					(setDirection)?"o":"u"
				};
				trunkVlan.add(tvlan);
				trunkVlan.add(tvlanBack);
				isActiveVlan = true;
				if (DEBUG_OUT) com.outl(pad+"---->Returned active on trunk, vlan: <b>" + vlan + "</b>, boksid("+boksid+"): <b>" + boksName.get(boksid) + "</b>, to("+toid+"): <b>" + boksName.get(toid) + "</b> level: <b>" + level + "</b> (<b>"+tvlan[0]+" / "+tvlanBack[0]+"</b>)");
			} else {
				if (DEBUG_OUT) com.outl(pad+"---->Returned NOT active on trunk, vlan: <b>" + vlan + "</b>, boksid("+boksid+"): <b>" + boksName.get(boksid) + "</b>, to("+toid+"): <b>" + boksName.get(toid) + "</b> level: <b>" + level + "</b>");
			}
			visitNode.remove(boksid);


		}


		// Vi skal returnere om vlanet kjører på denne boksen
		// Først sjekker vi om noen av trunkene har dette vlanet aktivt
		if (isActiveVlan) {
			if (DEBUG_OUT) com.outl(pad+"><font color=\"red\">[RETURN]</font> from node("+boksid+"): " + boksName.get(boksid) + ", <b>ActiveVlan on trunk</b>");
			return true;
		}

		// Nei, da sjekker vi om det er noen ikke-trunker som har det aktivt, det er gitt i activeVlan
		HashSet hs = (HashSet)activeVlan.get(boksid);
		if (hs != null && hs.contains(new Integer(vlan)) ) {
			if (DEBUG_OUT) com.outl(pad+"><font color=\"red\">[RETURN]</font> from node("+boksid+"): " + boksName.get(boksid) + ", <b>ActiveVlan on NON-trunk</b>");
			return true;
		}
		if (DEBUG_OUT) com.outl(pad+"><font color=\"red\">[RETURN]</font> from node("+boksid+"): " + boksName.get(boksid) + ", <b>Not active</b>");
		return false;
	}

	private static boolean isAllowedVlan(String hexstr, int vlan)
	{
		if (hexstr.length() == 256) {
			return isAllowedVlanFwd(hexstr, vlan);
		}
		return isAllowedVlanRev(hexstr, vlan);
	}

	private static boolean isAllowedVlanFwd(String hexstr, int vlan)
	{
		if (vlan < 0 || vlan > 1023) return false;
		int index = vlan / 4;

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
	*/



	/*
	private void avledTopologi2()
	{
		com.outl("Begin<br>");

		//String[][] data = db.exece("select nettelid,port,idbak,n1.via3,n1.sysName,n2.sysName from swp_nettel,nettel as n1,nettel as n2 where n1.id=nettelid and n2.id=idbak order by via3,n1.id;");
		//String[][] data = db.exece("select nettelid,port,idbak,n1.via3,n1.sysName,n2.sysName from swp_nettel,nettel as n1,nettel as n2 where n1.id=nettelid and n2.id=idbak and (n1.via3=8 or n1.via3=14 or n1.via3=19) order by via3,n1.id,port;");

		//String[][] data = db.exece("select nettelid,port,idbak,n1.via3,n1.sysName,n2.sysName from swp_nettel,nettel as n1,nettel as n2 where n1.id=nettelid and n2.id=idbak order by via3,n1.id,port;");

		//String[][] data = db.exece("");

		//SELECT nettelid,port,idbak,n1.via3,n1.sysName,n2.sysName from swp_nettel,nettel as n1,nettel as n2 where n1.id=nettelid and n2.id=idbak order by via3,n1.id,port

		//SELECT swp_boks.boksid,modul,port,boksbak,gwport.boksid AS via3,b1.sysName,b2.sysName FROM gwport,swp_boks,boks AS b1,boks AS b2 WHERE b1.boksid=swp_boks.boksid AND b2.boksid=boksbak AND b1.prefiksid=gwport.prefiksid AND gwport.hsrppri='1' ORDER BY b1.prefiksid,b1.boksid,modul,port;
		String[][] data = db.exece("SELECT swp_boks.boksid,modul,port,boksbak,gwport.boksid AS via3,b1.sysName,b2.sysName FROM gwport,swp_boks,boks AS b1,boks AS b2 WHERE b1.boksid=swp_boks.boksid AND b2.boksid=boksbak AND b1.prefiksid=gwport.prefiksid AND gwport.hsrppri='1' ORDER BY b1.prefiksid,b1.boksid,modul,port");




		String[] nettelid = data[0];
		String[] port = data[1];
		String[] idbak = data[2];
		String[] via3 = data[3];
		String[] name = data[4];
		String[] namebak = data[5];

		HashMap nettelNavn = new HashMap();
		HashMap nettelType = new HashMap();
		data = db.exece("SELECT boksid,sysName,typeid FROM boks");
		for (int i=0; i < data[0].length; i++) {
			nettelNavn.put(new Integer(Integer.parseInt(data[0][i])), data[1][i]);
			nettelType.put(new Integer(Integer.parseInt(data[0][i])), data[2][i]);
		}
		Nettel.nettelNavn=nettelNavn;
		Nettel.nettelType=nettelType;


		//HashMap nettelNavn = new HashMap();
		//for (int i=0; i < nettelid.length; i++) nettelNavn.put(new Integer(Integer.parseInt(nettelid[i])), name[i]);
		//Nettel.nettelNavn=nettelNavn;

		//String lastVia3 = via3[0];
		int begin = 0;
		for (int k = 0; k < via3.length; k++)
		{
			ArrayList l = new ArrayList();
			HashMap hm = new HashMap();

			do
			{
				k++;
				while (k<nettelid.length && nettelid[k-1].equals(nettelid[k])) k++;


				Nettel n = new Nettel(com, nettelid[k-1], port, idbak, via3[k-1], begin, k, hm);
				l.add(n);
				hm.put(new Integer(n.getId()), n);

				//com.outl("Add: " + nettelid[k-1] + " last port: " + port[k-1] + " b: " + begin + " e: " + k + "<br>");


				begin=k;


			//}  while (k<via3.length && via3[k-1].equals(via3[k]));
			}  while (k<via3.length);

			// Ferdig med denne ruteren
			com.outl("=Ruter done, last: " + nettelid[k-1] + " end: " + k + "<br>");
			com.outl("Begin processing...<br>");

			boolean notDone=true;
			boolean[] nDone = new boolean[l.size()];
			for (int i=1; notDone; i++) {
				notDone=false;
				com.outl("<b>Working on level: " + i + "</b><br>");
				for (int j=0; j < l.size(); j++) {
					if (nDone[j]) continue;
					Nettel n = (Nettel)l.get(j);
					com.outl("-->Nettel: <b>" + n.getName() + "</b> ("+nettelType.get(n.getIdInt())+")<br>");
					nDone[j] = n.processLevel(i);
					if (!nDone[j]) notDone=true;
					//if (!) notDone=true;
				}

			}

			com.outl("Processing complete:<br>");

			for (int i=0; i < l.size(); i++) {
				Nettel n = (Nettel)l.get(i);
				String[] uplink = n.getUplink();
				com.outl("-->Nettel(" + n.getId() + "): <b>" + n + "</b> Type: <b>" + nettelType.get(n.getIdInt()) + "</b> Uplinkport: <b>" + uplink[1] + "</b> Navn(" + uplink[0] + "): <b>" + uplink[2] + "</b> Type: <b>" + uplink[3] + "</b><br>");
				String[][] downlinks = n.getFormatedDownlinks();
				for (int j=0; j < downlinks.length; j++) {
					String dlId = downlinks[j][0];
					String dlPort = downlinks[j][1];
					String dlName = downlinks[j][2];
					String dlType = downlinks[j][3];

					com.outl("---->Port: <b>"+dlPort+"</b> Navn(" + dlId + "): <b>" + dlName + "</b> Type: <b>" + dlType + "</b><br>");
				}
			}

			// Sjekk mot swport-tabell
			int[] keys = { 0,1,2 };
			HashMap swport = db.exech(keys, "SELECT swid,mp,idbak,portname FROM swport");
			com.outl("Report for comparison with swport:<br>");

			com.outl("<table>");
			com.outl(" <tr>");
			com.outl("  <td><b>swid</b></td>");
			com.outl("  <td><b>swName</b></td>");
			com.outl("  <td><b>mp</b></td>");
			com.outl("  <td><b>portname</b></td>");
			com.outl("  <td><b>idbak</b></td>");
			com.outl("  <td><b>namebak</b></td>");
			com.outl("  <td><b>Type</b></td>");
			com.outl("  <td><b>Description</b></td>");
			com.outl("  <td><b>Fixed</b></td>");
			com.outl(" </tr>");

			com.outl(" <tr><td colspan=50><b>Uplinks:</b></td></tr>");
			for (int i=0; i < l.size(); i++) {
				Nettel n = (Nettel)l.get(i);
				String nid = ""+n.getId();
				String nnavn = (String)nettelNavn.get(n.getIdInt());

				String portname = "";
				String type = "";
				String desc = "";
				boolean fix = false;

				// Sjekk at uplink er riktig
				String[] uplink = n.getUplink();
				String ulId = uplink[0];
				String ulPort = uplink[1];
				String ulName = uplink[2];
				if (ulId != null) {
					String[] s = (String[])swport.get(nid+ulPort+ulId);
					if (s != null) {
						// Sjekk om den er riktig markert som uplink
						if (!s[3].startsWith("o")) {
							//com.outl(nnavn + "("+nid+") has uplink port (<b>" + ulPort + "</b>) <b>incorrectly</b> marked: " + s[3] + "<br>");
							type = "<font color=teal>Incorrect marking";
							desc = "Link is not marked as uplink (o:)";
						}

					} else {
						s = (String[])swport.get(nid+ulId);
						if (s != null) {
							//com.outl(nnavn + "("+nid+") has an <b>empty</b> mp for uplink port, should be: <b>" + ulPort + "</b><br>");
							type = "<font color=\"#800080\">Empty mp";
							desc = "Link has an empty mp";
						} else {
							//com.outl(nnavn + "("+nid+") is <b>missing</b> uplink port (<b>" + ulPort + "</b>), to: " + ulName +"("+ulId+")<br>");
							type = "<font color=blue>Missing link";
							desc = "Link information is missing";
						}
					}
					if (s != null) portname = s[3];
				}

				if (type.length() > 0) {
					com.outl(" <tr>");
					com.outl("  <td>"+nid+"</td>");
					com.outl("  <td><b>"+nnavn+"</b></td>");
					com.outl("  <td>"+ulPort+"</td>");
					com.outl("  <td>"+portname+"</td>");
					com.outl("  <td>"+ulId+"</td>");
					com.outl("  <td>"+ulName+"</td>");
					//com.outl("  <td><font color=blue>"+type+"</font></td>");
					com.outl("  <td>"+type+"</font></td>");
					com.outl("  <td><i>"+desc+"</i></td>");
					String fixed = (fix) ? "<font color=green>Yes</font>" : "<font color=red>No</font>";
					com.outl("  <td>"+fixed+"</td>");
					com.outl(" </tr>");
				}

			}

			com.outl(" <br><tr><td colspan=50><b>Other links</b>:</td></tr>");
			for (int i=0; i < l.size(); i++) {
				Nettel n = (Nettel)l.get(i);
				String nid = ""+n.getId();
				String nnavn = (String)nettelNavn.get(n.getIdInt());

				String[][] downlinks = n.getFormatedDownlinks();
				for (int j=0; j < downlinks.length; j++) {
					String dlId = downlinks[j][0];
					String dlPort = downlinks[j][1];
					String dlName = downlinks[j][2];
					String dlType = downlinks[j][3];

					String portname = "";
					String type = "";
					String desc = "";
					boolean fix = false;

					String[] s = (String[])swport.get(nid+dlPort+dlId);
					if (s != null) {
						portname = s[3];
						// Sjekk om den er riktig markert som downlink
						if (!s[3].startsWith("n")) {
							//com.outl(nnavn + "("+nid+") has downlink on port (<b>" + dlPort + "</b>) <b>incorrectly</b> marked: " + s[3] + "<br>");
							type = "<font color=teal>Incorrect marking";
							desc = "Link is not marked as downlink (n:)";
						}

					} else {
						//com.outl(nnavn + "("+nid+") is <b>missing</b> downlink on port (<b>" + dlPort + "</b>), to: " + dlName +"("+dlId+")<br>");

						type = "<font color=blue>Missing link";
						desc = "Link information is missing";
					}

					if (type.length() > 0) {
						com.outl(" <tr>");
						com.outl("  <td>"+nid+"</td>");
						com.outl("  <td><b>"+nnavn+"</b></td>");
						com.outl("  <td>"+dlPort+"</td>");
						com.outl("  <td>"+portname+"</td>");
						com.outl("  <td>"+dlId+"</td>");
						com.outl("  <td>"+dlName+"</td>");
						//com.outl("  <td><font color=blue>"+type+"</font></td>");
						com.outl("  <td>"+type+"</font></td>");
						com.outl("  <td><i>"+desc+"</i></td>");
						String fixed = (fix) ? "<font color=green>Yes</font>" : "<font color=red>No</font>";
						com.outl("  <td>"+fixed+"</td>");
						com.outl(" </tr>");
					}


				}
			}

			com.outl("</table>");





			//com.outl("Next ruter.<br>");
		}

		com.outl("All done.<br>");




	}
	*/


	private void updateMac()
	{
		com.outl("Starter updateMac...<br>");

		//INSERT INTO boksMac (boksid,mac) VALUES
		//SELECT boks.boksid,mac FROM arp,boks,gwport WHERE arp.ip IN (boks.ip,gwip)
		/*
		select boksid,arp.ip,mac,sysname,boks.ip from arp join boks using (boksid);

		SELECT DISTINCT ON (boksid) boks.boksid,sysName,kat,typeid,mac FROM boks LEFT JOIN arp USING (ip) WHERE mac IS NULL;
		SELECT gwport.boksid,sysName,gwip,kat,typeid,mac FROM (gwport LEFT JOIN arp ON arp.ip=gwport.gwip) JOIN boks ON gwport.boksid=boks.boksid ORDER BY gwport.boksid;

		129.241.76.164

		129.241.076.165
		255.255.255.252





		SELECT DISTINCT ON (mac) boks.boksid,mac FROM arp JOIN boks USING (ip)

		SELECT DISTINCT ON (mac) gwport.boksid,mac FROM arp,gwport WHERE arp.ip=gwport.gwip


		CREATE VIEW boksmac AS SELECT DISTINCT ON (mac) boks.boksid,mac FROM arp JOIN boks USING (ip) UNION SELECT DISTINCT ON (mac) gwport.boksid,mac FROM arp,gwport WHERE arp.ip=gwport.gwip
		*/

		//SELECT arp.ip,mac FROM arp,boks,gwport WHERE arp.ip = (boks.ip OR gwip)


		com.outl("<br><b>Oppdaterer switch/hub/annet...</b><br>");
		String[][] data = db.exece("SELECT nettel.id,arp.mac,sysName FROM nettel,arp WHERE nettel.ip=arp.ip GROUP BY mac");
		if (data[0][0] != null)
			for (int i = 0; i < data[0].length; i++)
			{
				com.outl("Oppdaterer: (" + data[0][i] + ") " + data[2][i] + " MAC: " + data[1][i] + "<br>");
				db.exec("INSERT INTO nettelMac (id,nettelid,mac) VALUES (null,'" + data[0][i] +"','" + data[1][i] + "')");
			}

		com.outl("<br><b>Oppdaterer rutere...</b><br>");
		data = db.exece("SELECT ruter,arp.mac,sysName FROM subnet,arp,nettel WHERE gwip=arp.ip AND ruter=nettel.id GROUP BY mac");
		if (data[0][0] != null)
			for (int i = 0; i < data[0].length; i++)
			{
				com.outl("Oppdaterer: (" + data[0][i] + ") " + data[2][i] + " MAC: " + data[1][i] + "<br>");
				db.exec("INSERT INTO nettelMac (id,nettelid,mac) VALUES (null,'" + data[0][i] +"','" + data[1][i] + "')");
			}

		/*
		com.outl("<br><b>Oppdaterer switch/hub/annet...</b><br>");
		String[][] data = db.exece("select nettel.id,arp.mac,sysName from nettel,arp where nettel.ip=arp.ip and arp.mac!=nettel.mac group by mac");
		if (data[0][0] != null)
			for (int i = 0; i < data[0].length; i++)
			{
				com.outl("Oppdaterer: (" + data[0][i] + ")" + data[2][i] + " MAC: " + data[1][i] + "<br>");
				db.exec("update nettel set mac='" + data[1][i] + "' where id='" + data[0][i] + "'");
			}

		com.outl("<br><b>Oppdaterer rutere...</b><br>");
		data = db.exece("select ruter,arp.mac,sysName from subnet,arp,nettel where gwip=arp.ip and ruter=nettel.id and arp.mac!=nettel.mac group by ruter");
		if (data[0][0] != null)
			for (int i = 0; i < data[0].length; i++)
			{
				com.outl("Oppdaterer: (" + data[0][i] + ")" + data[2][i] + " MAC: " + data[1][i] + "<br>");
				db.exec("update nettel set mac='" + data[1][i] + "' where id='" + data[0][i] + "'");
			}
		*/

		/*
		select sysName,kat,nettel.ip,arp.mac,router from nettel,arp where nettel.ip=arp.ip and arp.mac!=nettel.mac group by mac;
		select ruter,gwip,org,subnet.kat,arp.mac,router from subnet,arp,nettel where gwip=arp.ip and ruter=nettel.id and arp.mac!=nettel.mac group by ruter,arp.mac;

		select ruter,arp.mac,sysName from subnet,arp,nettel where gwip=arp.ip and ruter=nettel.id and arp.mac!=nettel.mac group by ruter,arp.mac;
		*/

		com.outl("All done.<br>");


	}

	/* [/ni.checkError]
	 * Finner feil i swport/subnet
	 */
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

	/* [/ni.makeTree]
	 * Lager tre-struktur i swport
	 */
	private void makeTree()
	{
		/*
		// Hent alle ruter-MAC
		select nettel.id,sysName,via3,mac from nettel,subnet,arp where nettel.kat='HUB' and via3=subnet.ruter and gwip=arp.ip group by nettel.id;

		// Hent alle relevante MAC
		select * from cam group by mac;



		006097AF1D45
		select mac from cam limit 500000,1;
		*/


		// Hent ruter-MAC for alle HUBer
		com.outl("Henter ruter-MAC for alle HUBer...");
		String[][] rmac = db.exece("select nettel.id,sysName,via3,mac from nettel,subnet,arp where nettel.kat='HUB' and via3=subnet.ruter and gwip=arp.ip group by nettel.id;");
		com.outl("done.<br>");

		// Henter portnummer for alle MAC
		com.outl("Henter portnummer for alle MAC...");
		String[][] data = db.exece("select hub,up,mac from cam group by mac;");
		com.outl("done.<br>");























	}

	/* [/ni.updatePortBak]
	 * Oppdaterer portBak-feltet
	 */

	private void updatePortBak()
	{
		// oppdater portBak-feltet for alle enheter ved å se på mp-feltet
		/*
		{
			String[][] data = db.exece("select swport.id,swid,idbak,mp,portBak,portname,status,sysName from swport,nettel where swid=nettel.id and idbak!='0';");
			String[] id = data[0];
			String[] swid = data[1];
			String[] idbak = data[2];
			String[] mp = data[3];
			String[] portBak = data[4];
			String[] portname = data[5];
			String[] status = data[6];
			String[] sysName = data[7];

			for (int i = 0; i < swid.length; i++)
			{
				// konstruer motsatt portname
				String portnameBak;
				String[] type = misc.tokenize(portname[i], ":");
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
				portnameBak += ":" + sysName[i];

				String[] info = db.exec("select mp from swport where swid='" + idbak[i] + "' and idbak='" + swid[i] + "' and portname='" + portnameBak + "' and status='" + status[i] + "';");
				if (info[0] != null)
				{
					if (info[0].equals(portBak[i]))
					{
						// no change
					} else
					{
						// need update
						db.exec("update swport set portBak='" + info[0] + "' where id='" + id[i] + "';");
						com.outl("Updating " + sysName[i] + " (swid: " + swid[i] + "), idbak: " + idbak[i] + ", setting portBak: " + info[0] + ", old: " + portBak[i] + "<br>");
					}
				} else
				{

					// sjekk om det er link til gw
					type = misc.tokenizel(portname[i], "-");
					if (type.length > 1 && type[1].charAt(0) == 'g')
					{
						//link til gw
					} else
					{
						com.outl("Error, missing link for " + sysName[i] + " (swid: " + swid[i] + ") and idbak: " + idbak[i] + "<br>");
					}

				}
			}
		}
		if (true) return;
		*/

		// Så henter vi all data via SNMP fra HUB'ene
		String[][] data = db.exece("select portname,mp,idbak,sysName,ip,swid,swport.id,type from swport,nettel where swid=nettel.id and idbak!='0' and kat='HUB';"); // limit 121,25
		String[] portname = data[0];
		String[] mp = data[1];
		String[] idbak = data[2];
		String[] sysName = data[3];
		String[] ip = data[4];
		String[] swid = data[5];
		String[] id = data[6];
		String[] type = data[7];

		com.outl("<b>Processing " + portname.length + " units.</b><br>");

		com.outl("<table width=\"100%\">");
		com.outl(" <tr>");
		com.outl("   <td width=\"4%\"><b>Nr</b></td>");
		com.outl("   <td width=\"16%\"><b>sysName</b></td>");
		com.outl("   <td width=\"12%\"><b>IP</b></td>");
		com.outl("   <td width=\"8%\"><b>Type</b></td>");
		com.outl("   <td width=\"30%\"><b>portname</b></td>");
		com.outl("   <td width=\"5%\"><b>port</b></td>");
		com.outl("   <td width=\"5%\"><b>New port</b></td>");
		com.outl("   <td width=\"20%\"><b>Status</b></td>");
		com.outl(" </tr>");
		com.outl("</table>");

		for (int i = 0; i < portname.length; i++)
		{
			String newPort = "";
			String status = "";
			String color;
			String portBak;

			// sjekk om det er flere downlinks til samme enhet
			int downlink = 0;
			String[] link = misc.tokenizel(portname[i], ":");
			if ( (link[0].charAt(0) == 'n' || link[0].charAt(0) == 'o') && link[0].length() > 1)
			{
				// joda, finn antall downlinks
				downlink = Integer.parseInt(link[0].substring(1, link[0].length() ));
			}

			if (downlink > 0)
			{
				// hent port med SNMP, for en bestemt unit i stack'en
				portBak = findPortBak(sysName[i], ip[i], null, true, downlink);

			} else
			{
				// hent port med SNMP
				portBak = findPortBak(sysName[i], ip[i], null, true);
			}

			if (portBak.equals("Not found"))
			{
				// not found
				newPort = "NA";
				status = "Not found";
				color = "red";

			} else
			if (portBak.equals("No change"))
			{
				// no change
				newPort = mp[i];
				status = "No change";
				color = "green";

			} else
			if (portBak.equals("Unsupported type"))
			{
				// unsupported type
				newPort = mp[i];
				status = "Unsupported type";
				color = "gray";

			} else
			{
				db.exec("update swport set mp='" + portBak + "' where id='" + id[i] + "';");

				newPort = portBak;
				status = "Updated";
				color = "blue";

			}

			String font1 = "<font color=\"" + color + "\">";
			String font2 = "</font>";

			com.outl("<table width=\"100%\">");
			com.outl(" <tr>");
			com.outl("   <td width=\"4%\">" + font1 + (i+1) + font2 +  "</td>");
			com.outl("   <td width=\"16%\">" + font1 + sysName[i] + font2 +  "</td>");
			com.outl("   <td width=\"12%\">" + font1 + ip[i] + font2 +  "</td>");
			com.outl("   <td width=\"8%\">" + font1 + type[i] + font2 +  "</td>");
			com.outl("   <td width=\"30%\">" + font1 + portname[i] + font2 +  "</td>");
			com.outl("   <td width=\"5%\">" + font1 + mp[i] + font2 +  "</td>");
			com.outl("   <td width=\"5%\">" + font1 + newPort + font2 +  "</td>");
			com.outl("   <td width=\"20%\">" + font1 + status + font2 + "</td>");
			com.outl(" </tr>");
			com.outl("</table>");
		}

	}

	/*
	private void updatePortBakOld()
	{
		com.outl("<b>updatePortBak</b><br>");

		String[][] data = getRootSwitches();

		String[] swId = data[0];
		String[] swName = data[1];

		for (int i = 0; i < swId.length; i++)
		{
			portBakExpand(swId[i], swName[i], null, null, 0);
		}

	}

	private void portBakExpand(String id, String swName, String port, String parentName, int depth)
	{
		String[][] data = db.exece("select portname,mp,idbak,sysName,ip from swport,nettel where idbak=nettel.id and swid='" + id + "' and portname like 'n:%' and idbak!='null';");
		String[] portname = data[0];
		String[] mp = data[1];
		String[] idbak = data[2];
		String[] nameBak = data[3];
		String[] ipBak = data[4];

		if (portname[0] == null)
		{
			com.outl("&nbsp;&nbsp;&nbsp;Error in swport! Record for " + swName + " is missing.<br>");
			return;
		}

		updateDbNode(parentName, swName, port, findPortBak(swName, null, null, true) );

		for (int j = 0; j < portname.length; j++)
		{
			if (portname[0] == null) break;

			String[] type = misc.tokenizel(portname[j], "-");

			if (type[1].charAt(0) == 's')
			{
				portBakExpand(idbak[j], nameBak[j], mp[j], swName, depth+1 );

			} else
			if (type[1].charAt(0) == 'h')
			{
				updateDbNode(swName, nameBak[j], mp[j], findPortBak(nameBak[j], ipBak[j], null, true) );
			}
		}
	}
	private void updateDbNode(String parentName, String name, String port, String portBak)
	{
		//printDepth(depth);
		if (port != null)
		{
			if (portBak.equals("Not found"))
			{
				// not found
			} else
			if (portBak.equals("No change"))
			{
				// no change
				com.outl("No update in swport, swid='" + parentName + "' and port='" + port + "' and idbak='" + name + "'.<br>");

			} else
			if (portBak.equals("Unsupported type"))
			{
				// unsupported type
			} else
			{
				com.outl("Updating swport, setting portBak='" + portBak + "' where swid='" + parentName + "' and port='" + port + "' and idbak='" + name + "'.<br>");
				db.exec("update swport set portBak='" + portBak + "' where portname='n:" + name + "' and mp='" + port + "';");
			}
		} else
		{
			com.outl("<b>Jobber n&aring; med kjernesvitsj " + name + "</b><br>");
		}

	}
	*/




	/* [/ni.updateStatic]
	 * Oppdater statiske felter i swport
	 */
	private void updateStatic()
	{
		//com.outl("<b>updateStatic</b><br>");
		com.outl("<table>");

		com.outl(" <tr>");
		com.outl("  <td colspan=50>");
		com.outl("   Legend: <font color=blue>New record</font> | <font color=green>Updated record</font> | <font color=red>Deleted record</font> | <font color=gray>No change</font>");
		com.outl("  </td>");
		com.outl(" </tr>");

		com.outl(" <tr>");
		com.outl("  <td><b>swid</b></td>");
		com.outl("  <td><b>swName</b></td>");
		com.outl("  <td><b>mp</b></td>");
		com.outl("  <td><b>vlan</b></td>");
		com.outl("  <td><b>portname</b></td>");
		com.outl("  <td><b>speed</b></td>");
		com.outl("  <td><b>idbak</b></td>");
		com.outl("  <td><b>portBak</b></td>");
		com.outl(" </tr>");

		String[][] data = getRootSwitches();

		String[] swId = data[0];
		String[] swName = data[1];

		for (int i = 0; i < swId.length; i++)
		{
			swRecord sw = new swRecord(null, null, null, null, null, null, null, null, null, swId[i], null);
			//com.outl("i: " + i + " swName: " + swName[i] + "<br>");
			staticExpand(swName[i], sw, null);

		}
		com.outl("</table>");

	}
	//private void staticExpand(String id, String swName, String port, String parentName, int depth)
	private void staticExpand(String swName, swRecord sw, String parentName)
	{
		// hent alle downlinker fra denne switchen
		//String[][] data = db.exece("select portname,mp,idbak,sysName,ip from swport,nettel where idbak=nettel.id and swid='" + id + "' and portname like 'n:%' and idbak!='null';");
		String[][] data = db.exece("select portname,swid,mp,vlan,status,duplex,speed,porttype,idbak,portBak from swport where swid='" + sw.getidbak() + "' and portname like 'n%:%' and idbak!='0';");
		String[] portname = data[0];
		String[] swid = data[1];
		String[] mp = data[2];
		String[] vlan = data[3];
		String[] status = data[4];
		String[] duplex = data[5];
		String[] speed = data[6];
		String[] porttype = data[7];
		String[] idbak = data[8];
		String[] portBak = data[9];

		if (portname[0] == null && parentName == null)
		{
			// Record for root switch mangler, error
			String[] info = db.exec("select id from swport where swid='" + sw.getidbak() + "' limit 1;");
			if (info[0] != null)
			{
				// ingen smarte records
				com.outl("<tr><td colspan=50><b>Root switch " + swName + " does not have any 'smart' downlinks, nothing to do.</b><br></td></tr>");
			} else
			{
				// ingen record i det hele tatt
				com.outl("<tr><td colspan=50><font color=red><b>Record for root switch " + swName + " is missing, but I cannot auto-insert a record for root switches.</b></font><br></td></tr>");
			}
			return;

		} else
		if (portname[0] == null)
		{
			// Record for switch mangler, sett inn
			String[] info = db.exec("select id from swport where swid='" + sw.getidbak() + "' limit 1;");
			if (info[0] == null)
			{
				com.outl("<tr><td colspan=50>Record for " + swName + " is missing, inserting static record.<br></td></tr>");

				// lag uplink av downlink
				String[] link = misc.tokenizel(sw.getportname(), ":");
				link[0] = link[0].replace('n', 'o');

				swRecord insertSw = new swRecord(sw.getidbak(), sw.getportBak(), "", sw.getvlan(), link[0] + ":" + parentName, sw.getstatus(), sw.getduplex(), sw.getspeed(), sw.getporttype(), sw.getswid(), sw.getmp() );

				//createSwRecord(id, String mp, String IfIndex, String vlan, String portname, String status, String duplex, String speed, String porttype, String idbak, String portBak)
				createSwRecord(null, swName, insertSw, true, false);
			} else
			{
				// ingen record i det hele tatt
				com.outl("<tr><td colspan=50>Switch " + swName + " does not have any 'smart' downlinks, nothing to do.<br></td></tr>");
			}


			return;
		}

		com.outl("<tr><td colspan=50><b>Now working with " + swName + " (" + sw.getidbak() + ").</b><br></td></tr>");

		// henter alle uplinker til denne enheten slik at vi kan sjekke om noen av dem ikke lengre eksisterer
		data = db.exece("select swid,swport.id,sysName,mp,vlan,portname,speed,idbak,portBak from swport,nettel where swid=nettel.id and idbak='" + sw.getidbak() + "' and portname like 'o%:%' and swport.static='Y';");
		// lag hasher av swid og tilsvarende idbak for å finne diferansen
		if (data[0][0] != null)
		{
			HashSet downlinks = new HashSet();
			for (int i = 0; i < idbak.length; i++)
			{
				downlinks.add(idbak[i]);
			}

			HashMap uplinks = new HashMap();
			for (int i = 0; i < data[0].length; i++)
			{
				String[] s = new String[9];
				s[0] = data[0][i];
				s[1] = data[1][i];
				s[2] = data[2][i];
				s[3] = data[3][i];
				s[4] = data[4][i];
				s[5] = data[5][i];
				s[6] = data[6][i];
				s[7] = data[7][i];
				s[8] = data[8][i];
				uplinks.put(data[0][i], s);
			}

			// tar bort alle id'er fra uplinks som også finnes i downlinks
			Set uplinkSet = uplinks.keySet();
			uplinkSet.removeAll(downlinks);

			// Går gjennom de gjenstående id'ene og sletter dem fra tabellen
			Set uplinkValues = uplinks.entrySet();
			Iterator iter = uplinkValues.iterator();
			if (!uplinks.isEmpty()) while (iter.hasNext())
			{
				Map.Entry entry = (Map.Entry)iter.next();
				String[] rec = (String[])entry.getValue();

				// skriver ut info om det som skal slettes
				String font1 = "<font color=red>";
				String font2 = "</font>";

				com.outl(" <tr>");
				com.outl("  <td>" + font1 + rec[0] + font2 + "</td>");
				com.outl("  <td>" + font1 + rec[2] + font2 + "</td>");
				com.outl("  <td>" + font1 + rec[3] + font2 + "</td>");
				com.outl("  <td>" + font1 + rec[4] + font2 + "</td>");
				com.outl("  <td>" + font1 + rec[5] + font2 + "</td>");
				com.outl("  <td>" + font1 + rec[6] + font2 + "</td>");
				com.outl("  <td>" + font1 + rec[7] + font2 + "</td>");
				com.outl("  <td>" + font1 + rec[8] + font2 + "</td>");
				com.outl(" </tr>");

				// fjerner swportId from swport-tabellen
				db.exec("delete from swport where id='" + rec[1] + "';");
			}
		}

		//staticNode(parentName, swName, port, findPortBak(swName, null, true) );

		for (int j = 0; j < portname.length; j++)
		{
			// sjekk om det er flere downlinks til samme enhet
			int downlinks = 1;
			String[] link = misc.tokenizel(portname[j], ":");
			if (link[0].charAt(0) == 'n' && link[0].length() > 1)
			{
				// joda, finn antall downlinks
				downlinks = Integer.parseInt(link[0].substring(1, link[0].length() ));
			}

			String[] type = misc.tokenizel(portname[j], "-");

			if (type.length > 1 && type[1].charAt(0) == 's')
			{
				//staticExpand(idbak[j], mp[j], IfIndex[j], vlan[j], portname[j], status[j], duplex[j], speed[j], porttype[j], swName, depth+1 );
				swRecord expandSw = new swRecord(swid[j], mp[j], "", vlan[j], portname[j], status[j], duplex[j], speed[j], porttype[j], idbak[j], portBak[j] );
				staticExpand(link[1], expandSw, swName);
				//com.outl("<tr><td>Return from expand!</td></tr>");

			} else
			if (type.length > 1 && type[1].charAt(0) == 'h')
			{
				//staticNode(swName, nameBak[j], mp[j], findPortBak(nameBak[j], ipBak[j], true) );
				swRecord insertSw = new swRecord(swid[j], mp[j], "", vlan[j], portname[j], status[j], duplex[j], speed[j], porttype[j], idbak[j], portBak[j] );
				staticNode(link[1], insertSw, swName);
			}
		}
	}
	private void staticNode(String swName, swRecord sw, String parentName)
	{
		// lag uplink av downlink
		String[] link = misc.tokenizel(sw.getportname(), ":");
		link[0] = link[0].replace('n', 'o');
		swRecord insertSw = new swRecord(sw.getidbak(), sw.getportBak(), "", sw.getvlan(), link[0] + ":" + parentName, sw.getstatus(), sw.getduplex(), sw.getspeed(), sw.getporttype(), sw.getswid(), sw.getmp() );

		// sjekk om en static record allerede eksisterer
		String[][] data = db.exece("select portname,mp,vlan,status,duplex,speed,porttype,idbak,portBak,id from swport where swid='" + insertSw.getswid() + "' and portname like '" + link[0] + ":%' and status='" + insertSw.getstatus() + "' and idbak!='0';");
		String[] portname = data[0];
		String[] mp = data[1];
		String[] vlan = data[2];
		String[] status = data[3];
		String[] duplex = data[4];
		String[] speed = data[5];
		String[] porttype = data[6];
		String[] idbak = data[7];
		String[] portBak = data[8];
		String[] id = data[9];

		if (portname[0] == null)
		{
			// sett inn ny record
			createSwRecord(null, swName, insertSw, true, false);
		} else
		{
			// sjekk om update er nødvendig
			String[] linkDb = misc.tokenizel(portname[0], ":");
			boolean update = false;

			if (!insertSw.getmp().equals(mp[0])) update = true;
			if (!insertSw.getvlan().equals(vlan[0])) update = true;
			if (!parentName.equals(linkDb[1])) update = true;
			if (!insertSw.getstatus().equals(status[0])) update = true;
			if (!insertSw.getduplex().equals(duplex[0])) update = true;
			if (!insertSw.getspeed().equals(speed[0])) update = true;
			if (!insertSw.getporttype().equals(porttype[0])) update = true;
			if (!insertSw.getidbak().equals(idbak[0])) update = true;
			if (!insertSw.getportBak().equals(portBak[0])) update = true;

			if (update)
			{
				// ingen new record, men update
				createSwRecord(id[0], swName, insertSw, false, true);
			} else
			{
				// bare skriv ut info, ingen update
				createSwRecord(id[0], swName, insertSw, false, false);
			}


		}






	}
	private void createSwRecord(String id, String swName, swRecord sw, boolean newRecord, boolean update)
	{
		String[] ins = new String[14];

		ins[0] = sw.getswid();
		ins[1] = sw.getmp();
		ins[2] = sw.getIfIndex();
		ins[3] = sw.getvlan();
		ins[4] = sw.getportname();
		ins[5] = sw.getstatus();
		ins[6] = sw.getduplex();
		ins[7] = sw.getspeed();
		ins[8] = sw.getporttype();
		ins[9] = sw.getidbak();
		ins[10] = "NOW()";
		ins[11] = "null";
		ins[12] = "Y";
		ins[13] = sw.getportBak();

		String font1 = "";
		String font2 = "";

		if (newRecord)
		{
			font1 = "<font color=blue>";
			font2 = "</font>";

			db.insert("swport", ins, 0);
		} else
		if (update)
		{
			// update
			String[] link = misc.tokenizel(sw.getportname(), ":");

			db.exec("update swport set mp='" + ins[1] + "' where id='" + id + "';");
			db.exec("update swport set vlan='" + ins[3] + "' where id='" + id + "';");
			db.exec("update swport set portname='" + ins[4] + "' where id='" + id + "';");
			db.exec("update swport set status='" + ins[5] + "' where id='" + id + "';");
			db.exec("update swport set duplex='" + ins[6] + "' where id='" + id + "';");
			db.exec("update swport set speed='" + ins[7] + "' where id='" + id + "';");
			db.exec("update swport set porttype='" + ins[8] + "' where id='" + id + "';");
			db.exec("update swport set idbak='" + ins[9] + "' where id='" + id + "';");
			db.exec("update swport set portBak='" + ins[13] + "' where id='" + id + "';");

			font1 = "<font color=green>";
			font2 = "</font>";


		} else
		{
			font1 = "<font color=gray>";
			font2 = "</font>";
		}

		com.outl(" <tr>");

		com.outl("  <td>" + font1 + ins[0] + font2 + "</td>");
		com.outl("  <td>" + font1 + swName + font2 + "</td>");
		com.outl("  <td>" + font1 + ins[1] + font2 + "</td>");
		com.outl("  <td>" + font1 + ins[3] + font2 + "</td>");
		com.outl("  <td>" + font1 + ins[4] + font2 + "</td>");
		com.outl("  <td>" + font1 + ins[7] + font2 + "</td>");
		com.outl("  <td>" + font1 + ins[9] + font2 + "</td>");
		com.outl("  <td>" + font1 + ins[13] + font2 + "</td>");

		com.outl(" </tr>");


		//com.outl("Record inserted, swid(" + swName + "): " + ins[0] + " mp: " + ins[1] + " vlan: " + ins[3] + " portname: " + ins[4] + " speed: " + ins[7] + " idbak: " + ins[9] + " portBak: " + ins[13] + "<br>");



	}
	//private void createSwRecord(String swid, String mp, String IfIndex, String vlan, String portname, String status, String duplex, String speed, String porttype, String idbak, String portBak)
	//{
	//	createSwRecord(new swRecord
	//}


	/* [/ni.listSwport]
	 * Skriv ut swport
	 */
	private void listSwport()
	{
		String name = "<b>NTNU network</b>";
		String imgRoot = "<img border=0 src=\"" + com.getConf().get("ServletGFXRoot") + "/";
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
		String imgRoot = "<img border=0 src=\"" + com.getConf().get("ServletGFXRoot") + "/";
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

	/* [/ni.searchSwport]
	 * Søker etter nettel-enheter og viser dem via listSwport
	 */
	private void searchSwport()
	{




	}


	/* [/ni.updateCommunity]
	 * Oppdatert community-tabell fra /usr/local/nettinfo/etc/nettel.ntnu
	 */
	private void findMissingLinks()
	{
		HashMap nettelId = new HashMap();
		HashSet swportId = new HashSet();
		String[][] data;
		String[] info;

		// fetch all IDs from nettel
		data = db.exece("select id,sysName,ip,type,kat from nettel where kat='HUB';");
		for (int i = 0; i < data[0].length; i++)
		{
			String[] s = new String[5];
			s[0] = data[0][i];
			s[1] = data[1][i];
			s[2] = data[2][i];
			s[3] = data[3][i];
			s[4] = data[4][i];

			nettelId.put(data[0][i], s);
		}
		com.outl("nettelIdSize: " + nettelId.size() + "<br>");

		// fetch all IDs from swport
		info = db.exec("select swid from swport group by swid;");
		for (int i = 0; i < info.length; i++)
		{
			swportId.add(info[i]);
		}
		com.outl("swportIdSize: " + swportId.size() + "<br>");

		// remove swport-IDs from nettel hashmap
		Set nettelIdSet = nettelId.keySet();
		nettelIdSet.removeAll(swportId);
		com.outl("missingIdSize: " + nettelId.size() + "<br>");

		//fetch all ips and other info
		data = db.exece("select ip,swid,sysName from swport,nettel where swid=nettel.id group by ip;");


		Set nettelIdValues = nettelId.entrySet();
		Iterator iter = nettelIdValues.iterator();
		while (iter.hasNext())
		{
			Map.Entry entry = (Map.Entry)iter.next();
			info = (String[])entry.getValue();

			String id = info[0];
			String sysName = info[1];
			String ip = info[2];

			com.outl("<b>" + info[0] + ", " + info[1] + ", " + info[2] );

			String bits = findGwBits(ip);

			com.outl("bits: " + bits + "</b><br>");

			int[] sameSubnet = misc.findInSameSubnet(ip, bits, data[0] );

			if (sameSubnet != null)
			{
				//com.outl("Antall enheter p&aring; samme subnet: " + sameSubnet.length + "<br>");

				for (int i = 0; i < sameSubnet.length; i++)
				{
					com.outl("&nbsp;&nbsp;&nbsp;" + data[2][sameSubnet[i]] + ", IP: " + data[0][sameSubnet[i]] + "<br>");
				}
			} else
			{
				com.outl("&nbsp;&nbsp;&nbsp;" + "<i>Feil: Ingen enheter p&aring; samme subnet registrert i swport</i>" + "<br>");
			}

		}




	}


	/* [/ni.updateCommunity]
	 * Oppdatert community-tabell fra /usr/local/nettinfo/etc/nettel.ntnu
	 */
	private void updateCommunity()
	{
		String f = "/usr/local/nettinfo/etc/nettel.txt";
		/*
		int[] keys = { 0, 2 };
		HashMap hm = db.exech(keys, "select ip,mp,portname from nettel,swport where nettel.id=swport.swid and kat='HUB' and status!='down';");
		*/

		try
		{
			BufferedReader in = new BufferedReader(new FileReader(f));
			String line;
			com.outl("<pre>");

			while (in.ready())
			{
				line = in.readLine();
				if (line.length() > 0 && !(line.trim().charAt(0) == ';' || line.trim().charAt(0) == '#') )
				{
					String[] opt = misc.tokenize(line.trim(), "\t");
					//com.outl("Processing line: " + line);
					if (opt.length > 5)
					{
						//com.outl("&nbsp;&nbsp;Checking passwords...");
						// oppdater tabellen
						String ip = opt[1];
						String ro = opt[5];
						String rw = "";
						if (opt.length > 6) rw = opt[6];

						String[] id = db.exec("select id from nettel where ip='" + ip + "';");

						if (id[0] != null)
						{
							String[][] data = db.exece("select ro,rw from community where nettelid='" + id[0] + "';");

							if (data[0][0] != null)
							{
								// sjekk ro
								if (!data[0][0].equals(ro) && !ro.equals("") )
								{
									db.exec("update community set ro='" + ro + "' where nettelid='" + id[0] + "';");
									com.outl("Updatedet read-only entry for IP: " + ip + " ro: " + ro + " rw: " + rw + "");
								}

								// sjekk rw
								if (!data[1][0].equals(rw) && !rw.equals("") )
								{
									db.exec("update community set rw='" + rw + "' where nettelid='" + id[0] + "';");
									com.outl("Updatedet read-write entry for IP: " + ip + " ro: " + ro + " rw: " + rw + "");
								}



							} else
							{
								// fins ikke, vi må sette inn
								String[] ins = new String[4];

								ins[0] = "null";
								ins[1] = id[0];
								ins[2] = ro;
								ins[3] = rw;

								db.insert("community", ins, 0);

								com.outl("Inserted new entry for nettel: " + id[0] + " IP: " + ip + " ro: " + ro + " rw: " + rw + "");
							}
						}
					} // if (opt.length > 5)
					if (opt.length > 7)
					{
						//com.outl("  Checking uplink ports...");
						String ip = opt[1];
						ArrayList ports = new ArrayList();
						for (int i=7; i < opt.length; i++) if (opt[i].charAt(0) == 'u') ports.add(opt[i].substring(1, opt[i].length()) );
						if (ports.size() == 0) continue;

						//com.outl("    Fetching data for ip: " + ip);

						String[][] data = db.exece("select swport.id,ip,portname,mp,sysName from nettel,swport where nettel.id=swport.swid and kat='HUB' and ip='"+ip+"' and status!='down' and portname like 'o%' order by portname;");

						if (data[0][0] == null)
						{
							String[] info = db.exec("select sysName from nettel where ip='" + ip + "';");
							String name = (info[0] == null) ? "&lt;not found&gt;" : info[0];

							com.outl("<font color=red>ERROR: swport is missing data for IP: " + ip + " ("+name+")</font>");
							continue;
						}

						for (int i=0; i < data[0].length; i++)
						{
							for (int j=0; j < ports.size(); j++)
							{
								String port = (String)ports.get(j);
								port = port.replace(':','.');
								//com.outl("      Port is: " + port);
								//com.outl("      data[2]["+i+"] is: " + data[2][i]);
								String[] t = misc.tokenizel(data[2][i], ":"); if (t.length == 1) continue;

								if (t[0].equals("o"+port.substring(0, 1)) || data[0].length == 1)
								{
									// Sjekk om mp allerede er riktig
									if (!data[3][i].equals(port))
									{
										// Nei, oppdater
										String b = (data[3][i].length()==0) ? "&lt;blank&gt;" : data[3][i];
										com.outl("<font color=blue>Uplink for " + data[4][i] + ", portname: " + data[2][i] + " is " + b + ", but nettel.txt says: " + port + "|</font>");
										//db.exec("update swport set mp='"+port+"' where id='"+data[0][i]+"';");
									}
								}
							}
						} // end for()


					}

				}
			}
			com.outl("All done, community is up-to-date.");
			com.outl("</pre>");
		}
		catch (java.io.IOException e)
		{
			// Config-fil mangler, bruker kun default-verdier. Skriver likevel en advarsel.
			com.out("Konfigurasjonsfil '" + f + "' mangler. Kan ikke fortsette.");
		}




	}

	/* [/admin.antUserTreff]
	 * Viser antall treff fra user-søk
	 */
	private void antUserTreff()
	{
		String field = com.getp("searchField");
		String search = com.getp("searchString");
		if (search == null)
		{
			search = "";
		}

		if (field.equals("login"))
		{
			field = "users.login";
		}

		String[] info = db.exec("select users.login from users left join personalia on users.login=personalia.login where " +
										field + " like '%" + search + "%';", true);

		if (info[0] != null)
		{
			com.out(info[0]);
		} else
		{
			com.out("0");
		}

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



	/*
	 * Finner gw for en gitt ip
	 */
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







	/************************************************************
	* Level 2 functions											*
	* user.<>.*													*
	************************************************************/

	/* [/admin.temp.list.*]
	 * Viser verdi fra felt i users-tabell
	 */
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
			if (subSect.equals("listSwport"))
			{
				String p1 = com.getp("p1");

				if (p1 != null)
				{
					String p2 = com.getp("p2");
					if (p2 != null)
					{
						HashMap trav;
						Object o = com.getUser().getData("traverseList");
						if (o != null)
						{
							trav = (HashMap)o;
						} else
						{
							trav = new HashMap();
						}
						if (p1.equals("open"))
						{
							trav.put(p2, new Boolean(false) );
						} else
						if (p1.equals("close"))
						{
							trav.remove(p2);
						} else
						if (p1.equals("expand"))
						{
							trav.put(p2, new Boolean(true) );
						}
						com.getUser().setData("traverseList", trav);
					}
				}
				html = "html/ni/listSwport.html";
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
	Sql db;
	int num;
	int tempNr;




}

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




























