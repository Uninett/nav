/*
 * NTNU ITEA "nav" prosjekt
 *
 * Server-modul for vlanPlot
 *
 * Skrvet av: Kristian Eide <kreide@online.no>
 *
 */

import no.ntnu.nav.ConfigParser.*;
import no.ntnu.nav.Database.*;
import no.ntnu.nav.Path;

import java.io.*;
import java.util.*;
import java.sql.*;

import javax.servlet.*;
import javax.servlet.http.*;

public class vPServer extends HttpServlet
{
	public static final String scriptName = "default";

	public void init(ServletConfig conf) throws ServletException
	{
		super.init(conf);
	}

	public void service(HttpServletRequest req, HttpServletResponse res) throws IOException
	{
		//Com com = new Com();
		res.setContentType("text/html");
		res.setHeader("nav-template-wrapper", "false");
		ServletOutputStream out = res.getOutputStream();


		String dbConfigFile = getServletContext().getInitParameter("dbConfigFile");
		String configFile = getServletContext().getInitParameter("configFile");
		String navConfigFile = getServletContext().getInitParameter("navConfigFile");

		ConfigParser cp, dbCp, navCp;
		try {
			cp = new ConfigParser(Path.sysconfdir + File.separatorChar + configFile);
		} catch (IOException e) {
			out.println("Error, could not read config file: " + Path.sysconfdir + File.separatorChar + configFile);
			return;
		}
		try {
			dbCp = new ConfigParser(Path.sysconfdir + File.separatorChar + dbConfigFile);
		} catch (IOException e) {
			out.println("Error, could not read database config file: " + Path.sysconfdir + File.separatorChar + dbConfigFile);
			return;
		}
		try {
			navCp = new ConfigParser(Path.sysconfdir + File.separatorChar + navConfigFile);
		} catch (IOException e) {
			out.println("Error, could not read nav config file: " + Path.sysconfdir + File.separatorChar + navConfigFile);
			return;
		}

		// Åpne databasen
		if (!Database.openConnection(dbCp.get("dbhost"), dbCp.get("dbport"), dbCp.get("db_nav"), dbCp.get("script_"+scriptName), dbCp.get("userpw_"+dbCp.get("script_"+scriptName)))) {
			out.println("Error, could not connect to database!");
			return;
		}
		HttpSession session = req.getSession(true);

		// Check user
		String user = req.getHeader("x-authenticated-user");
		boolean hasAdmin = user != null && user.length() > 0;

		SqlBoks.req = req;
		SqlBoks.res = res;
		SqlBoks.out = out;
		SqlAdmin.req = req;
		SqlAdmin.out = out;

		String section = req.getParameter("section");
		String request = req.getParameter("request");

		//try {
			if (section != null && request != null) {
				//StringTokenizer st = new StringTokenizer(request, ",");
				String[] r = request.split(",");

				if (section.equals("boks")) {
					SqlBoks.serviceRequest(r, user, hasAdmin, cp, navCp);
				} else
				if (section.equals("admin")) {
					if (!hasAdmin) {
						failAuth(out);
						return;
					}
					SqlAdmin.serviceRequest(r, user);
				}
			} else {
				out.println("Missing parameter.");
			}
		//} catch (Exception e) {
		//	out.println("Error, exception thrown: " + e.getMessage());
		//}

		out.close(); //Close the output stream
		Database.closeConnection(); // Close the SQL connection
	}

	private void failAuth(ServletOutputStream out) throws IOException {
		out.println("Error, failed authentication!");
	}


}

class SqlBoks
{
	public static HttpServletRequest req;
	public static HttpServletResponse res;
	public static ServletOutputStream out;

	private static String rrdTime;
	private static String rrdType;
	private static ConfigParser navCp;

	private static LinkedList reqQ = new LinkedList();
	static void serviceRequest(String[] reqA, String user, boolean hasAdmin, ConfigParser cp, ConfigParser _navCp) throws IOException
	{
		reqQ.addAll(Arrays.asList(reqA));
		navCp = _navCp;

		rrdTime = req.getParameter("time");
		rrdType = req.getParameter("type");

		while (!reqQ.isEmpty()) {
			String req = (String)reqQ.removeFirst();
			try {
				if (req.equals("listConfig")) listConfig(user, hasAdmin, cp, navCp);
				else if (req.equals("listRouters")) listRouters();
				else if (req.equals("listRouterGroups")) listRouterGroups();
				else if (req.equals("listRouterXY")) listRouterXY();
				else if (req.equals("listBoks")) listBoks();
				else if (req.equals("listLoad")) listLoad();
				else outl("Unsupported request string: " + req);


			} catch (SQLException e) {
				outl("<pre>");
				outl("Got SQLException: " + e.getMessage());
				e.printStackTrace(new PrintStream(out));
				outl("Stack trace complete.");
				outl("</pre>");
			}
		}
	}

	// Config for vP
	static void listConfig(String user, boolean hasAdmin, ConfigParser cp, ConfigParser navCp) throws SQLException
	{
		outl("listConfig");

		String vpNetName = cp.get("vpNetName");
		String vpNetLink = cp.get("vpNetLink");

		outl("vpNetName^"+vpNetName);
		outl("vpNetLink^"+vpNetLink);
		outl("domainSuffix^"+navCp.get("DOMAIN_SUFFIX"));
		outl("userName^"+user);

		outl("hasAdmin^"+hasAdmin);

	}

	// Lister ut alle routere på topp-nivå og linker/vlan mellom dem
	static void listRouters() throws SQLException
	{
		HashMap text = new HashMap();
		HashMap textOut = new HashMap();

		/*
		listRouterText
		t0,2
		t1,"sysName: ^ !!Kat: ^", 569, 568, 567
		t2,"sysName: ^ !!Kat: ^", -92, -186
		569,hb-gw,GW
		568,hb-gw2,GW
		567,sb-gw,GW
		-92,fddi,stam
		-186,isdn,stam

		listRouterLinkText
		t0,2
		*/

		// && = variabelnavn, ## = bytt ut med gitt verdi, !! = \n

		/*
		String gwBoksText = "boksid: &&boksid!!sysName: &&sysName!!Kat: ##!!Last: &&boksLast";
		String defBoksText = "sysName: &&sysName!!Kat: ##!!Ikke-gw-boks";
		String[] gwBoksFields = {
			"kat",
		};
		String[] defBoksFields = {
			"kat",
		};

		String gwLinkText = "gwportid: &&linkid!!&&sysNameFrom -> &&sysNameTo!!Kat: ##!!Interface: ##!!Speed: ##!!OSPF: ##!!Last: &&linkLastPst (&&linkLast)";
		String defLinkText = "gwportid: &&linkid!!&&sysNameFrom -> &&sysNameTo!!Kat: ##!!Last: &&linkLastPst (&&linkLast)";
		String[] linkLinkFields = {
			"kat",
			"interf",
			"speed",
			"metric"
		};
		String[] defLinkFields = {
			"kat",
		};

		String cFields = "";
		{
			HashSet hs = new HashSet();

			for (int i=0;i<gwBoksFields.length;i++) if (hs.add(gwBoksFields[i])) cFields += ","+gwBoksFields[i];
			for (int i=0;i<defBoksFields.length;i++) if (hs.add(defBoksFields[i])) cFields += ","+defBoksFields[i];

			for (int i=0;i<linkLinkFields.length;i++) if (hs.add(linkLinkFields[i])) cFields += ","+linkLinkFields[i];
			for (int i=0;i<defLinkFields.length;i++) if (hs.add(defLinkFields[i])) cFields += ","+defLinkFields[i];
		}
		*/

		// && = variabelnavn, ## = bytt ut med gitt verdi, !! = \n
		{
			String[] s = {
				"Name: &&sysname!!Category: ##!!Type: ##!!Room: ##!!CPU load: &&boksLast",
				"catid",
				"typename",
				"roomid",
			};
			text.put("gwBoks", s);
			text.put("gswBoks", s);
		}
		{
			String[] s = {
				"Name: &&sysName!!Category: core!!Net addr: ##",
				"netaddr",
			};
			text.put("coreBoks", s);
		}
		{
			String[] s = {
				"Name: &&sysname!!Category: ##",
				"catid",
			};
			text.put("defBoks", s);
		}

		// Linker
		{
			String[] s = {
				"Link: &&sysNameFrom -> &&sysNameTo!!Interface: ##!!IP address: ##!!Net ident: ##!!Capacity: ## Mbps!!Metric: ##!!Load: &&linkLastPst (&&linkLast)",
				"interface",
				"gwip",
				"netident",
				"speed",
				"metric",
			};
			text.put("gw-gwLink", s);
		}
		{
			String[] s = {
				"Link: &&sysNameFrom -> &&sysNameTo!!Interface: ##!!IP address: ##!!Net ident: ##!!Capacity: ## Mbps!!Metric: ##!!Load: &&linkLastPst (&&linkLast)",
				"interface",
				"gwip",
				"netident",
				"speed",
				"metric",
			};
			text.put("gw-coreLink", s);
			text.put("core-gwLink", s);
			text.put("gsw-coreLink", s);
			text.put("core-gswLink", s);

			text.put("gsw-defLink", s);
			text.put("def-gswLink", s);
			text.put("gw-defLink", s);
			text.put("def-gwLink", s);
			text.put("core-defLink", s);
			text.put("def-coreLink", s);
			text.put("def-defLink", s);
		}

		/*
		{
			String[] s = {
				"&&sysNameFrom -> &&sysNameTo!!Interface: ##!!OSPF: ##!!Nettadr: ##!!Capacity: ##!!Last: &&linkLastPst (&&linkLast)!!(gw->def)",
				"interface",
				"metric",
				"netaddr",
				"speed"
			};
			text.put("gw-defLink", s);
		}
		{
			String[] s = {
				"&&sysNameFrom -> &&sysNameTo!!OSPF: ##!!Nettadr: ##!!Capacity: ##!!Last: &&linkLastPst (&&linkLast)!!(stam->gw)",
				"metric",
				"netaddr",
				"speed"
			};
			text.put("stam-gwLink", s);
		}
		{
			String[] s = {
				"&&sysNameFrom -> &&sysNameTo!!OSPF: ##!!Nettadr: ##!!Capacity: ##!!Last: &&linkLastPst (&&linkLast)!!(def->gw)",
				"metric",
				"netaddr",
				"speed"
			};
			text.put("def-gwLink", s);
		}
		{
			String[] s = {
				"&&sysNameFrom -> &&sysNameTo!!Nettadr: ##!!Capacity: ##!!Last: &&linkLastPst (&&linkLast)!!(def->def)",
				"netaddr",
				"speed"
			};
			text.put("def-defLink", s);
		}
		*/


		String cFields = "";
		{
			HashSet hs = new HashSet();
			String[] aa = { "gwportid", "netboxid", "sysname", "interface", "prefixid", "nettype", "catid", "netident" };
			for (int i=0; i < aa.length; i++) hs.add(aa[i].toLowerCase());

			Iterator iter = text.entrySet().iterator();
			while (iter.hasNext()) {
				Map.Entry me = (Map.Entry)iter.next();
				String key = (String)me.getKey();
				textOut.put(key, new ArrayList());

				String[] s = (String[])me.getValue();
				for (int i=1;i<s.length;i++) if (hs.add(s[i].toLowerCase())) cFields += ","+s[i].toLowerCase();
			}
		}


		ResultSet rs = Database.query("SELECT gwportid,netboxid,sysname,interface,prefix.prefixid,nettype,catid,netident"+cFields+" FROM gwport JOIN gwportprefix USING(gwportid) JOIN prefix USING (prefixid) JOIN vlan USING(vlanid) JOIN module USING (moduleid) JOIN netbox USING (netboxid) JOIN type USING(typeid) WHERE nettype NOT IN ('loopback','unknown','lan') ORDER BY netboxid");
		// SELECT gwportid,boksid,sysName,gwport.prefiksid,nettype,kat,nettident FROM (gwport JOIN prefiks USING (prefiksid)) JOIN boks USING (boksid) WHERE nettype NOT IN ('loopback','ukjent','lan') ORDER BY boksid


		//SELECT gwportid,boksid,sysName,gwport.prefiksid,komm FROM (gwport JOIN prefiks USING (prefiksid)) JOIN boks USING (boksid) WHERE gwport.prefiksid>0 ORDER BY boksid
		//SELECT gwportid,boksid,sysName,gwport.prefiksid,komm FROM (gwport JOIN prefiks USING (prefiksid)) JOIN boks USING (boksid);
		//SELECT gwportid,boksid,sysName,gwport.prefiksid FROM gwport JOIN boks USING (boksid) ORDER BY boksid
		//SELECT gwportid,boksid,sysName,gwport.prefiksid FROM gwport JOIN boks USING (boksid) WHERE gwport.prefiksid IN (SELECT prefiksid FROM gwport GROUP BY prefiksid HAVING COUNT(prefiksid)>=2) ORDER BY boksid

		HashMap pRouters = new HashMap();
		HashMap sysNames = new HashMap();
		ArrayList links = new ArrayList();
		ArrayList l=null;
		int curid=0;

		HashMap linkInfo = new HashMap();

		HashMap textBoks = new HashMap();
		ArrayList routerBoksIds = new ArrayList();
		ArrayList otherBoksIds = new ArrayList();

		HashMap textLinks = new HashMap();
		//ArrayList routerLinkIds = new ArrayList();
		//ArrayList otherLinkIds = new ArrayList();


		// Gå gjennom data fra databasen og legg det i datastrukturene klar for å skrives ut
		HashSet boksDupe = new HashSet();
		while (rs.next()) {
			Integer gwportid = new Integer(rs.getString("gwportid"));
			Integer boksid = new Integer(rs.getString("netboxid"));
			Integer prefiksid = new Integer(rs.getString("prefixid"));
			String nettype = rs.getString("nettype");
			String kat = rs.getString("catid").toLowerCase();

			if (!pRouters.containsKey(prefiksid)) {
				// Ny prefiksid oppdaget, lag tom liste for den og legg til enheten
				pRouters.put(prefiksid, new ArrayList() );

				if ("static".equals(nettype)) continue;
				if (!nettype.equals("link")) {
					String nettident = rs.getString("netident");
					if (nettident == null || nettident.length() == 0) nettident = "unknown_netident";
					if (nettident.indexOf("-fw") != -1) nettype = "fw";

					String[] s = { nettident, nettype };
					sysNames.put("-"+prefiksid, s);

					// Egen sær ting for tekst på ikke-gw bokser
					String[] fields = (String[])text.get(nettype+"Boks");
					if (fields == null) fields = (String[])text.get("defBoks");
					if (fields == null) continue; // fail-safe

					ArrayList tl = (ArrayList)textOut.get(nettype+"Boks");
					if (tl == null) tl = (ArrayList)textOut.get("defBoks");
					if (tl == null) continue; // fail-safe

					s = new String[fields.length];
					s[0] = "-"+prefiksid;
					for (int i=1;i<s.length;i++) s[i] = rs.getString(fields[i]);
					tl.add(s);

					/*
					if (nettype.equals("elink")) {
						String[] s = { rs.getString("orgid"), nettype };
						sysNames.put("-"+prefiksid, s);
					} else {
						String[] s = { rs.getString("komm"), nettype };
						sysNames.put("-"+prefiksid, s);
					}
					*/
				}
			}
			ArrayList pRouterL = (ArrayList)pRouters.get(prefiksid);
			pRouterL.add(gwportid);
			pRouterL.add(boksid);

			// Legg til link-info
			{
				String[] s = {
					rs.getString("speed"),
					rs.getString("interface")
				};
				linkInfo.put(gwportid, s);
			}

			// Legg til tekst for bokser
			if (boksDupe.add(boksid)) {
				// Legg til tekst for bokser
				String[] fields = (String[])text.get(kat+"Boks");
				if (fields == null) fields = (String[])text.get("defBoks");
				if (fields == null) continue; // fail-safe

				ArrayList tl = (ArrayList)textOut.get(kat+"Boks");
				if (tl == null) tl = (ArrayList)textOut.get("defBoks");
				if (tl == null) continue; // fail-safe

				String[] s = new String[fields.length];
				s[0] = String.valueOf(boksid);
				for (int i=1;i<s.length;i++) s[i] = rs.getString(fields[i]);
				tl.add(s);

				/*
				String kat = rs.getString("kat").toLowerCase();

				String[] boksFields;
				if (kat.equals("gw")) boksFields = gwBoksFields;
				else boksFields = defBoksFields;

				String[] s = new String[boksFields.length];
				for (int i=0;i<boksFields.length;i++) s[i] = rs.getString(boksFields[i]);
				textBoks.put(boksid, s);
				*/
			}


			if (nettype.equals("link")) nettype = "gw";
			// Legg til tekst for link gw->gw eller gw->(stam||elink)
			{
				String[] fields = (String[])text.get("gw-"+nettype+"Link");
				if (fields == null) fields = (String[])text.get("gw-defLink");
				if (fields == null) continue; // fail-safe

				ArrayList tl = (ArrayList)textOut.get("gw-"+nettype+"Link");
				if (tl == null) tl = (ArrayList)textOut.get("gw-defLink");
				if (tl == null) continue; // fail-safe

				String[] s = new String[fields.length];
				s[0] = String.valueOf(gwportid);
				for (int i=1;i<s.length;i++) s[i] = rs.getString(fields[i]);

				tl.add(s);
			}

			// Legg til tekst for link fra (stam||elink) -> gw
			if (!nettype.equals("gw")) {
				String[] fields = (String[])text.get(nettype+"-"+kat+"Link");
				if (fields == null) fields = (String[])text.get(nettype+"-defLink");
				if (fields == null) fields = (String[])text.get("def-defLink");
				if (fields == null) continue; // fail-safe

				ArrayList tl = (ArrayList)textOut.get(nettype+"-"+kat+"Link");
				if (tl == null) tl = (ArrayList)textOut.get(nettype+"-defLink");
				if (tl == null) tl = (ArrayList)textOut.get("def-defLink");
				if (tl == null) continue; // fail-safe

				String[] s = new String[fields.length];
				s[0] = "-"+gwportid;
				for (int i=1;i<s.length;i++) s[i] = rs.getString(fields[i]);

				tl.add(s);
			}

			if (rs.getInt("netboxid")!=curid) {
				curid = rs.getInt("netboxid");
				l = new ArrayList();
				l.add(new Integer(curid));
				links.add(l);
			}
			l.add(prefiksid);

			String[] s = { rs.getString("sysname"), kat };
			sysNames.put(boksid, s);

		}

		// Skriv ut liste over rutere
		outl("listRouters");
		//outl("boksid^sysname^kat");
		Iterator iter = sysNames.entrySet().iterator();
		Set rrdNetboxid = new HashSet();
		Map sysnameMap = new HashMap();
		while (iter.hasNext()) {
			Map.Entry entry = (Map.Entry)iter.next();
			// Ikke skriv ut (stam||elink) rutere (negativ boksid)
			String boksid = entry.getKey().toString();
			if (boksid.charAt(0) == '-') continue;

			String[] s = (String[])entry.getValue();
			outl(boksid + "^" + s[0] + "^" + s[1] );
			routerBoksIds.add(boksid);
			rrdNetboxid.add(boksid);
			sysnameMap.put(boksid, s[0]);
		}

		{
			Map mm = new HashMap();
			mm.put("boxId", rrdNetboxid);
			mm.put("datatype", "cpu5min");
			loadMap.put("listBoxLoad", mm);
		}

		// Skriv ut alle (stam||elink) rutere
		iter = pRouters.entrySet().iterator();
		while (iter.hasNext()) {
			Map.Entry entry = (Map.Entry)iter.next();
			Integer prefiksid = (Integer)entry.getKey();
			ArrayList pRouterL = (ArrayList)entry.getValue();
			if (pRouterL.size() == 4) continue;

			String[] s = (String[])sysNames.get("-"+prefiksid);
			if (s == null) {
				//outl("ERROR at prefiksid: " + prefiksid);
				continue;
			}
			outl("-"+prefiksid + "^" + s[0] + "^" + s[1]);
			otherBoksIds.add("-"+prefiksid);
		}

		// Skriv ut liste over linker mellom ruterne
		outl("listRouterLinks");
		//outl("boksid^linkto^kat");
		Set routerLinkIds = new HashSet();
		//List rrdLinks = new ArrayList();
		for (int i=0; i<links.size(); i++) {
			l = (ArrayList)links.get(i);
			int myBoksid = ((Integer)l.get(0)).intValue();
			out(""+myBoksid);
			for (int j=1; j<l.size(); j++) {
				Integer prefiksid = (Integer)l.get(j);
				ArrayList pRouterL = (ArrayList)pRouters.get(prefiksid);
				if (pRouterL.size() == 4) {
					int g1 = ((Integer)pRouterL.get(0)).intValue();
					int v1 = ((Integer)pRouterL.get(1)).intValue();
					int g2 = ((Integer)pRouterL.get(2)).intValue();
					int v2 = ((Integer)pRouterL.get(3)).intValue();
					if (myBoksid == v1) v1 = v2; else g1 = g2;
					// Format: linkid,boksid
					out("^"+g1+","+v1);
					routerLinkIds.add(new Integer(g1));
					//rrdLinks.add(new String[] { ""+myBoksid, ""+g1, (String)sysnameMap.get(""+myBoksid) });
				}
			}
			outl("");
		}

		// Skriv ut alle (stam||elink) linker
		Set otherLinkIds = new HashSet();
		iter = pRouters.entrySet().iterator();
		while (iter.hasNext()) {
			Map.Entry entry = (Map.Entry)iter.next();
			Integer prefiksid = (Integer)entry.getKey();
			ArrayList pRouterL = (ArrayList)entry.getValue();
			if (pRouterL.size() == 4) continue;

			out("-" + prefiksid);
			for (int i=0;i<pRouterL.size(); i+=2) {
				out("^" + pRouterL.get(i) + "," + pRouterL.get(i+1));
				otherLinkIds.add(pRouterL.get(i));
			}
			outl("");
		}

		{
			Map mm = new HashMap();
			mm.put("gwId", routerLinkIds);
			mm.put("dualGwId", otherLinkIds);
			loadMap.put("listLinkLoad", mm);
		}

		//listCPULinkLoad(rrdLinks, linkInfo);

		outl("listRouterLinkInfo");
		iter = linkInfo.entrySet().iterator();
		while (iter.hasNext()) {
			Map.Entry entry = (Map.Entry)iter.next();
			Integer gwportid = (Integer)entry.getKey();
			String[] s = (String[])entry.getValue();

			out(gwportid.toString());
			for (int i=0;i<s.length; i++) {
				out("^" + s[i]);
			}
			outl("");
		}

		// Skriv ut tekst for bokser
		String[] types = {
			"Boks",
			"Link"
		};
		for (int typ=0; typ < types.length; typ++) {
			outl("list"+types[typ]+"Text");
			int tcnt=0;
			iter = textOut.entrySet().iterator();
			while (iter.hasNext()) {
				Map.Entry me = (Map.Entry)iter.next();
				String key = (String)me.getKey();
				if (!key.endsWith(types[typ])) continue;
				l = (ArrayList)me.getValue();

				String txt = ((String[])text.get(key))[0];
				out("t"+tcnt+"^"+txt);
				for (int i=0; i < l.size(); i++) out("^"+((String[])l.get(i))[0]);
				outl("");
				for (int i=0; i < l.size(); i++) {
					String[] s = (String[])l.get(i);
					out(s[0]);
					for (int j=1; j < s.length; j++) out("^"+s[j]);
					outl("");
				}
				tcnt++;
			}
		}

		/*
		outl("listRouterText");
		out("t0^"+gwBoksText);
		for (int i=0;i<routerBoksIds.size();i++) out("^"+routerBoksIds.get(i));
		outl("");
		out("t1^"+defBoksText);
		for (int i=0;i<otherBoksIds.size();i++) out("^"+otherBoksIds.get(i));
		outl("");

		iter = textBoks.entrySet().iterator();
		while (iter.hasNext()) {
			Map.Entry entry = (Map.Entry)iter.next();
			Integer boksid = (Integer)entry.getKey();
			String[] s = (String[])entry.getValue();

			out(""+boksid);
			for (int i=0;i<s.length;i++) out("^"+s[i]);
			outl("");
		}

		// Skriv ut tekst for linker
		outl("listRouterLinkText");
		out("t0^"+gwLinkText);
		for (int i=0;i<routerLinkIds.size();i++) out("^"+routerLinkIds.get(i));
		outl("");
		out("t1^"+defLinkText);
		for (int i=0;i<otherLinkIds.size();i++) out("^"+otherLinkIds.get(i));
		outl("");

		iter = textLinks.entrySet().iterator();
		while (iter.hasNext()) {
			Map.Entry entry = (Map.Entry)iter.next();
			Integer linkid = (Integer)entry.getKey();
			String[] s = (String[])entry.getValue();

			out(""+linkid);
			for (int i=0;i<s.length;i++) out("^"+s[i]);
			outl("");
		}
		*/




		reqQ.add("listLoad");

	}

	private static Map newMap(String key, Object val) {
		Map m = new HashMap();
		m.put(key, val);
		return m;
	}

	/*
	// Lister ut alle routere på topp-nivå og linker/vlan mellom dem
	static void listRouters2() throws SQLException
	{
		// listRouters, listRouterLinks, list
		//"select tilruter,id,speed,interf,gwip,bits,maxhosts,antmask,ospf from subnet where type='link' and ruter='" + nettel[i] + "' order by tilruter;");

		ResultSet rs = Database.query("select g0.boksid,b0.sysName,g0.interf,g1.boksid as tilboksid,b1.sysName as tilsysname,g1.interf from gwport as g0,gwport as g1,boks as b0,boks as b1 where g0.prefiksid=g1.prefiksid and g0.boksid!=g1.boksid and g0.boksid=b0.boksid and g1.boksid=b1.boksid order by g0.boksid");
		HashMap sysNames = new HashMap();
		ArrayList links = new ArrayList();
		ArrayList l=null;
		int curid=0;

		while (rs.next()) {
			if (rs.getInt(1)!=curid) {
				curid = rs.getInt(1);
				l = new ArrayList();
				l.add(new Integer(curid));
				links.add(l);
			}
			l.add(new Integer(rs.getInt("tilboksid")));
			sysNames.put(new Integer(curid), rs.getString("sysName"));
			sysNames.put(new Integer(rs.getInt("tilboksid")), rs.getString("tilsysName"));
		}

		outl("listRouters");
		Iterator iter = sysNames.entrySet().iterator();
		while (iter.hasNext()) {
			Map.Entry entry = (Map.Entry)iter.next();
			outl(entry.getKey() + "," + entry.getValue() );
		}

		outl("listRouterLinks");
		for (int i=0; i<links.size(); i++) {
			l = (ArrayList)links.get(i);
			out(""+l.get(0));
			for (int j=1; j<l.size(); j++) {
				out(","+l.get(j));
			}
			outl("");
		}
	}
	*/

	private static Map loadMap = new HashMap();
	private static void listLoad() throws SQLException
	{
		outl("---");
		try {
			out.flush();
			res.flushBuffer();
		} catch (IOException exp) {
			outl("IOException: " + exp);
		}

		try {
			for (Iterator it = loadMap.entrySet().iterator(); it.hasNext();) {
				Map.Entry me = (Map.Entry)it.next();
				String func = (String)me.getKey();
				Map m = (Map)me.getValue();
	
				if (func.equals("listBoxLoad")) listBoxLoad(m);
				if (func.equals("listLinkLoad")) listLinkLoad(m);
			}
		} catch (Exception e) {
			e.printStackTrace(new PrintStream(out));
		}
	}


	private static void listBoxLoad(Map hm)
	{
		outl("listBoxLoad");

		Set rrdNetboxid = (Set)hm.get("boxId");
		String datatype = (String)hm.get("datatype");

		Map m = getRRD(rrdNetboxid, datatype);
		for (Iterator it = m.entrySet().iterator(); it.hasNext();) {
			Map.Entry me = (Map.Entry)it.next();
			String netboxid = (String)me.getKey();
			Map fnMap = (Map)((Map)me.getValue()).get(datatype);
			outl(netboxid+"^"+fnMap.values().iterator().next());
		}
	}

	private static void listLinkLoad(Map hm) throws SQLException
	{
		outl("listLinkLoad");
		Set rrdGwId = (Set)hm.get("gwId");
		Set rrdSwId = (Set)hm.get("swId");
		Set rrdDualGwId = (Set)hm.get("dualGwId");
		Set rrdDualSwId = (Set)hm.get("dualSwId");

		if (rrdGwId == null) rrdGwId = new HashSet();
		if (rrdSwId == null) rrdSwId = new HashSet();
		if (rrdDualGwId == null) rrdDualGwId = new HashSet();

		String sqlAdd = "";
		Map swMap = new HashMap();
		Set gwSet = new HashSet();
		Set swId = new HashSet();
		if (!rrdGwId.isEmpty() || !rrdDualGwId.isEmpty()) {
			// Get RSM translation
			ResultSet rs = Database.query("select gwportid,swportid from gwport join gwportprefix using(gwportid) join prefix using(prefixid) join vlan using(vlanid) join module m1 on (gwport.moduleid=m1.moduleid) join swport on (substr(gwport.interface,5)=swport.vlan and swport.moduleid in (select moduleid from module where netboxid=gwport.to_netboxid)) join netbox using(netboxid) join type using(typeid) where typename='Cis-WX5302' and swport.link='y' and trunk='f' and gwportid in ("+concat(rrdGwId)+concat(rrdDualGwId)+") order by gwportid");

			while (rs.next()) {
				swId.add(rs.getString("swportid"));
				swMap.put(rs.getString("swportid"), rs.getString("gwportid"));
				gwSet.add(rs.getString("gwportid"));
			}
		}
		rrdSwId.addAll(swId);

		Map m = getRRD(null, "ifOutOctets", rrdGwId, rrdSwId);
		Map m2 = getRRD(null, new HashSet(Arrays.asList(new String[] { "ifOutOctets", "ifInOctets" })), rrdDualGwId, rrdDualSwId);

		Map[] mA = new Map[] { m, m2 };
		for (int k=0; k < mA.length; k++) {
			for (Iterator it = mA[k].entrySet().iterator(); it.hasNext();) {
				Map.Entry me = (Map.Entry)it.next();
				String netboxid = (String)me.getKey();
				Map ifMap = (Map)((Map)me.getValue()).values().iterator().next();
				for (Iterator ifIt = ifMap.entrySet().iterator(); ifIt.hasNext();) {
					me = (Map.Entry)ifIt.next();
					String[] ss = ((String)me.getKey()).split(":");
					String id = ss[1];
					if (swMap.containsKey(id)) id = (String)swMap.get(id);
					else if (gwSet.contains(id)) continue;
					outl(id+"^"+me.getValue());
				}
			}
		}
	}


	private static Map getRRD(Set netboxidS, String s) {
		return getRRD(netboxidS, s, null, null);
	}
	private static Map getRRD(Set netboxidS, String s, Set gwSet) {
		return getRRD(netboxidS, s, gwSet, null);
	}
	private static Map getRRD(Set netboxidS, String s, Set gwSet, Set swSet) {
		return getRRD(netboxidS, new HashSet(Arrays.asList(new String[] { s } )), gwSet, swSet, null);
	}
	private static Map getRRD(Set netboxidS, Set descrS, Set gwSet, Set swSet) {
		return getRRD(netboxidS, descrS, gwSet, swSet, null);
	}
	private static Map getRRD(Set netboxidS, Set descrS, Set gwSet, Set swSet, String sqlAdd) {
		if ((netboxidS == null || netboxidS.isEmpty()) &&
			(gwSet == null || gwSet.isEmpty()) &&
			(swSet == null || swSet.isEmpty()) &&
			sqlAdd == null) return new HashMap();

		try {
			String sql = "SELECT netboxid,descr,name,path,filename,key,value FROM rrd_file JOIN rrd_datasource USING(rrd_fileid) WHERE subsystem='cricket' AND descr IN ("+concat(descrS,"'")+")";
			if (netboxidS != null && !netboxidS.isEmpty()) sql += " AND netboxid IN ("+concat(netboxidS)+")";
			boolean g = gwSet != null && !gwSet.isEmpty();
			if (g) sql += " AND ((key='gwport' AND value IN ("+concat(gwSet, "'")+"))";
			if (swSet != null && !swSet.isEmpty()) sql += " " + (g?"OR":"AND") + " (key='swport' AND value IN ("+concat(swSet, "'")+"))";
			if (g) sql += ")";
			if (sqlAdd != null) sql += sqlAdd;
			ResultSet rs = Database.query(sql);

			Map fnMap = new HashMap();
			while (rs.next()) {
				String fn = rs.getString("path")+"/"+rs.getString("filename");
				List l;
				if ( (l=(List)fnMap.get(fn)) == null) {
					fnMap.put(fn, l = new ArrayList());
					l.add(new String[] { rs.getString("netboxid"), rs.getString("descr"), rs.getString("key"), rs.getString("value") } );
				}
				l.add(rs.getString("name"));
			}
			List f = new ArrayList();
			List ff = new ArrayList();
			for (Iterator it = fnMap.entrySet().iterator(); it.hasNext();) {
				Map.Entry me = (Map.Entry)it.next();
				String fn = "\"" + (String)me.getKey() + "\"";
				List l = (List)me.getValue();
				ff.add(l.remove(0));
				for (Iterator lIt = l.iterator(); lIt.hasNext();) {
					fn += " " + lIt.next();
				}
				f.add(fn);
			}
			List rrd = rrd(f);
			if (rrd.size() != f.size()) {
				outl("0^Error, rrd: " + rrd.size() + ", " + f.size());
				return new HashMap();
			}
			Map m = new HashMap();
			for (int i=0; i < rrd.size(); i++) {
				String rrdVal = (String)rrd.get(i);
				String[] rrdA = rrdVal.split(" ");
				if (!isNum(rrdA[0])) continue;
				String[] s = (String[])ff.get(i);
				String netboxid = s[0];
				String descr = s[1];
				String kv = s[2]+":"+s[3];
				Map m2;
				if ( (m2=(Map)m.get(netboxid)) == null) m.put(netboxid, m2 = new HashMap());

				Map m3;
				if ( (m3=(Map)m2.get(descr)) == null) m2.put(descr, m3 = new HashMap());

				if (rrdA.length > 1 && isNum(rrdA[1])) {
					rrdVal = rrdA[0] + "^" + rrdA[1];
				}					
				m3.put(kv, rrdVal);
			}
			return m;
		} catch (SQLException exp) {
			outl("SQLException: " + exp);
			exp.printStackTrace(new PrintStream(out));
		} catch (Exception exp) {
			outl("Exception: " + exp);
			exp.printStackTrace(new PrintStream(out));
		}
		return new HashMap();
	}

	private static boolean isNum(String s) {
		try {
			Double.parseDouble(s);
		} catch (NumberFormatException exp) {
			return false;
		}
		return true;
	}

	private static String concat(Set set) {
		return concat(set, "");
	}
	private static String concat(Set set, String fnut) {
		StringBuffer sb = new StringBuffer();
		for (Iterator it = set.iterator(); it.hasNext();) {
			Object s = (Object)it.next();
			sb.append(fnut+s+fnut);
			if (it.hasNext()) sb.append(",");
		}
		return sb.toString();
	}

	private static List rrd(List f)
	{
		List rrd = new ArrayList();
		try {
			String[] hostCmd = {
				Path.bindir + File.separatorChar + "vprrd.py",
			};

			Runtime rt = Runtime.getRuntime();
			Process p = rt.exec(hostCmd);
			PrintWriter out = new PrintWriter(p.getOutputStream());
			//out.println("/usr/local/nav/cricket/cricket-data/");
			out.println( ("max".equals(rrdType)?"MAX":"AVERAGE") );
			out.println(rrdTime);
			for (Iterator it = f.iterator(); it.hasNext();) {
				out.println(it.next());
			}
			out.close();

			BufferedReader in = new BufferedReader(new InputStreamReader(p.getInputStream()));
			try {
				p.waitFor();
			} catch (InterruptedException e) {
				System.err.println("InterruptedException: " + e);
				outl("InterruptedException: " + e);
				e.printStackTrace(System.err);
				return rrd;
			}
			String s;
			while ( (s=in.readLine()) != null) {
				s = s.trim();
				if (s.length() == 0) continue;
				rrd.add(s);
			}
		} catch (Exception e) {
			e.printStackTrace(new PrintStream(out));
		}
		return rrd;
	}
		

	static void listRouterGroups() throws SQLException
	{
		outl("listRouterGroups");

		// INSERT INTO vpBoksGrp (gruppeid,pboksid) VALUES ((SELECT gruppeid FROM vpBoksGrpInfo WHERE name='Kjernenett'), (SELECT boksid FROM boks WHERE sysName='ntnu-gw'));
		// INSERT INTO vpBoksGrp (gruppeid,pboksid) VALUES ((SELECT gruppeid FROM vpBoksGrpInfo WHERE name='Kjernenett'), (SELECT boksid FROM boks WHERE sysName='sb-gw'));
		// INSERT INTO vpBoksGrp (gruppeid,pboksid) VALUES ((SELECT gruppeid FROM vpBoksGrpInfo WHERE name='Kjernenett'), (SELECT boksid FROM boks WHERE sysName='rfb-gw'));
		// INSERT INTO vpBoksGrp (gruppeid,pboksid) VALUES ((SELECT gruppeid FROM vpBoksGrpInfo WHERE name='Kjernenett'), (SELECT boksid FROM boks WHERE sysName='hb-gw2'));
		// INSERT INTO vpBoksGrp (gruppeid,pboksid) VALUES ((SELECT gruppeid FROM vpBoksGrpInfo WHERE name='Kjernenett'), (SELECT boksid FROM boks WHERE sysName='kjemi-gw'));
		// INSERT INTO vpBoksGrp (gruppeid,pboksid) VALUES ((SELECT gruppeid FROM vpBoksGrpInfo WHERE name='Kjernenett'), (SELECT boksid FROM boks WHERE sysName='ed-gw2'));
		// INSERT INTO vpBoksGrp (gruppeid,pboksid) VALUES ((SELECT gruppeid FROM vpBoksGrpInfo WHERE name='Kjernenett'), (SELECT boksid FROM boks WHERE sysName='ntnu-gw2'));

		// INSERT INTO vpBoksGrp (gruppeid,pboksid) VALUES ((SELECT gruppeid FROM vpBoksGrpInfo WHERE name='Testnett'), (SELECT boksid FROM boks WHERE sysName='oslo-tn-gw2'));
		// INSERT INTO vpBoksGrp (gruppeid,pboksid) VALUES ((SELECT gruppeid FROM vpBoksGrpInfo WHERE name='Testnett'), (SELECT boksid FROM boks WHERE sysName='hb-gw6'));
		// INSERT INTO vpBoksGrp (gruppeid,pboksid) VALUES ((SELECT gruppeid FROM vpBoksGrpInfo WHERE name='Testnett'), (SELECT boksid FROM boks WHERE sysName='hb-gw5'));
		// INSERT INTO vpBoksGrp (gruppeid,pboksid) VALUES ((SELECT gruppeid FROM vpBoksGrpInfo WHERE name='Testnett'), (SELECT boksid FROM boks WHERE sysName='tyholt-gw3'));
		// INSERT INTO vpBoksGrp (gruppeid,pboksid) VALUES ((SELECT gruppeid FROM vpBoksGrpInfo WHERE name='Testnett'), (SELECT boksid FROM boks WHERE sysName='tyholt-gw'));
		// INSERT INTO vpBoksGrp (gruppeid,pboksid) VALUES ((SELECT gruppeid FROM vpBoksGrpInfo WHERE name='Testnett'), (SELECT boksid FROM boks WHERE sysName='stav-tn-gw2'));
		// INSERT INTO vpBoksGrp (gruppeid,pboksid) VALUES ((SELECT gruppeid FROM vpBoksGrpInfo WHERE name='Testnett'), (SELECT boksid FROM boks WHERE sysName='hb-gw7'));


		int curid=-1;
		//ResultSet rs = Database.query("SELECT gruppeid,name,pboksid FROM vpBoksGrpInfo NATURAL JOIN vpBoksGrp ORDER BY gruppeid");
		ResultSet rs = Database.query("SELECT vp_netbox_grp_infoid,name,hideicons,iconname,x,y,pnetboxid FROM vp_netbox_grp_info LEFT JOIN vp_netbox_grp USING (vp_netbox_grp_infoid) ORDER BY vp_netbox_grp_infoid");
		while (rs.next()) {
			if (rs.getInt("vp_netbox_grp_infoid")!=curid) {
				if (curid>=0) outl("");
				curid = rs.getInt("vp_netbox_grp_infoid");
				out(rs.getString("vp_netbox_grp_infoid") + "^" + rs.getString("name") + "^" + rs.getString("x") + "^" + rs.getString("y") + "^" + (rs.getBoolean("hideicons")?"true":"false") + "^" + rs.getString("iconname") );
				if (rs.getString("pnetboxid") == null) continue;
			}
			out("^" + rs.getString("pnetboxid"));
		}
		outl("");
	}

	static void listRouterXY() throws SQLException
	{
		outl("listRouterXY");

		String gruppeid = getp("gruppeid");
		if (gruppeid == null) return;

		ResultSet rs = Database.query("SELECT pnetboxid,x,y FROM vp_netbox_xy WHERE vp_netbox_grp_infoid = '" + gruppeid + "'");
		while (rs.next()) {
			outl(rs.getString("pnetboxid") + "^" + rs.getString("x") + "^" + rs.getString("y"));
		}
	}

	static void listBoks() throws SQLException
	{
		outl("listBoks");

		String thisBoksid = getp("boksid");
		String thisKat = getp("kat");
		if (thisBoksid == null) return;

		if (thisKat == null || thisKat.length() == 0) {
			// Må koste på oss et SQL kall ekstra
			ResultSet rs = Database.query("SELECT catid FROM netbox WHERE netboxid='"+Database.addSlashes(thisBoksid)+"'");
			if (!rs.next()) return; // boksid eksisterer ikke
			thisKat = rs.getString("catid");
		}

		ArrayList up = new ArrayList();
		ArrayList dn = new ArrayList();
		ArrayList link = new ArrayList();
		ArrayList linkInfo = new ArrayList();
		HashMap linkVlanMap = new HashMap();
		HashMap vlanNameMap = new HashMap();

		HashMap text = new HashMap();
		HashMap textOut = new HashMap();

		Set netboxidSet = new HashSet();
		Set rrdGwId = new HashSet();
		Set rrdSwId = new HashSet();

		// Vi har egentlig tre tilfeller her:
		// kat=gw -> vi henter info fra gwport og prefiks
		// kat=lan -> det er egentlig en switch vi skal vise, så vi må sjekke id'en for denne og så gå i swport
		// kat=<alt annet> -> Vi regner med at info finnes i swport

		if (thisKat.equalsIgnoreCase("gw")) {
			// Hent normalt fra gwport og prefiks
			// && = variabelnavn, ## = bytt ut med gitt verdi, !! = \n

			{
				String[] s = {
					"&&sysName!!Kat: ##!!Romid: ##!!Last: &&boksLast",
					"catid",
					"roomid"
				};
				text.put("gwBoks", s);
			}
			{
				String[] s = {
					"&&sysName!!Nettadr: ##",
					"netaddr",
				};
				text.put("lanBoks", s);
			}
			{
				String[] s = {
					"&&sysName!!Nettadr: ##",
					"netaddr",
				};
				text.put("stamBoks", s);
			}
			{
				String[] s = {
					"&&sysName!!Nettadr: ##",
					"netaddr",
				};
				text.put("defBoks", s);
			}

			// Linker
			{
				String[] s = {
					"&&sysNameFrom -> &&sysNameTo!!Interface: ##!!OSPF: ##!!Nettadr: ##!!Capacity: ##!!Last: &&linkLastPst (&&linkLast)!!(gw->gw)",
					"interface",
					"metric",
					"netaddr",
					"speed"
				};
				text.put("gw-gwLink", s);
			}
			{
				String[] s = {
					"&&sysNameFrom -> &&sysNameTo!!Interface: ##!!OSPF: ##!!Nettadr: ##!!Capacity: ##!!Last: &&linkLastPst (&&linkLast)!!(gw->stam)",
					"interface",
					"metric",
					"netaddr",
					"speed"
				};
				text.put("gw-stamLink", s);
			}
			{
				String[] s = {
					"&&sysNameFrom -> &&sysNameTo!!Interface: ##!!OSPF: ##!!Nettadr: ##!!Capacity: ##!!Last: &&linkLastPst (&&linkLast)!!(gw->lan)",
					"interface",
					"metric",
					"netaddr",
					"speed"
				};
				text.put("gw-lanLink", s);
			}
			{
				String[] s = {
					"&&sysNameFrom -> &&sysNameTo!!Interface: ##!!OSPF: ##!!Nettadr: ##!!Capacity: ##!!Last: &&linkLastPst (&&linkLast)!!(gw->def)",
					"interface",
					"metric",
					"netaddr",
					"speed"
				};
				text.put("gw-defLink", s);
			}
			{
				String[] s = {
					"&&sysNameFrom -> &&sysNameTo!!OSPF: ##!!Nettadr: ##!!Capacity: ##!!Last: &&linkLastPst (&&linkLast)!!(stam->gw)",
					"metric",
					"netaddr",
					"speed"
				};
				text.put("stam-gwLink", s);
			}
			{
				String[] s = {
					"&&sysNameFrom -> &&sysNameTo!!OSPF: ##!!Nettadr: ##!!Capacity: ##!!Last: &&linkLastPst (&&linkLast)!!(lan->gw)",
					"metric",
					"netaddr",
					"speed"
				};
				text.put("lan-gwLink", s);
			}
			{
				String[] s = {
					"&&sysNameFrom -> &&sysNameTo!!OSPF: ##!!Nettadr: ##!!Capacity: ##!!Last: &&linkLastPst (&&linkLast)!!(def->gw)",
					"metric",
					"netaddr",
					"speed"
				};
				text.put("def-gwLink", s);
			}
			{
				String[] s = {
					"gwportid: &&linkid!!&&sysNameFrom -> &&sysNameTo!!Kat: ##!!(def->def)",
					"catid",
				};
				text.put("def-defLink", s);
			}

			// Vi må vite hvilken kat en gitt boks er slik at vP kan oppgi dette når den spør om LAN'et
			HashMap boksKatMap = new HashMap();
			ResultSet rs = Database.query("SELECT netboxid,catid FROM netbox WHERE netboxid IN (SELECT to_netboxid FROM gwport JOIN gwportprefix USING(gwportid) WHERE prefixid IN (SELECT prefixid FROM gwport JOIN module USING(moduleid) JOIN gwportprefix USING(gwportid) WHERE netboxid='"+thisBoksid+"'))");
			while (rs.next()) boksKatMap.put(rs.getString("netboxid"), rs.getString("catid").toLowerCase());

			String cFields = "";
			{
				HashSet hs = new HashSet();
				String[] aa = { "gwportid", "netboxid", "sysName", "interface", "prefix.prefixid", "nettype", "netident", "catid", "vlan", "speed", "to_netboxid" };
				for (int i=0; i < aa.length; i++) hs.add(aa[i].toLowerCase());

				Iterator iter = text.entrySet().iterator();
				while (iter.hasNext()) {
					Map.Entry me = (Map.Entry)iter.next();
					String key = (String)me.getKey();
					textOut.put(key, new ArrayList());

					String[] s = (String[])me.getValue();
					for (int i=1;i<s.length;i++) if (hs.add(s[i].toLowerCase())) cFields += ","+s[i].toLowerCase();
				}
			}

			rs = Database.query("SELECT gwportid,netboxid,sysName,interface,prefix.prefixid,nettype,netident,catid,vlan,speed,to_netboxid"+cFields+" FROM gwport JOIN gwportprefix USING(gwportid) JOIN prefix USING(prefixid) JOIN vlan USING(vlanid) JOIN module USING(moduleid) JOIN netbox USING(netboxid) WHERE nettype NOT IN ('loopback','unknown') AND prefix.prefixid IN (SELECT prefixid FROM gwport JOIN module USING(moduleid) JOIN gwportprefix USING(gwportid) WHERE netboxid='"+thisBoksid+"') AND NOT (netboxid!='"+thisBoksid+"' AND nettype!='link') ORDER BY gwip");

			// NY
			// SELECT gwportid,boksid,sysName,interf,gwport.prefiksid,nettype,nettident,kat,vlan,speed,boksbak FROM (gwport JOIN prefiks USING (prefiksid)) JOIN boks USING (boksid) WHERE nettype NOT IN ('loopback','ukjent') AND gwport.prefiksid IN (SELECT prefiksid FROM gwport WHERE boksid='') AND NOT (boksid!='' AND nettype!='link') ORDER BY gwip

			// Gammel
			// SELECT gwportid,boksid,sysName,interf,gwport.prefiksid,nettype,nettident,kat,vlan,speed,boksbak FROM (gwport JOIN prefiks USING (prefiksid)) JOIN boks USING (boksid) WHERE nettype NOT IN ('loopback','ukjent') AND gwport.prefiksid IN (SELECT prefiksid FROM gwport WHERE boksid='') ORDER BY gwip


			//SELECT gwportid,boksid,sysName,gwport.prefiksid,nettype,nettident,kat,vlan,speed FROM (gwport JOIN prefiks USING (prefiksid)) JOIN boks USING (boksid) WHERE nettype NOT IN ('loopback','ukjent') AND gwport.prefiksid IN (SELECT prefiksid FROM gwport WHERE boksid='"+boksid+"'
			// SELECT gwportid,boksid,sysName,gwport.prefiksid,nettype,nettident FROM (gwport JOIN prefiks USING (prefiksid)) JOIN boks USING (boksid) WHERE nettype NOT IN ('loopback','ukjent') AND gwport.prefiksid IN (SELECT prefiksid FROM gwport WHERE boksid='549')
			// SELECT gwportid,boksid,sysName,gwport.prefiksid,nettype,nettident FROM (gwport JOIN prefiks USING (prefiksid)) JOIN boks USING (boksid) WHERE nettype NOT IN ('loopback','ukjent') AND gwport.prefiksid IN (204)
			// SELECT gwportid,boksid,sysName,gwport.prefiksid,nettype,nettident FROM (gwport JOIN prefiks USING (prefiksid)) JOIN  boks USING (boksid) WHERE nettype NOT IN ('loopback','ukjent') AND gwport.prefiksid IN (SELECT prefiksid FROM gwport WHERE  boksid='549' AND nettype='link') AND boksid !=549 ORDER BY prefiksid;
			//ArrayList linkList = new ArrayList();
			HashMap linkMap = new HashMap();
			HashSet boksDupe = new HashSet();
			while (rs.next()) {
				String gwportid = rs.getString("gwportid");
				String prefiksid = rs.getString("prefixid");
				String boksidTo = rs.getString("netboxid");
				String sysname = rs.getString("sysname");
				String katTo = rs.getString("catid").toLowerCase();
				String nettype = rs.getString("nettype");
				String boksbak = rs.getString("to_netboxid");
				String retning = "o"; // Up er default
				netboxidSet.add(boksidTo);

				// Først legger vi til boksen som den er for å være sikker på at den alltid kommer med
				if (boksDupe.add(boksidTo)) {
					if (!nettype.equals("link") && boksbak != null) {
						outl(boksidTo+"^"+sysname+"^"+katTo+"^"+boksbak+","+boksKatMap.get(boksbak));
					} else {
						outl(boksidTo+"^"+sysname+"^"+katTo);
					}

					// Legg til tekst for bokser
					String[] fields = (String[])text.get(katTo+"Boks");
					if (fields == null) fields = (String[])text.get("defBoks");
					if (fields == null) continue; // fail-safe

					ArrayList l = (ArrayList)textOut.get(katTo+"Boks");
					if (l == null) l = (ArrayList)textOut.get("defBoks");
					if (l == null) continue; // fail-safe

					String[] s = new String[fields.length];
					s[0] = boksidTo;
					for (int i=1;i<s.length;i++) s[i] = rs.getString(fields[i]);
					l.add(s);
				}

				// Har vi en ikke-link ut fra boksen så skriver vi om slik at boksen blir det vi har link til
				if (thisBoksid.equals(boksidTo) && !nettype.equals("link") ) {
					// lan, elink, stam eller tilsvarende. Nå skal det bare være en enkelt link, så vi bare skriver ut
					// og legger til linken.
					String nettident = rs.getString("netident");
					if (nettident == null) nettident = "(null)";
					if (nettident.indexOf("-fw") != -1) nettype = "fw";

					boksidTo = "-"+prefiksid;
					sysname = nettident;
					katTo = nettype;

				} else
				if (!nettype.equals("link")) continue;

				//if (katTo.equals("lan")) {
				if (!nettype.equals("link")) {
					if (!boksDupe.contains(boksidTo)) {
						//ArrayList l = (katTo.equals("lan")) ? dn : up;
						//retning = (katTo.equals("lan")) ? "n" : "o";
						if (katTo.equals("lan")) retning = "n";
						link.add(gwportid+"^"+gwportid+"^"+boksidTo);
					}
				} else {
					ArrayList l;
					if ( (l=(ArrayList)linkMap.get(prefiksid)) == null) linkMap.put(prefiksid, l=new ArrayList());
					// Linken ut skal komme først
					if (thisBoksid.equals(boksidTo)) {
						l.add(0, gwportid);
					} else {
						l.add(gwportid+"^"+boksidTo);
					}

					//up.add(gwportid+","+boksidTo);
				}

				// Hvis vi har fått en "ny" boks må vi evt. legge til boksinfo for den
				if (boksDupe.add(boksidTo)) {
					if (!nettype.equals("link") && boksbak != null) {
						outl(boksidTo+"^"+sysname+"^"+katTo+"^"+boksbak+","+boksKatMap.get(boksbak));
					} else {
						outl(boksidTo+"^"+sysname+"^"+katTo);
					}

					// Legg til tekst for bokser
					String[] fields = (String[])text.get(katTo+"Boks");
					if (fields == null) fields = (String[])text.get("defBoks");
					if (fields == null) continue; // fail-safe

					ArrayList l = (ArrayList)textOut.get(katTo+"Boks");
					if (l == null) l = (ArrayList)textOut.get("defBoks");
					if (l == null) continue; // fail-safe

					String[] s = new String[fields.length];
					s[0] = boksidTo;
					for (int i=1;i<s.length;i++) s[i] = rs.getString(fields[i]);
					l.add(s);
				}

				String[] linkInfoTo = { gwportid, rs.getString("speed"), rs.getString("interface") };
				linkInfo.add(linkInfoTo);
				{
					ArrayList l = new ArrayList();
					l.add(rs.getString("vlan")+","+retning);
					linkVlanMap.put(gwportid, l);
				}

				// Legg til tekst for linker
				{
					String[] fields = (String[])text.get("gw-"+katTo+"Link");
					if (fields == null) fields = (String[])text.get("gw-defLink");
					if (fields == null) continue; // fail-safe

					ArrayList l = (ArrayList)textOut.get("gw-"+katTo+"Link");
					if (l == null) l = (ArrayList)textOut.get("gw-defLink");
					if (l == null) continue; // fail-safe

					String[] s = new String[fields.length];
					s[0] = gwportid;
					for (int i=1;i<s.length;i++) s[i] = rs.getString(fields[i]);

					l.add(s);
				}

				if (!nettype.equals("link")) {
					// Vi må også legge til tekst for linken andre veien
					String[] fields = (String[])text.get(katTo+"-"+thisKat+"Link");
					if (fields == null) fields = (String[])text.get(katTo+"-defLink");
					if (fields == null) fields = (String[])text.get("def-defLink");
					if (fields == null) continue; // fail-safe

					ArrayList l = (ArrayList)textOut.get(katTo+"-"+thisKat+"Link");
					if (l == null) l = (ArrayList)textOut.get(katTo+"-defLink");
					if (l == null) l = (ArrayList)textOut.get("def-defLink");
					if (l == null) continue; // fail-safe

					String[] s = new String[fields.length];
					s[0] = "-"+gwportid;
					for (int i=1;i<s.length;i++) s[i] = rs.getString(fields[i]);

					l.add(s);
				}

			}

			// Nå går vi gjennom linkMap og legger inn linkene, der det er to gwportid'er per link
			Iterator iter = linkMap.values().iterator();
			while (iter.hasNext()) {
				ArrayList l = (ArrayList)iter.next();
				if (l.size() < 2) continue;
				String gwportid1 = (String)l.get(0);
				String gwportid2 = (String)l.get(1);
				link.add(gwportid1+"^"+gwportid2);
			}


		} else
		if (thisKat.equalsIgnoreCase("lan")) {
			// Først må vi vite id


		} else {
			// Henter fra swport
			// && = variabelnavn, ## = bytt ut med gitt verdi, !! = \n

			{
				String[] s = {
					"&&sysName!!Kat: ##!!Romid: ##!!Bakplan: &&boksLast",
					"catid",
					"roomid"
				};
				text.put("swBoks", s);
			}
			{
				String[] s = {
					"&&sysName!!Kat: ##!!Romid: ##!!Last: &&boksLast",
					"catid",
					"roomid"
				};
				text.put("gwBoks", s);
			}
			{
				String[] s = {
					"&&sysName!!Kat: ## (kant)",
					"catid"
				};
				text.put("kantBoks", s);
			}
			{
				String[] s = {
					"&&sysName!!Kat: ## (srv)",
					"catid"
				};
				text.put("srvBoks", s);
			}
			{
				String[] s = {
					"&&sysName!!(hub)"
				};
				text.put("hubBoks", s);
			}
			{
				String[] s = {
					"&&sysName!!(def)",
				};
				text.put("defBoks", s);
			}

			// Linker
			{
				String[] s = {
					"&&sysNameFrom -> &&sysNameTo!!MP: ##/##!!Speed: ##!!Duplex: ##!!Portnavn: ##!!Last: &&linkLastPst (&&linkLast)!!(sw->sw)",
					"module",
					"port",
					"speed",
					"duplex",
					"portname"
				};
				text.put("sw-swLink", s);
			}
			{
				String[] s = {
					"&&sysNameFrom -> &&sysNameTo!!MP: ##/##!!Speed: ##!!Duplex: ##!!Portnavn: ##!!Last: &&linkLastPst (&&linkLast)!!(sw->gw)",
					"module",
					"port",
					"speed",
					"duplex",
					"portname"
				};
				text.put("sw-gwLink", s);
			}
			{
				String[] s = {
					"&&sysNameFrom -> &&sysNameTo!!MP: ##/##!!Speed: ##!!Duplex: ##!!Portnavn: ##!!Last: &&linkLastPst (&&linkLast)!!(sw->kant)",
					"module",
					"port",
					"speed",
					"duplex",
					"portname"
				};
				text.put("sw-kantLink", s);
			}
			{
				String[] s = {
					"&&sysNameFrom -> &&sysNameTo!!MP: ##/##!!Speed: ##!!Duplex: ##!!Portnavn: ##!!Last: &&linkLastPst (&&linkLast)!!(sw->hub)",
					"module",
					"port",
					"speed",
					"duplex",
					"portname"
				};
				text.put("sw-hubLink", s);
			}
			{
				String[] s = {
					"&&sysNameFrom -> &&sysNameTo!!MP: ##/##!!Speed: ##!!Duplex: ##!!Portnavn: ##!!Last: &&linkLastPst (&&linkLast)!!(sw->srv)",
					"module",
					"port",
					"speed",
					"duplex",
					"portname"
				};
				text.put("sw-srvLink", s);
			}
			{
				String[] s = {
					"&&sysNameFrom -> &&sysNameTo!!MP: ##/##!!Speed: ##!!Duplex: ##!!Portnavn: ##!!Last: &&linkLastPst (&&linkLast)!!(sw->mas)",
					"module",
					"port",
					"speed",
					"duplex",
					"portname"
				};
				text.put("sw-masLink", s);
			}
			{
				String[] s = {
					"&&sysNameFrom -> &&sysNameTo!!Speed: ##!!Last: &&linkLastPst (&&linkLast)!!(gw->sw)",
					"speed"
				};
				text.put("gw-swLink", s);
			}
			{
				String[] s = {
					"&&sysNameFrom -> &&sysNameTo!!MP: ##/##!!Speed: ##!!Duplex: ##!!Portnavn: ##!!Last: &&linkLastPst (&&linkLast)!!(kant->sw)",
					"module",
					"port",
					"speed",
					"duplex",
					"portname"
				};
				text.put("kant-swLink", s);
			}
			{
				String[] s = {
					"&&sysNameFrom -> &&sysNameTo!!Speed: ##!!Last: &&linkLastPst (&&linkLast)!!(def-def)",
					"speed"
				};
				text.put("def-defLink", s);
			}

			// Hent høyste boksid
			ResultSet rs = Database.query("SELECT MAX(netboxid) AS maxboksid FROM netbox");
			rs.next();
			int maxBoksid = rs.getInt("maxboksid");

			// Vi trenger å vite hvilken gw som er rootgw for et gitt prefiks
			//rs = Database.query("SELECT boksid FROM prefiks JOIN gwport ON (rootgwid=gwportid)");

			// Vi trenger kobling mellom boksid og kat for å vite hvilken tekst som skal på en link ut fra senter-enheten
			HashMap boksidKatMap = new HashMap();
			rs = Database.query("SELECT netboxid,catid FROM netbox WHERE netboxid IN (SELECT netboxid FROM module JOIN swport USING (moduleid) WHERE to_netboxid="+thisBoksid+")");
			while (rs.next()) boksidKatMap.put(rs.getString("netboxid"), rs.getString("catid").toLowerCase() );

			// Felter fra gw'er som skal med
			String cFields = "";
			{
				HashSet hs = new HashSet();
				String[] aa = { "netboxid", "sysName" };
				for (int i=0; i < aa.length; i++) hs.add(aa[i].toLowerCase());

				Iterator iter = text.entrySet().iterator();
				while (iter.hasNext()) {
					Map.Entry me = (Map.Entry)iter.next();
					String key = (String)me.getKey();
					if (!key.equals("gwBoks")) continue;
					textOut.put(key, new ArrayList());

					String[] s = (String[])me.getValue();
					for (int i=1;i<s.length;i++) if (hs.add(s[i])) cFields += ","+s[i];
				}
			}
			// Hent alle bokser ut som er gw
			HashSet boksDupe = new HashSet();
			HashSet linkDupe = new HashSet();
			HashSet gwboksSet = new HashSet();
			rs = Database.query("SELECT netboxid,sysName"+cFields+" FROM netbox WHERE catid='GW' AND netboxid IN (SELECT netboxid FROM module JOIN gwport USING(moduleid) WHERE to_netboxid='"+thisBoksid+"')");
			// SELECT boksid,sysName FROM boks WHERE kat='GW' AND boksid IN (SELECT boksbak FROM swport WHERE boksid='')
			while (rs.next()) {
				String boksid = rs.getString("netboxid");
				String sysname = rs.getString("sysname");
				String kat = rs.getString("catid").toLowerCase();

				outl(boksid+"^"+sysname+"^"+kat);

				// Legg til tekst for bokser
				String[] fields = (String[])text.get(kat+"Boks");
				if (fields == null) fields = (String[])text.get("defBoks");
				if (fields == null) continue; // fail-safe

				ArrayList l = (ArrayList)textOut.get(kat+"Boks");
				if (l == null) l = (ArrayList)textOut.get("defBoks");
				if (l == null) continue; // fail-safe

				String[] s = new String[fields.length];
				s[0] = boksid;
				for (int i=1;i<s.length;i++) s[i] = rs.getString(fields[i]);
				l.add(s);
				gwboksSet.add(boksid);
				boksDupe.add(boksid);
			}

			// Så er det resten, da har vi info om linken også, så legg til alle felter vi skal ha med
			cFields = "";
			{
				HashSet hs = new HashSet();
				String[] aa = { "swportid", "netboxid", "sysName", "catid", "module", "port", "vlan.vlan", "speed", "direction", "to_netboxid", "portname", "nettype", "netident" };
				for (int i=0; i < aa.length; i++) hs.add(aa[i].toLowerCase());

				Iterator iter = text.entrySet().iterator();
				while (iter.hasNext()) {
					Map.Entry me = (Map.Entry)iter.next();
					String key = (String)me.getKey();
					if (key.equals("gwBoks")) continue;
					textOut.put(key, new ArrayList());

					String[] s = (String[])me.getValue();
					for (int i=1;i<s.length;i++) if (hs.add(s[i])) cFields += ","+s[i];
				}
			}

			// Så henter vi alle bokser vi må eksplistitt hente info fra boks for
			// SELECT * da vi ikke vet hva som skal være med
			HashSet boksSet = new HashSet();
			rs = Database.query("SELECT * FROM netbox WHERE netboxid IN (SELECT netboxid FROM module JOIN swport USING(moduleid) WHERE netboxid="+thisBoksid+") AND netboxid NOT IN (SELECT netboxid FROM module JOIN swport USING(moduleid) WHERE to_netboxid="+thisBoksid+")");
			while (rs.next()) {
				String boksid = rs.getString("netboxid");
				String sysname = rs.getString("sysname");
				String kat = rs.getString("catid").toLowerCase();

				outl(boksid+"^"+sysname+"^"+kat);

				// Legg til tekst for bokser
				String[] fields = (String[])text.get(kat+"Boks");
				if (fields == null) fields = (String[])text.get("defBoks");
				if (fields == null) continue; // fail-safe

				ArrayList l = (ArrayList)textOut.get(kat+"Boks");
				if (l == null) l = (ArrayList)textOut.get("defBoks");
				if (l == null) continue; // fail-safe

				String[] s = new String[fields.length];
				s[0] = boksid;
				for (int i=1;i<s.length;i++) s[i] = rs.getString(fields[i]);
				l.add(s);
				boksidKatMap.put(boksid, kat);
				boksSet.add(boksid);
			}

			//rs = Database.query("SELECT swportid,boksid,sysName,kat,vlan,speed,retning,boksbak"+cFields+" FROM swport JOIN boks USING (boksid) JOIN swportvlan USING (swportid) WHERE status!='down' AND boksbak IS NOT NULL AND (boksid='"+thisBoksid+"' OR boksbak='"+thisBoksid+"')");
			rs = Database.query("SELECT swportid,netboxid,sysName,catid,module,port,vlan.vlan,speed,direction,to_netboxid,portname,nettype,netident"+cFields+" FROM swport JOIN module USING(moduleid) JOIN netbox USING(netboxid) JOIN swportvlan USING (swportid) JOIN vlan USING(vlanid) LEFT JOIN prefix USING (vlanid) WHERE netbox.up!='n' AND (netboxid='"+thisBoksid+"' OR to_netboxid='"+thisBoksid+"') ORDER BY vlan.vlan");
			//SELECT DISTINCT ON (vlan,boksid,boksbak) swportid,boksid,sysName,kat,vlan,speed,retning,boksbak,vpkatbak,portnavn,nettype,nettident FROM swport JOIN boks USING (boksid) JOIN swportvlan USING (swportid) LEFT JOIN prefiks USING (vlan) WHERE status!='down' AND (boksid='' OR boksbak='') ORDER BY vlan

			//SELECT DISTINCT ON (vlan,boksid,boksbak) swportid,boksid,sysName,kat,trunk,boksbak,vlan,retning,vpkatbak,nettype,nettident FROM swport JOIN boks USING (boksid) JOIN swportvlan USING (swportid) LEFT JOIN prefiks USING (vlan) WHERE status!='down' AND (boksid='16' OR boksbak='16') and boksbak IN (1,28) ORDER BY vlan,boksbak;

			HashMap linkMap = new HashMap();
			ArrayList noInfoBoksL = new ArrayList();
			while (rs.next()) {
				String swportid = rs.getString("swportid");
				String boksid = rs.getString("netboxid");
				String sysname = rs.getString("sysname");
				String kat = rs.getString("catid").toLowerCase();
				String vlan = rs.getString("vlan");
				//String retning = rs.getString("retning");
				String boksbak = rs.getString("to_netboxid");
				boolean boksbakNull = (boksbak==null) ? true : false;

				String katBak;
				if (thisBoksid.equals(boksid)) {
					// Link ut fra enheten, så vi må endre kat
					if (boksbak == null) {
						String[] katSysname = decodeBoksbak(null, rs.getString("portname"));
						katBak = katSysname[0];
						String boksidBak = String.valueOf(++maxBoksid);
						boksbak = boksidBak;
						String sysnameBak =katSysname[1];
						outl(boksidBak+"^"+sysnameBak+"^"+katBak);

						// Vi må også legge til tekst for enheten
						String[] fields = (String[])text.get(katBak+"Boks");
						if (fields == null) fields = (String[])text.get("defBoks");
						if (fields == null) continue; // fail-safe

						ArrayList l = (ArrayList)textOut.get(katBak+"Boks");
						if (l == null) l = (ArrayList)textOut.get("defBoks");
						if (l == null) continue; // fail-safe

						String[] s = new String[fields.length];
						s[0] = boksidBak;
						for (int i=1;i<s.length;i++) s[i] = rs.getString(fields[i]);
						l.add(s);

					} else {
						katBak = (String)boksidKatMap.get(boksbak);
					}
				} else {
					katBak = thisKat;
				}

				// Legg til vlan
				if (!vlanNameMap.containsKey(vlan)) {
					vlanNameMap.put(vlan, rs.getString("nettype")+","+rs.getString("netident"));
				}

				// Legg evt. til boksen
				if (boksDupe.add(boksid)) {
					outl(boksid+"^"+sysname+"^"+kat);

					// Legg til tekst for bokser
					String[] fields = (String[])text.get(kat+"Boks");
					if (fields == null) fields = (String[])text.get("defBoks");
					if (fields == null) continue; // fail-safe

					ArrayList l = (ArrayList)textOut.get(kat+"Boks");
					if (l == null) l = (ArrayList)textOut.get("defBoks");
					if (l == null) continue; // fail-safe

					String[] s = new String[fields.length];
					s[0] = boksid;
					for (int i=1;i<s.length;i++) s[i] = rs.getString(fields[i]);
					l.add(s);
				}

				// Så sjekker vi linken
				if (linkDupe.add(swportid)) {
					String key = (thisBoksid.equals(boksid)) ? boksbak : boksid;
					// Vi lagrer linker per vlan, da det kan være flere fysiske linker mellom to enheter, men
					// de vil alltid være på forskjellig vlan
					key += ":"+vlan;

					// Legg til selve linken, litt styr fordi begge swportid'ene skal være med i samme link ut fra midten
					{
						ArrayList l;
						if ( (l=(ArrayList)linkMap.get(key)) == null) linkMap.put(key, l=new ArrayList());
						// Linken ut skal komme først
						if (thisBoksid.equals(boksid)) {
							//l.add(0, retning);
							l.add(0, swportid);
							l.add(1, boksbak);
						} else {
							l.add(swportid+"^"+boksid);
						}
					}

					String[] linkInfoTo = { swportid, rs.getString("speed"), rs.getString("module")+"_"+rs.getString("port") };
					linkInfo.add(linkInfoTo);

					// Legg til tekst for vanlige linker
					{
						/*
						String k1,k2;
						if (thisBoksid.equals(boksid)) {
							// Fra senter og ut
							k1 = thisKat;
							k2 = kat;
						} else {
							// Inn mot senter
							k1 = kat;
							k2 = thisKat;
						}
						*/

						String[] fields = (String[])text.get(kat+"-"+katBak+"Link");
						if (fields == null) fields = (String[])text.get(kat+"-defLink");
						if (fields == null) fields = (String[])text.get("def-defLink");
						if (fields == null) continue; // fail-safe

						ArrayList l = (ArrayList)textOut.get(kat+"-"+katBak+"Link");
						if (l == null) l = (ArrayList)textOut.get(kat+"-defLink");
						if (l == null) l = (ArrayList)textOut.get("def-defLink");
						if (l == null) continue; // fail-safe

						String[] s = new String[fields.length];
						s[0] = swportid;
						for (int i=1;i<s.length;i++) s[i] = rs.getString(fields[i]);

						l.add(s);
					}

					// Spesialtilfelle der vi kun har linken en vei, dvs. boksbak er null eller det er srv, mas eller noe annet
					// der boksbak er definert
					// Dette er da linken inn mot senter
					if (boksbakNull || boksSet.contains(boksbak)) {

						String[] fields = (String[])text.get(katBak+"-"+thisKat+"Link");
						if (fields == null) fields = (String[])text.get(katBak+"-defLink");
						if (fields == null) fields = (String[])text.get("def-defLink");
						if (fields == null) continue; // fail-safe

						ArrayList l = (ArrayList)textOut.get(katBak+"-"+thisKat+"Link");
						if (l == null) l = (ArrayList)textOut.get(katBak+"-defLink");
						if (l == null) l = (ArrayList)textOut.get("def-defLink");
						if (l == null) continue; // fail-safe

						String[] s = new String[fields.length];
						s[0] = "-"+swportid;
						for (int i=1;i<s.length;i++) s[i] = rs.getString(fields[i]);

						l.add(s);
					}

					// Spesialtilfelle for link gw->sw
					if (gwboksSet.contains(boksbak)) {
						String[] fields = (String[])text.get("gw-"+thisKat+"Link");
						if (fields == null) fields = (String[])text.get("gw-defLink");
						if (fields == null) fields = (String[])text.get("def-defLink");
						if (fields == null) continue; // fail-safe

						ArrayList l = (ArrayList)textOut.get("gw-"+thisKat+"Link");
						if (l == null) l = (ArrayList)textOut.get("gw-defLink");
						if (l == null) l = (ArrayList)textOut.get("def-defLink");
						if (l == null) continue; // fail-safe

						String[] s = new String[fields.length];
						s[0] = "-"+swportid;
						for (int i=1;i<s.length;i++) s[i] = rs.getString(fields[i]);

						l.add(s);
					}

				}

				// Legg til vlan for linken
				{
					ArrayList l;
					if ( (l=(ArrayList)linkVlanMap.get(swportid)) == null) linkVlanMap.put(swportid, l=new ArrayList());
					String retning = rs.getString("direction");
					if (!retning.equals("o") && !retning.equals("b")) retning = "n";
					l.add(rs.getString("vlan")+","+retning);
				}

			}

			// Nå går vi gjennom linkMap og legger inn linkene, det er to swportid'er per link
			Iterator iter = linkMap.values().iterator();
			while (iter.hasNext()) {
				String retning, swportidUt, swportidInn;
				ArrayList l = (ArrayList)iter.next();
				if (l.size() == 2) {
					// Nå har vi det tilfellet der vi har har funnet linken ut, det skjer for uplink til gw
					// og for endel servere
					// Vi har retning og swportid på ene siden, men vi bruker også den samme id'en andre veien da
					// last hentes bare fra ene siden
					//retning = (String)l.get(0);
					swportidUt = (String)l.get(0);
					String boksbak = (String)l.get(1);
					swportidInn = swportidUt+"^"+boksbak;
					// Vi har imidlertid ingen info, så legg enheten til en liste over enheter vi må hente info for, fra gwport
					//gwboksL.add(boksbak);
				} else if (l.size() < 3) {
					continue;
				} else {
					//retning = (String)l.get(0);
					swportidUt = (String)l.get(0);
					swportidInn = (String)l.get(2);
				}
				String linkS = swportidUt+"^"+swportidInn;
				link.add(linkS);
				/*
				if (retning.equals("o")) {
					up.add(linkS);
				}
				else {
					dn.add(linkS);
				}
				*/

			}

			/*
			StringBuffer sb = new StringBuffer();
			for (int i=0; i < gwboksL.size(); i++) {
				String boksid = (String)gwboksL.get(i);
				sb.append(boksid);
				if (i != gwboksL.size()-1) sb.append(",");
			}
			String sql = "SELECT * FROM gwport JOIN boks USING (boksid) WHERE boksbak='"+thisBoksid+"' AND boksid = (SELECT boksbak FROM swport WHERE swportid IN ("+sb+"))";
			outl("gwport: " + sql);
			*/



		}

		{
			Map newMap = new HashMap();
			netboxidSet.add(thisBoksid);

			newMap.put("boxId", netboxidSet);
			newMap.put("datatype", "c5000Bandwidth");
			loadMap.put("listBoxLoad", newMap);
		}

		// Så skrives linkene ut
		outl("listBoksLinks");
		Set linkIdSet = new HashSet();
		for (int i=0; i < link.size(); i++) {
			outl((String)link.get(i) );
			linkIdSet.add( ((String)link.get(i)).split("\\^")[0] );
		}

		{
			Map newMap = new HashMap();
			newMap.put("cn", thisBoksid);
			if (thisKat.equalsIgnoreCase("gw")) rrdGwId.addAll(linkIdSet);
			else rrdSwId.addAll(linkIdSet);

			newMap.put("dualGwId", rrdGwId);
			newMap.put("dualSwId", rrdSwId);
			loadMap.put("listLinkLoad", newMap);
		}

		/*
		out("up");
		for (int i=0; i < up.size(); i++) out("^"+up.get(i) );
		outl("");

		outl("hz^");
		out("dn");
		for (int i=0; i < dn.size(); i++) out("^"+dn.get(i) );
		outl("");
		*/

		outl("listBoksLinkInfo");
		for (int i=0; i < linkInfo.size(); i++) {
			String[] linkInfoTo = (String[])linkInfo.get(i);
			out(linkInfoTo[0]);
			for (int j=1; j < linkInfoTo.length; j++) {
				out("^"+linkInfoTo[j]);
			}
			outl("");
		}

		outl("listLinkVlans");
		{
			Iterator iter = linkVlanMap.entrySet().iterator();
			while (iter.hasNext()) {
				Map.Entry me = (Map.Entry)iter.next();
				String linkId = (String)me.getKey();
				ArrayList l = (ArrayList)me.getValue();

				out(linkId);
				for (int i=0; i < l.size(); i++) {
					String linkVlanTo = (String)l.get(i);
					out("^"+linkVlanTo);
				}
				outl("");
			}
		}

		if (!vlanNameMap.isEmpty()) {
			outl("listVlanNames");
			Iterator iter = vlanNameMap.entrySet().iterator();
			while (iter.hasNext()) {
				Map.Entry me = (Map.Entry)iter.next();
				String vlan = (String)me.getKey();
				String vlanName = (String)me.getValue();
				outl(vlan+"^"+vlanName);
			}
		}

		String[] types = {
			"Boks",
			"Link"
		};
		for (int typ=0; typ < types.length; typ++) {
			outl("list"+types[typ]+"Text");
			int tcnt=0;
			Iterator iter = textOut.entrySet().iterator();
			while (iter.hasNext()) {
				Map.Entry me = (Map.Entry)iter.next();
				String key = (String)me.getKey();
				if (!key.endsWith(types[typ])) continue;
				ArrayList l = (ArrayList)me.getValue();

				String txt = ((String[])text.get(key))[0];
				out("t"+tcnt+"^"+txt);
				for (int i=0; i < l.size(); i++) out("^"+((String[])l.get(i))[0]);
				outl("");
				for (int i=0; i < l.size(); i++) {
					String[] s = (String[])l.get(i);
					out(s[0]);
					for (int j=1; j < s.length; j++) out("^"+s[j]);
					outl("");
				}
				tcnt++;
			}
		}
		reqQ.add("listLoad");
	}

	// Henter ut sysname og kat ved å se på vpkatbak og portnavn
	// Er vpkatbak definert brukes den, ellers brukers portnavn, det
	// skilles da på ":". Eksisterer ikke denne sjekker det for komma-notasjon
	private static String[] decodeBoksbak(String vpkatbak, String portnavn)
	{
		String kat = vpkatbak;
		if (portnavn == null || portnavn.length() == 0) portnavn = "<undef>";
		StringTokenizer st = new StringTokenizer(portnavn, ":");
		if (st.countTokens() > 1) {
			String s = st.nextToken();
			if (kat == null) kat = s;
		}
		String sysname = st.nextToken();
		while (st.hasMoreTokens()) sysname += st.nextToken();

		if (kat != null && kat.charAt(0) == 'n') {
			st = new StringTokenizer(sysname, ",");
			if (st.countTokens() >= 2) kat = "hub";
		}
		if (kat == null) kat = "undef";

		String[] s = { kat, sysname };
		return s;
	}

	// Helper methods
	private static String getp(String s) { return req.getParameter(s); }
	private static void out(String s)
	{
		try {
			out.print(s);
		} catch (IOException e) {}
	}
	private static void outl(String s)
	{
		try {
			out.println(s);
		} catch (IOException e) {}
	}

	private static HashMap getHashFromResultSet(ResultSet rs, ResultSetMetaData md) throws SQLException
	{
		HashMap hm = new HashMap();
		for (int i=md.getColumnCount(); i > 0; i--) {
			hm.put(md.getColumnName(i), rs.getString(i));
		}
		return hm;
	}

}

class SqlAdmin
{
	public static HttpServletRequest req;
	public static ServletOutputStream out;

	static void serviceRequest(String[] reqA, String user) throws IOException
	{
		LinkedList reqQ = new LinkedList();
		reqQ.addAll(Arrays.asList(reqA));

		while (!reqQ.isEmpty()) {
			String req = (String)reqQ.removeFirst();

			try {
				if (req.equals("verifyPw")) return;
				else if (req.equals("saveBoksXY")) saveBoksXY(user);
				else outl("Unsupported request string: " + req);

			} catch (SQLException e) {
				out.println("SQLException: " + e.getMessage());
			}
		}
	}


	static void saveBoksXY(String user) throws SQLException
	{
		String gruppeid = getp("gruppeid");
		String boks = getp("boks");

		if (gruppeid == null || boks == null) return;
		// Vi må være sikker på at gruppeid er et tall
		try {
			Integer.parseInt(gruppeid);
		} catch (NumberFormatException e) {
			//outl("false: Gruppeid is not a valid number: " + gruppeid);
			return;
		}

		HashMap boksXYMap = new HashMap();
		ResultSet rs = Database.query("SELECT pnetboxid,x,y FROM vp_netbox_xy WHERE vp_netbox_grp_infoid='"+gruppeid+"'");
		while (rs.next()) {
			int[] xy = { rs.getInt("x"), rs.getInt("y") };
			boksXYMap.put(rs.getString("pnetboxid"), xy);
		}

		int newcnt=0,updcnt=0,remcnt=0;
		StringTokenizer st = new StringTokenizer(boks, "*");
		while (st.hasMoreTokens()) {
			String boksXY = st.nextToken();
			StringTokenizer boksSt = new StringTokenizer(boksXY, ",");
			if (boksSt.countTokens() != 3) continue;

			String boksid = boksSt.nextToken();
			int x = Integer.parseInt(boksSt.nextToken());
			int y = Integer.parseInt(boksSt.nextToken());

			int[] xy;
			if ( (xy = (int[])boksXYMap.remove(boksid)) != null) {
				if (xy[0] != x || xy[1] != y) {
					// Må oppdatere
					String[] updateFields = {
						"x", String.valueOf(x),
						"y", String.valueOf(y)
					};
					String[] condFields = {
						"pnetboxid", boksid,
						"vp_netbox_grp_infoid", gruppeid
					};
					Database.update("vp_netbox_xy", updateFields, condFields);
					updcnt++;
				}
			} else {
				// Må sette inn
				String[] insertFields = {
					"pnetboxid", boksid,
					"x", String.valueOf(x),
					"y", String.valueOf(y),
					"vp_netbox_grp_infoid", gruppeid
				};
				Database.insert("vp_netbox_xy", insertFields);
				newcnt++;
			}
		}

		Iterator iter = boksXYMap.keySet().iterator();
		while (iter.hasNext()) {
			String boksid = (String)iter.next();

			String sql = "DELETE FROM vp_netbox_xy WHERE pnetboxid='"+boksid+"' AND vp_netbox_grp_infoid='"+gruppeid+"'";
			//Database.update(sql);
			//remcnt++;
		}
		if (newcnt > 0 || updcnt > 0 || remcnt > 0) {
			//outl("true: New: " + newcnt + " Upd: " +updcnt + " Rem: " + remcnt);
			Database.commit();
		}

		if (gruppeid.equals("0")) {
			int grpcnt=0;
			String gruppe = getp("gruppe");
			if (gruppe == null) return;

			HashMap grpXYMap = new HashMap();
			rs = Database.query("SELECT vp_netbox_grp_infoid,x,y FROM vp_netbox_grp_info");
			while (rs.next()) {
				int[] xy = { rs.getInt("x"), rs.getInt("y") };
				grpXYMap.put(rs.getString("vp_netbox_grp_infoid"), xy);
			}

			st = new StringTokenizer(gruppe, "*");
			while (st.hasMoreTokens()) {
				String gruppeXY = st.nextToken();
				StringTokenizer grpSt = new StringTokenizer(gruppeXY, ",");
				if (grpSt.countTokens() != 3) continue;

				String grpid = grpSt.nextToken();
				int x = Integer.parseInt(grpSt.nextToken());
				int y = Integer.parseInt(grpSt.nextToken());

				int[] xy;
				if ( (xy = (int[])grpXYMap.get(grpid)) != null) {
					if (xy[0] != x || xy[1] != y) {
						// Må oppdatere
						String[] updateFields = {
							"x", String.valueOf(x),
							"y", String.valueOf(y)
						};
						String[] condFields = {
							"vp_netbox_grp_infoid", grpid
						};
						Database.update("vp_netbox_grp_info", updateFields, condFields);
						grpcnt++;
					}
				}
			}
			if (grpcnt > 0) Database.commit();
		}


	}


	// Helper methods
	private static String getp(String s) { return req.getParameter(s); }
	private static void out(String s)
	{
		try {
			out.print(s);
		} catch (IOException e) {}
	}
	private static void outl(String s)
	{
		try {
			out.println(s);
		} catch (IOException e) {}
	}
	private static HashMap getHashFromResultSet(ResultSet rs, ResultSetMetaData md) throws SQLException
	{
		HashMap hm = new HashMap();
		for (int i=md.getColumnCount(); i > 0; i--) {
			hm.put(md.getColumnName(i), rs.getString(i));
		}
		return hm;
	}

}

/*
class sqlNettel
{
	Com com;
	Sql db;

	// felles data mellom metodene
	String[] up;
	String[] hz;
	String[] dn;
	boolean gw = false;

	Vector idV = new Vector();
	Vector linkV = new Vector();
	Vector utFraSwitch = new Vector();
	Vector utFraRouter = new Vector();

	Vector linkLast;

	DbCnf cnf;
	HashMap textNettel = new HashMap();
	HashMap textLink = new HashMap();


	public sqlNettel(Com InCom)
	{
		com = InCom;
		db = com.getDb();

		cnf = new DbCnf(com);
	}

	public void sendInfo(String[] sqlReq)
	{
		for (int i = 0; i < sqlReq.length; i++)
		{
			send(sqlReq[i]);
		}
	}

	private void send(String s)
	{
		if (s.equals("listConfig"))
		{
			// Skriver ut config-info
			com.out("listConfig\n");

			String[][] data = db.exece("select id,parent,value from vpConfig order by parent,id;");

			String[] id = data[0];
			String[] parent = data[1];
			String[] value = data[2];

			for (int i = 0; i < id.length; i++)
			{
				com.out(id[i] + "^" + parent[i] + "^" + value[i] + "\n");
			}

		} else
		if (s.equals("listTextRouters"))
		{
			com.out("listTextRouters\n");

			DbCnf cnf = new DbCnf(com);

			String[] txt;
			{
				String[] txtAlle = cnf.get("dbcnf.nettel.txt.alle");
				String[] txtRouter = cnf.get("dbcnf.nettel.txt.router");

				txt = new String[txtAlle.length+txtRouter.length];
				for (int i = 0; i < txtAlle.length; i++) txt[i] = txtAlle[i];
				for (int i = 0; i < txtRouter.length; i++) txt[txtAlle.length+i] = txtAlle[i];
			}

			for (int i = 0; i < txt.length; i++)
			{
				com.outl("Text: " + txt[i] + "<br>");
				expandTextRouter(txt[i]);

				//for (int j = 0; j < txtAlle[i].length; j++)
				//{
				//	com.outl("("+i+","+j+"): " + txtAlle[i][j] + "<br>");
				//}
			}

			com.outl("Done<br>");


		}
		if (s.equals("listRouters"))
		{
			// liste over alle routere (gateways)
			com.out("listRouters\n");

			String[][] data = db.exece("select id,sysName from nettel where kat='GW' order by id;");

			String[] idNettel = data[0];
			String[] nettel = data[1];

			//String[] idNettel = db.exec("select id from nettel where kat='GW' order by id;");
			//String[] nettel = db.exec("select sysName from nettel where kat='GW' order by id;");
			String[] link;

			for (int i = 0; i < idNettel.length; i++)
			{
				//com.outl("nettel: " + nettel[i].toLowerCase() + "|");
				if (nettel[i] != null && !nettel[i].toLowerCase().equals("null"))
				{
					String[] tok = misc.tokenizel(nettel[i], "-");
					String name = tok[0];

					// sjekk gateway-nummer
					int nr = 1;
					if (tok[1].length() > 2)
					{
						tok[1] = tok[1].substring(2, tok[1].length() );
						nr = Integer.parseInt(tok[1]);
					}

					com.out(idNettel[i] + "^" + name + "^" + nr + "^gw" );
					com.out("\n");
				} else
				{
					//com.outl("ERROR: NULL");
					String name = "null";
					int nr = 1;
					com.outl(idNettel[i] + "^" + name + "^" + nr + "^gw");
				}

			}

		} else
		if (s.equals("listRouterLinks"))
		{
			// liste over alle linker mellom routere
			com.out("listRouterLinks\n");
			//String[] nettel = db.exec("select id from nettel where type='gw' order by id;");
			String[] nettel = db.exec("select id from nettel where kat='GW' order by id;");
			String[] id;
			String[] link;
			String[] speed;
			String[] interf;
			for (int i = 0; i < nettel.length; i++)
			{
				String[][] data = db.exece("select tilruter,id,speed,interf,gwip,bits,maxhosts,antmask,ospf from subnet where type='link' and ruter='" + nettel[i] + "' order by tilruter;");

				com.out(nettel[i] + "^");

				if (data[0][0] != null)
				{
					com.printString(data, "^", ",");
				}

				com.out("\n");
			}

		} else
		if (s.equals("listNetRouters"))
		{
			// liste over alle net-routere
			com.outl("listNetRouters");

			// liste over alle stam-routere
			String[] netId = db.exec("select id from subnet where type='stam' group by kat order by id;");

			if (netId[0] != null)
			{
				String[] net = db.exec("select kat from subnet where type='stam' group by kat order by id;");
				for (int i = 0; i < netId.length; i++)
				{
					com.out("-"+netId[i] + "^" + net[i] + "^1^stam");
					com.out("\n");
				}
			}

			// liste over alle elink-routere
			netId = db.exec("select id from subnet where type='elink' order by id;");

			if (netId[0] != null)
			{
				String[] net = db.exec("select kat from subnet where type='elink' order by id;");
				for (int i = 0; i < netId.length; i++)
				{
					com.out("-"+netId[i] + "^" + net[i] + "^1^elink");
					com.out("\n");
				}
			}

		} else
		if (s.equals("listNetLinks"))
		{
			// liste over alle linker mellom net-routere (stam/elink)
			com.outl("listNetLinks");

			// liste over alle linker mellom stam-routere
			String[][] data = db.exece("select id,kat from subnet where type='stam' group by kat order by id;");
			String[] netId = data[0];
			String[] net = data[1];

			if (netId[0] != null)
			{
				String[] ruterId;
				String[] id;
				String[] speed;
				String[] interf;
				for (int i = 0; i < netId.length; i++)
				{
					data = db.exece("select ruter,id,speed,interf,gwip,bits,maxhosts,antmask,ospf from subnet where type='stam' and kat='" + net[i] + "' order by ruter;");
					//ruterId = data[0];
					//id = data[1];
					//speed = data[2];
					//interf = data[3];

					com.out("-"+netId[i] + "^");
					com.printString(data, "^", ",");
					com.outl("");
				}
			}

			// liste over alle linker mellom elink-routere
			data = db.exece("select id,ruter,speed,interf,gwip,bits,maxhosts,antmask,ospf from subnet where type='elink' order by id;");
			if (data[0][0] != null)
			{
				for (int i = 0; i < data[0].length; i++)
				{
					com.outl("-"+data[0][i] + "^" + data[1][i] + "," + data[0][i] + "," + data[2][i] + "," + data[3][i] + "," + data[4][i] + "," + data[5][i] + "," + data[6][i] + "," + data[7][i] + "," + data[8][i] );
				}
			}



		} else
		if (s.equals("listLinkInfo"))
		{
			// liste over info for hver link (listRouterLinks og listNetLinks må kalles først)
			com.outl("listLinkInfo");




		} else
		if (s.equals("listRouterGroups"))
		{
			// liste over alle routere i grupper
			com.outl("listRouterGroups");

			String[][] grupper = db.exece("select gruppe_id,name from vpNettelGrp,vpNettelGrpInfo where gruppe_id=vpNettelGrpInfo.id group by gruppe_id order by gruppe_id;");

			if (grupper[0][0] != null)
			{
				for (int i = 0; i < grupper[0].length; i++)
				{
					int x = 0;
					int y = 0;
					String xy[][];

					xy = db.exece("select x,y from vpNettelXY where id_nettel='" + grupper[0][i] + "' and type='grp';");
					if (xy[0][0] != null)
					{
						x = Integer.parseInt(xy[0][0]);
						y = Integer.parseInt(xy[1][0]);
					}

					String[] grp = db.exec("select nettel_id from vpNettelGrp where gruppe_id='" + grupper[0][i] + "';");

					com.out(grupper[0][i] + "^" + grupper[1][i] + "^" + x + "^" + y + "^");
					com.printString(grp, "^");
					com.outl("");
				}
			}

		} else
		if (s.equals("listRouterXY"))
		{
			// liste over XY-koordinater for router-boksene i gruppe-modus
			com.out("listRouterXY\n");

			String gruppeId = com.getp("gruppeId");

			// liste over XY-koordinater for router-boksene
			String[] idNettel = db.exec("select id from nettel where kat='GW' order by id;");
			String[] nettelConfigIndex = db.exec("select id_nettel from vpNettelXY where type='link' and gruppe='" + gruppeId + "' order by id_nettel;");
			String[] nettelConfigX = db.exec("select x from vpNettelXY where type='link' and gruppe='" + gruppeId + "' order by id_nettel;");
			String[] nettelConfigY = db.exec("select y from vpNettelXY where type='link' and gruppe='" + gruppeId + "' order by id_nettel;");
			for (int i = 0; i < idNettel.length; i++)
			{
				boolean b = true;
				for (int j = 0; j < nettelConfigIndex.length; j++)
				{
					if (idNettel[i].equals(nettelConfigIndex[j]) )
					{
						com.out(nettelConfigIndex[j] + "^" + nettelConfigX[j] + "^" + nettelConfigY[j]);
						b = false;
						break;
					}
				}
				if (b)
				{
					com.out(idNettel[i] + "^0^0");
				}
				com.out("\n");
			}


			// XY for stam-routere
			idNettel = db.exec("select id from subnet where type='stam' or type='elink' group by kat order by id;");
			nettelConfigIndex = db.exec("select id_nettel from vpNettelXY where type='net' and gruppe='" + gruppeId + "' order by id_nettel;");
			nettelConfigX = db.exec("select x from vpNettelXY where type='net' and gruppe='" + gruppeId + "' order by id_nettel;");
			nettelConfigY = db.exec("select y from vpNettelXY where type='net' and gruppe='" + gruppeId + "' order by id_nettel;");
			for (int i = 0; i < idNettel.length; i++)
			{
				boolean b = true;
				for (int j = 0; j < nettelConfigIndex.length; j++)
				{
					if (idNettel[i].equals(nettelConfigIndex[j]) )
					{
						com.out("-"+nettelConfigIndex[j] + "^" + nettelConfigX[j] + "^" + nettelConfigY[j]);
						b = false;
						break;
					}
				}
				if (b)
				{
					com.out("-"+idNettel[i] + "^0^0");
				}
				com.out("\n");
			}



		} else
		if (s.equals("listNettel"))
		{
			// liste over XY-koordinater for router-boksene
			com.out("listNettel\n");

			String id = com.getp("nettelID");

			String[][] data;

			String[] link;
			String[] utId;
			String[] innId;
			String[] speed;
			String[] interfUt; // ut fra senter-nettel
			String[] interfInn;
			String[] nettel;
			String[][] ipRomUt = new String[4][];
			String[][] ipRomInn = new String[4][];
			String[] ospfUt;
			String[] ospfInn;

			nettel = db.exec("select sysName from nettel where id='" + id + "' and kat='GW';");
			if (nettel[0] != null)
			{
				gw = true;
				Vector v = new Vector();
				String gwName = nettel[0];

				// skriv ut router-info fra subnet
				data = db.exece("select tilruter,id,speed,interf,gwip,bits,maxhosts,antmask,ospf from subnet where type='link' and ruter='" + id + "' order by id;");
				link = data[0];
				utId = data[1];
				speed = data[2];
				interfUt = data[3];
				ipRomUt[0] = data[4];
				ipRomUt[1] = data[5];
				ipRomUt[2] = data[6];
				ipRomUt[3] = data[7];
				ospfUt = data[8];

				data = db.exece("select id,interf,gwip,bits,maxhosts,antmask,ospf from subnet where type='link' and tilruter='" + id + "' order by id;");
				innId = data[0];
				interfInn = data[1];
				ipRomInn[0] = data[2];
				ipRomInn[1] = data[3];
				ipRomInn[2] = data[4];
				ipRomInn[3] = data[5];
				ospfInn = data[6];


				nettel = db.exec("select sysName from nettel,subnet where nettel.id=subnet.tilruter and ruter='" + id + "' order by subnet.id;");


				for (int i = 0; i < link.length; i++)
				{
					String[] tok = misc.tokenizel(nettel[i], "-");
					String name = tok[0];
					String type = tok[1];

					// sjekk gateway-nummer
					int nr = 1;
					if (type.length() > 2)
					{
						type = type.substring(2, type.length() );
						nr = Integer.parseInt(type);
					}

					com.out(link[i] + "^" + name + "^" + nr + "^gw");
					com.out("\n");
					v.addElement(link[i] + "," + utId[i] + ",gw," + speed[i] + "," + interfUt[i] + "," + interfInn[i] + "," + innId[i] +
								"," + ipRomUt[0][i] + "+" + ipRomUt[1][i] + "+" + ipRomUt[2][i] + "+" + ipRomUt[3][i] +
								"," + ipRomInn[0][i] + "+" + ipRomInn[1][i] + "+" + ipRomInn[2][i] + "+" + ipRomInn[3][i] +
								"," + ospfUt[i] + "+" + ospfInn[i] );
				}

				// skriv ut stam/elink info fra subnet
				link = db.exec("select id from subnet where ruter='" + id + "' and (type='stam' or type='elink') order by id;");
				if (link[0] != null)
				{
					int baseId = Integer.parseInt((db.exec("select id from nettel order by id desc limit 1;"))[0]);

					data = db.exece("select kat,type,vlan,speed,interf,gwip,bits,maxhosts,antmask,ospf from subnet where ruter='" + id + "' and (type='stam' or type='elink') order by id;");
					String[] kat = data[0];
					String[] type = data[1];
					String[] vlan = data[2];
					speed = data[3];
					interfUt = data[4];

					ipRomUt[0] = data[5];
					ipRomUt[1] = data[6];
					ipRomUt[2] = data[7];
					ipRomUt[3] = data[8];
					ospfUt = data[9];

					for (int i = 0; i < link.length; i++)
					{
						com.outl( (baseId+Integer.parseInt(link[i])) + "^" + kat[i] + "^1^" + type[i]);

						v.addElement( (baseId+Integer.parseInt(link[i])) + "," + link[i] + ",net," + speed[i] + "," + interfUt[i] + ",undef" +
									",1," + ipRomUt[0][i] + "+" + ipRomUt[1][i] + "+" + ipRomUt[2][i] + "+" + ipRomUt[3][i] + "," + ospfUt[i] );

						utFraRouter.addElement(vlan[i]);
					}
				}


				// legg alle linkene inn i hz-vektoren, linker mellom routere er hz
				hz = new String[v.size()];
				for (int i = 0; i < v.size(); i++)
				{
					hz[i] = (String)v.elementAt(i);
				}

				v = new Vector();

				// sjekk hvilken switch som har denne routeren som uplink
				nettel = db.exec("select swid from swport where portname like 'o:" + gwName + "';");
				String swid = "0";
				String swname = "null";
				if (nettel[0] != null)
				{
					swid = nettel[0];
					nettel = db.exec("select sysName from nettel where id='" + nettel[0] + "';");
					swname = misc.tokenize(nettel[0], "-")[0];
				}

				// sjekk om det er noen LAN ut fra routeren
				data = db.exece("select id,org,kat,speed,interf,gwip,bits,maxhosts,antmask,ospf from subnet where ruter='" + id + "' and type='lan' order by interf;");
				if (data[0][0] != null)
				{
					for (int i = 0; i < data[0].length; i++)
					{
						String name = data[1][i] + "," + data[2][i];

						com.out(data[0][i] + "^" + name + "^1^lan");

						com.out("^" + swid + "^" + swname);
						com.out("\n");

						String lanData = data[0][i] + "," + data[0][i] + ",net," + data[3][i] + "," + data[4][i] + ",undef";
						//v.addElement(data[0][i] + "," + data[0][i] + ",net," + data[3][i] + "," + data[4][i] + ",undef," + data[5][i] + "," + data[6][i] + "," + data[7][i] + "," + data[8][i]);


						int teller = i+1;
						String ipRomS = "," + data[5][i] + "+" + data[6][i] + "+" + data[7][i] + "+" + data[8][i];

						while (teller < data[0].length && data[4][i].equals(data[4][teller]) )
						{
							ipRomS = ipRomS + "," + data[5][teller] + "+" + data[6][teller] + "+" + data[7][teller] + "+" + data[8][teller];
							teller++;
						}
						int antIpRom = teller - i;
						i = teller - 1;

						String ospf = data[9][i];

						lanData = lanData + "," + antIpRom + ipRomS + ","+ospf;
						v.addElement(lanData);



					}

				}
				// legg alle linkene inn i dn-vektoren, lan ut fra routeren er dn
				dn = new String[v.size()];
				for (int i = 0; i < v.size(); i++)
				{
					dn[i] = (String)v.elementAt(i);
				}



			} else
			{
				// skriv ut switch-info fra swport
				link = db.exec("select idbak from swport where swid='" + id + "' and idbak!='0' order by id;");
				if (link[0] != null)
				{
					Vector u = new Vector();
					Vector h = new Vector();
					Vector d = new Vector();

					data = db.exece("select id,portname,speed,mp,idbak from swport where swid='" + id + "' and idbak!='0' order by id;");
					utId = data[0];
					String[] portname = data[1];
					speed = data[2];
					interfUt = data[3];
					String[] idbak = data[4];

					//utId = db.exec("                   select id from swport where swid='" + id + "' and idbak!='0' order by id;");
					//String[] portname = db.exec("select portname from swport where swid='" + id + "' and idbak!='0' order by id;");
					//speed = db.exec("               select speed from swport where swid='" + id + "' and idbak!='0' order by id;");
					//interfUt = db.exec("                select mp from swport where swid='" + id + "' and idbak!='0' order by id;");

					nettel = db.exec("select sysName from nettel,swport where nettel.id=idbak and swid='" + id + "' and idbak!='0' order by swport.id;");
					String[][] ifInnMatrix = db.exece("select swid,mp from swport where idbak='" + id + "' order by id;");

					for (int i = 0; i < nettel.length; i++)
					{
						//nettel = db.exec("select sysName from nettel where id='" + link[i] + "';");
						//String[] tok = misc.tokenize(nettel[i], "-");

						String[] direct = misc.tokenize(portname[i], ":");
						if (direct[0].equals("o") || direct[0].equals("h") || direct[0].equals("n") )
						{
							String[] tok = misc.tokenizel(nettel[i], "-");
							String name = tok[0];
							String type = tok[1];

							// sjekk gateway-nummer
							int nr = 1;

							if (type.length() > 2 && !type.substring(0, 1).equals("h") )
							{
								nr = Integer.parseInt(type.substring(2, type.length() ));
								type = type.substring(0, 2);

							} else
							if (type.length() > 1 && type.substring(0, 1).equals("h") )
							{
								nr = Integer.parseInt(type.substring(1, type.length() ));
								type = type.substring(0, 1);
							}

							com.outl(link[i] + "^" + name + "^" + nr + "^" + type);
						}
						// sjekk om det fins noe interface i andre enden som vi vet om
						//String ifInn = "undef";
						String ifInn = "";
						{
							int ifInnIndex = misc.getIndex(ifInnMatrix, Integer.parseInt(idbak[i]) );
							if (ifInnIndex != -1)
							{
								ifInn = ifInnMatrix[1][ifInnIndex];
							}
						}
						if (ifInn.equals(""))
						{
							ifInn = "undef";
						}

						if (direct[0].equals("o"))
						{
							u.addElement(link[i] + "," + utId[i] + ",sw," + speed[i] + "," + interfUt[i] + "," + ifInn );
							//com.out("legger til uplink: " + link[i] + "," + utId[i] + ",sw," + speed[i] + " name: " + portname[i] );
						} else
						if (direct[0].equals("h"))
						{
							h.addElement(link[i] + "," + utId[i] + ",sw," + speed[i] + "," + interfUt[i] + "," + ifInn );
						} else
						if (direct[0].equals("n"))
						{
							d.addElement(link[i] + "," + utId[i] + ",sw," + speed[i] + "," + interfUt[i] + "," + ifInn );
						}
					}

					// andre porter ut fra switch (srv, mas, feil, uspesifisert osv)
					// liten hack, for å unngå duplikat id
					link = db.exec("select id from nettel order by id desc limit 1;"); // finner høyste ID i bruk i nettel
					int baseId = Integer.parseInt(link[0]);

					data = db.exece("select id,portname,speed,mp,vlan from swport where swid='" + id + "' and (idbak is null or idbak='0') and status='Up' and portname not like 'link:%' order by id;");
					if (data[0][0] != null)
					{
						utId = data[0];
						nettel = data[1];
						speed = data[2];
						interfUt = data[3];
						String[] vlan = data[4];
						for (int i = 0; i < utId.length; i++)
						{
							String type = "undef";
							String[] direct = misc.tokenizel(nettel[i], ":");

							if (direct.length > 1)
							{
								if (direct[0].equals("srv") || direct[0].equals("pc") || direct[0].equals("mas"))
								{
									type = direct[0];
									nettel[i] = direct[1];
								} else
								if (misc.tokenize(direct[1],",").length >= 2)
								{
									// HUB'er med idbak=0, men med kommakonvensjon, vises som ikke-snmp hub
									type = "hub";
									nettel[i] = direct[1];
								}

							}

							com.outl( (baseId+Integer.parseInt(utId[i])) + "^" + nettel[i] + "^1^" + type);
							d.addElement( (baseId+Integer.parseInt(utId[i])) + "," + utId[i] + "," + type + "," + speed[i] + "," + interfUt[i] + ",undef" );
							utFraSwitch.addElement(vlan[i]);


						}
					}





					up = new String[u.size()];
					for (int i = 0; i < u.size(); i++)
					{
						up[i] = (String)u.elementAt(i);
					}
					hz = new String[h.size()];
					for (int i = 0; i < h.size(); i++)
					{
						hz[i] = (String)h.elementAt(i);
					}
					dn = new String[d.size()];
					for (int i = 0; i < d.size(); i++)
					{
						dn[i] = (String)d.elementAt(i);
					}


				}

			}

		}
		if (s.equals("listNettelLinks"))
		{
			// liste over linkene fra en bestemt nettel-boks
			com.out("listNettelLinks\n");

			// først alle uplinker
			com.out("up^");
			com.printString(up, "^");
			com.out("\n");

			// først alle uplinker
			com.out("hz^");
			com.printString(hz, "^");
			com.out("\n");

			// først alle uplinker
			com.out("dn^");
			com.printString(dn, "^");
			com.out("\n");

		} else
		if (s.equals("listLinkVlans"))
		{
			// liste over vlan på linker fra en bestemt nettel-boks
			com.out("listLinkVlans\n");
			Vector v = new Vector();

			// hvis gw kan vi gå ut fra ingen up, kun hz med 1 vlan og normal dn
			if (gw)
			{
				String[] link;
				String id = com.getp("nettelID");

				if (hz != null)
				{
					int utFraRouterTeller = 0;
					for (int i = 0; i < hz.length; i++)
					{
						com.out( (misc.tokenize(hz[i], ","))[0] + "^");
						link = db.exec("select interf from subnet where ruter='" + id + "' and tilruter='" + hz[i] + "';");
						if (link[0] != null)
						{
							if (link[0].substring(0, 4).equals("Vlan"))
							{
								com.out(link[0].substring(4, link[0].length() ) + "\n");
							} else
							{
								// ikke vlan, altså noe ethernet (direkte)
								com.out("0" + "\n");
							}
						} else
						{
							// går ut ifra port ut fra router til stam/elink.
							com.out("^" + (String)utFraRouter.elementAt(utFraRouterTeller) + "\n");
							utFraRouterTeller++;
						}
					}
				}

				if (dn != null)
				{
					//int begin = 0;

					// så skriv ut vlan for alle LAN (kun RSM så langt)
					//link = db.exec("select id from subnet where ruter='" + id + "' and type='lan' order by id;");
					String[] vlan = db.exec("select vlan from subnet where ruter='" + id + "' and type='lan' group by interf order by interf;");
					for (int i = 0; i < dn.length; i++)
					{
						com.outl( (misc.tokenize(dn[i], ","))[0] + "^" + vlan[i]);
					}


				}

				for (int i = 0; i < v.size(); i++)
				{
					String tilid = (String)v.elementAt(i);
					com.out(tilid + "^");
					link = db.exec("select interf from subnet where ruter='" + id + "' and tilruter='" + tilid + "';");
					if (link[0] != null)
					{
						com.out(link[0].substring(4, link[0].length() ) + "\n");
					} else
					{
						link = db.exec("select interf from subnet where ruter='" + id + "' and tilruter='" + tilid + "';");

					}
				}

				return;
			}
			// ikke gw, altså sw. up/hz/dn behandles nå likt

			if (up != null)
			{
				for (int i = 0; i < up.length; i++)
				{
					v.addElement(up[i]);
				}
			}
			if (hz != null)
			{
				for (int i = 0; i < hz.length; i++)
				{
					v.addElement(hz[i]);
				}
			}
			if (dn != null)
			{
				for (int i = 0; i < dn.length; i++)
				{
					v.addElement(dn[i]);
				}
			}

			String[] link;
			String id = com.getp("nettelID");

			int utFraSwitchTeller = 0;

			for (int i = 0; i < v.size(); i++)
			{
				String tilid = (String)v.elementAt(i);
				tilid = (misc.tokenize(tilid, ","))[0];
				//com.out(tilid + "^");
				com.out(tilid);
				String[][] data = db.exece("select vlan,id from swport where swid='" + id + "' and idbak='" + tilid + "' and portname not like 'link:%';");
				link = data[0];
				if (link[0] != null)
				{
					if (link[0].toLowerCase().equals("trunk"))
					{
						//link = db.exec("select id from swport where swid='" + id + "' and idbak='" + tilid + "';");
						//link = db.exec("select vlan from trunk where swportid='" + link[0] + "';");
						link = db.exec("select vlan from trunk where swportid='" + data[1][0] + "';");
						if (link[0] != null)
						{
							for (int j = 0; j < link.length; j++)
							{
								com.out("^" + link[j]);
							}
							com.out("\n");
						} else
						{
							com.out("^\n");
						}


					} else
					{
						com.out("^" + link[0] + "\n");
					}
				} else
				{
					// går ut ifra port ut fra switch, til lan/srv/mas osv.
					String vlan = (String)utFraSwitch.elementAt(utFraSwitchTeller);
					if (vlan.equals("Trunk")) vlan = "-1";
					com.out("^" + vlan + "\n");
					utFraSwitchTeller++;
				}

			}










		}

	}

	private Vector[] fetchLast(Vector gw, Vector sw, int from, int to, boolean avg)
	{
		// kaller eksternt perl-script, last.pl

		// lag liste over gw-id'er
		StringBuffer buf = new StringBuffer();
		buf.append( (String)gw.elementAt(0) );
		for (int i = 1; i < gw.size(); i++)
		{
			buf.append("," + (String)gw.elementAt(i) );
		}
		String gwList = buf.toString();

		// lag liste over sw-id'er
		buf = new StringBuffer();
		buf.append( (String)sw.elementAt(0) );
		for (int i = 1; i < sw.size(); i++)
		{
			buf.append("," + (String)sw.elementAt(i) );
		}
		String swList = buf.toString();

		// reverser tid
		from = -from;
		to = -to;
		String time;
		if (to == 0)
		{
			time = "" + from + ",now";
		} else
		{
			time = "" + from + "," + to;
		}

		// fix type
		String type;
		if (avg)
		{
			type = "avg";
		} else
		{
			type = "max";
		}

		// exec perl-program

		String[] cmd = new String[6];
		cmd[0] = "/usr/bin/perl";
		cmd[1] = "/usr/local/jserv/vPServer/last.pl";
		cmd[2] = gwList;
		cmd[3] = swList;
		cmd[4] = time;
		cmd[5] = type;

		Runtime rt = Runtime.getRuntime();

		int ev = -1;

		Vector retVect = new Vector();
		int teller = 0;
		Vector v = new Vector();
		Vector v2 = new Vector();

		try
		{
			Process last = rt.exec(cmd);

			BufferedReader in = new BufferedReader(new InputStreamReader(last.getInputStream() ));
			String line;

			while ((line = in.readLine()) != null)
			{
				//com.outl(line);
				v.addElement(misc.tokenize(line, ","));
			}
			last.destroy();

			for (int i = 1; i < v.size(); i++)
			{
				String[] s = (String[])v.elementAt(i);
				if (s[0].length() >= 4)
				{
					if (s[0].substring(0, 4).equals("list"))
					{
						retVect.addElement(v2);
						v2 = new Vector();
						teller++;
					} else
					{
						v2.addElement(s);
					}
				} else
				{
					v2.addElement(s);
				}
			}
			retVect.addElement(v2);


		}
		catch (Exception e)
		{
			com.out("Error: " + e.getMessage() );
		}

		Vector[] ret = new Vector[retVect.size()];
		for (int i = 0; i < retVect.size(); i++)
		{
			ret[i] = (Vector)retVect.elementAt(i);
		}

		return ret;

	}

	public int getIndex(Vector v, int n)
	{
		for (int i = 0; i < v.size(); i++)
		{
			String[] s = (String[])v.elementAt(i);
			int index = Integer.parseInt(s[0]);

			if (index == n)
			{
				return i;
			}
		}
		return -1;
	}




	private void expandTextRouter(String txt)
	{
		// hashmap textNettel
		HashMap hm = new HashMap();

		String[] elements = cnf.get("dbcnf.nettel.txt.alle." + txt);
		String[][][] replace = new String[elements.length][][];

		for (int i = 0; i < elements.length; i++)
		{
			String[] s = cnf.get("dbcnf.nettel.txt.alle." + txt + "." + elements[i]);

			com.out("element " + i + ": " + elements[i]);
			com.out("  s[0]: " + s[0]);

			String[][] data;
			if (s[0].equals("nettel"))
			{
				// trenger ikke å joine tabeller
				data = db.exece("select id," + s[2] + " from nettel where kat='GW' order by id;");
			} else
			{
				data = db.exece("select nettel.id," + s[0] + "." + s[2] + " from nettel," + s[0] + " where nettel.id=" + s[0] + "." + s[1] + " and nettel.kat='GW' group by nettel.id order by nettel.id;");
			}

			String[] id = data[0];
			String[] val = data[1];

			for (int j = 0; j < id.length; j++)
			{
				String v = (String)hm.get(id[j]);
				if (v != null) hm.put(id[j], stringReplace(v, s[i], val[j]));
			}
		}

		com.outl("Now printing<br>");

		// Legger til denne hashen til textNettel
		Set values = hm.entrySet();
		Iterator iter = values.iterator();
		if (!hm.isEmpty()) while (iter.hasNext())
		{
			Map.Entry entry = (Map.Entry)iter.next();
			String key = (String)entry.getKey();
			String s = (String)entry.getValue();

			com.out("Key: " + key + " Value: " + s);
		}


	}

	public String stringReplace(String s, String r, String d)
	{
		int index = s.indexOf(r);

		if (index != -1)
		{
			StringBuffer b = new StringBuffer(s);
			b.replace(index, r.length(), d);
			return b.toString();
		}
		return s;
	}


}

*/

























