/*******************
*
* $Id: getBoksMacs.java,v 1.6 2003/05/29 14:27:39 kristian Exp $
* This file is part of the NAV project.
* Loging of CAM/CDP data
*
* Copyright (c) 2002 by NTNU, ITEA nettgruppen
* Authors: Kristian Eide <kreide@online.no>
*
*******************/

import java.io.*;
import java.util.*;
import java.net.*;
import java.text.*;

import java.sql.*;

import no.ntnu.nav.ConfigParser.*;
import no.ntnu.nav.Database.*;
import no.ntnu.nav.SimpleSnmp.*;


class getBoksMacs
{
	public static final String navRoot = "/usr/local/nav/";
	public static final String dbConfigFile = "local/etc/conf/db.conf";
	public static final String configFile = "local/etc/conf/getBoksMacs.conf";
	public static final String watchMacsFile = "local/etc/conf/watchMacs.conf";
	public static final String scriptName = "getBoksMacs";

	public static int NUM_THREADS = 24;
	public static final int SHOW_TOP = 25;

	public static final boolean VERBOSE_OUT = false;
	public static final boolean DEBUG_OUT = false;

	public static final boolean DB_UPDATE = true;
	public static final boolean DB_COMMIT = true;

	public static final boolean DUMP_CAM = true;

	/*
	public static final boolean VERBOSE_OUT = true;
	public static final boolean DEBUG_OUT = true;

	public static final boolean DB_UPDATE = false;
	public static final boolean DB_COMMIT = false;

	public static final boolean DUMP_CAM = false;
	*/

	// Felles datastrukturer som bare skal leses fra
	static HashMap macBoksId = new HashMap();
	static HashMap boksIdName = new HashMap();
	static HashMap boksidKat = new HashMap();
	static HashMap boksidType = new HashMap();
	static HashMap sysnameMap = new HashMap();

	static HashMap spanTreeBlocked = new HashMap();

	static HashSet cdpBoks = new HashSet();

	static HashSet foundBoksBakSwp = new HashSet();

	static Set downBoksid = new HashSet();
	static Map vlanBoksid = new HashMap();

	// For CAM-logger
	static HashMap unclosedCam = new HashMap();
	static HashSet safeCloseBoksid = new HashSet();
	static HashSet watchMacs = new HashSet();

	public static void main(String[] args) throws SQLException
	{
		ConfigParser cp, dbCp;
		try {
			cp = new ConfigParser(navRoot + configFile);
		} catch (IOException e) {
			errl("Error, could not read config file: " + navRoot + configFile);
			return;
		}
		try {
			dbCp = new ConfigParser(navRoot + dbConfigFile);
		} catch (IOException e) {
			errl("Error, could not read config file: " + navRoot + dbConfigFile);
			return;
		}
		if (!Database.openConnection(dbCp.get("dbhost"), dbCp.get("dbport"), dbCp.get("db_nav"), dbCp.get("script_"+scriptName), dbCp.get("userpw_"+dbCp.get("script_"+scriptName)))) {
			errl("Error, could not connect to database!");
			return;
		}

		// Set MAX_MISSCNT
		int MAX_MISSCNT = 3;
		{
			String s = cp.get("MaxMisscnt");
			if (s != null) {
				try {
					MAX_MISSCNT = Integer.parseInt(s);
				} catch (NumberFormatException e) {
					errl("Warning, MaxMisscnt must be a number: " + s);
				}
			}
		}

		// Check arguments
		if (args.length > 0) {
			try {
				NUM_THREADS = Integer.parseInt(args[0]);
			} catch (NumberFormatException e) {
				outl("Error, unrecognized argument: " + args[0]);
				return;
			}
			if (NUM_THREADS > 128) {
				outl("Error, more than 128 threads not recommended, re-compile needed.");
				return;
			}
		}
		outl("Running with " + NUM_THREADS + " thread"+(NUM_THREADS>1?"s":"")+".");

		// Load watchMacs
		try {
			int wmcnt=0;
			BufferedReader bf = new BufferedReader(new FileReader(navRoot+watchMacsFile));
			String s;
			while ( (s=bf.readLine()) != null) {
				s = s.trim();
				if (s.length() != 12 || s.startsWith("#")) continue;
				watchMacs.add(s);
				wmcnt++;
			}
			outl("watchMacs read: " + wmcnt);
		} catch (IOException e) {
			outl("Could not read watchMacs.conf");
		}


		long dumpBeginTime,dumpUsedTime;

		outl("Dumping data from tables...");

		// Hent kobling mellom mac<->boksid og mac<->sysName
		//ResultSet rs = Database.query("SELECT mac,boksid,sysName FROM boksmac NATURAL JOIN boks");
		out("  netboxmac...");
		dumpBeginTime = System.currentTimeMillis();
		ResultSet rs = Database.query("SELECT netboxid,mac FROM netboxmac");
		while (rs.next()) macBoksId.put(rs.getString("mac"), rs.getString("netboxid"));
		dumpUsedTime = System.currentTimeMillis() - dumpBeginTime;
		outl(dumpUsedTime + " ms.");

		// Hent kobling mellom boksid<->sysName og motsatt
		out("  boks...");
		dumpBeginTime = System.currentTimeMillis();
		rs = Database.query("SELECT netboxid,sysName,catid,typename FROM netbox LEFT JOIN type USING(typeid)");
		while (rs.next()) {
			boksIdName.put(rs.getString("netboxid"), rs.getString("sysname"));
			boksidKat.put(rs.getString("netboxid"), rs.getString("catid").toUpperCase());
			boksidType.put(rs.getString("netboxid"), rs.getString("typename"));
			String sysname = rs.getString("sysname");
			String kat = rs.getString("catid").toLowerCase();
			if (kat.equals("gw") || kat.equals("sw") || kat.equals("kant")) {
				// Stripp etter første '.'
				int i;
				if ( (i=sysname.indexOf('.')) != -1) {
					sysname = sysname.substring(0, i);
				}
			}
			sysnameMap.put(sysname, rs.getString("netboxid"));
			//System.out.println("Lagt til: " + sysname + " kat: " + kat);
		}

		rs = Database.query("SELECT netboxid FROM netbox WHERE up!='y'");
		while (rs.next()) {
			downBoksid.add(rs.getString("netboxid"));
		}

		// Hent alle bokser der kat='GW'
		QueryBoks.boksGwSet = new HashSet();
		rs = Database.query("SELECT netboxid FROM netbox WHERE catid='GW'");
		while (rs.next()) {
			QueryBoks.boksGwSet.add(rs.getString("netboxid"));
		}

		// Hent alle bokser med cdp
		rs = Database.query("SELECT netboxid FROM netbox JOIN type USING(typeid) WHERE cdp='t'");
		while (rs.next()) {
			cdpBoks.add(rs.getString("netboxid"));
		}
		dumpUsedTime = System.currentTimeMillis() - dumpBeginTime;
		outl(dumpUsedTime + " ms.");

		// Mapping fra boksid, port og modul til swportid i swport
		out("  swport...");
		dumpBeginTime = System.currentTimeMillis();
		QueryBoks.swportSwportidMap = new HashMap();
		rs = Database.query("SELECT swportid,netboxid,module,port FROM swport JOIN module USING(moduleid)");
		while (rs.next()) {
			String key = rs.getString("netboxid")+":"+rs.getString("module")+":"+rs.getString("port");
			QueryBoks.swportSwportidMap.put(key, rs.getString("swportid"));
		}
		dumpUsedTime = System.currentTimeMillis() - dumpBeginTime;
		outl(dumpUsedTime + " ms.");

		// Hent alle vlan som er blokkert av spanning-tree
		out("  swportblocked...");
		dumpBeginTime = System.currentTimeMillis();
		rs = Database.query("SELECT swportid,netboxid,ifindex,vlan FROM swportblocked JOIN swport USING(swportid) JOIN module USING(moduleid)");
		while (rs.next()) {
			String key = rs.getString("netboxid")+":"+rs.getString("vlan");
			HashMap blockedIfind;
			if ( (blockedIfind=(HashMap)spanTreeBlocked.get(key)) == null) spanTreeBlocked.put(key, blockedIfind = new HashMap());
			blockedIfind.put(rs.getString("ifindex"), rs.getString("swportid"));
		}
		dumpUsedTime = System.currentTimeMillis() - dumpBeginTime;
		outl(dumpUsedTime + " ms.");


		// Hent alle aktive vlan
		out("  vlan...");
		dumpBeginTime = System.currentTimeMillis();
		//rs = Database.query("SELECT DISTINCT netboxid,vlan FROM swport JOIN swportvlan USING (swportid) JOIN module USING(moduleid) WHERE trunk='f'");
		rs = Database.query("SELECT DISTINCT netboxid,vlan FROM swport JOIN module USING(moduleid) WHERE trunk='f'");
		while (rs.next()) {
			Set s;
			String boksid = rs.getString("netboxid");
			if ( (s=(Set)vlanBoksid.get(boksid)) == null) vlanBoksid.put(boksid, s = new TreeSet());
			s.add(new Integer(rs.getInt("vlan")));
		}
		{
			rs = Database.query("SELECT DISTINCT vlan FROM prefix JOIN vlan USING(vlanid) WHERE vlan IS NOT null");
			int[] vlanList = new int[rs.getFetchSize()];
			for (int i=0; rs.next(); i++) vlanList[i] = rs.getInt("vlan");

			rs = Database.query("SELECT netboxid,hexstring FROM swport JOIN module USING(moduleid) JOIN swportallowedvlan USING (swportid)");
			while (rs.next()) {
				Set s;
				String boksid = rs.getString("netboxid");
				String hexstring = rs.getString("hexstring");
				if (hexstring == null || hexstring.length() == 0) continue;
				if ( (s=(Set)vlanBoksid.get(boksid)) == null) vlanBoksid.put(boksid, s = new TreeSet());
				for (int i=0; i < vlanList.length; i++) {
					if (isAllowedVlan(hexstring, vlanList[i])) {
						s.add(new Integer(vlanList[i]));
					}
				}
			}
		}
		dumpUsedTime = System.currentTimeMillis() - dumpBeginTime;
		outl(dumpUsedTime + " ms.");


		// Alt fra swp_boks for duplikatsjekking
		out("  swp_boks...");
		dumpBeginTime = System.currentTimeMillis();
		HashSet swp = new HashSet();
		HashMap swp_d = new HashMap();
		rs = Database.query("SELECT swp_netboxid,netboxid,module,port,to_netboxid,to_module,to_port,misscnt FROM swp_netbox");
		ResultSetMetaData rsmd = rs.getMetaData();
		//rs = Database.query("SELECT swp_boksid,boksid,modul,port,boksbak FROM swp_boks JOIN boks USING (boksid) WHERE sysName='sb-sw'");
		while (rs.next()) {
			String key = rs.getString("netboxid")+":"+rs.getString("module")+":"+rs.getString("port")+":"+rs.getString("to_netboxid");
			swp.add(key);

			HashMap hm = getHashFromResultSet(rs, rsmd, false);
			swp_d.put(key, hm);

			// Vi trenger å vite om det befinner seg en GW|SW|KANT bak en gitt enhet
			String boksBakKat = (String)boksidKat.get(rs.getString("to_netboxid"));
			if (boksBakKat == null || isNetel(boksBakKat)) {
				foundBoksBakSwp.add(rs.getString("netboxid")+":"+rs.getString("module")+":"+rs.getString("port"));
			}

		}
		dumpUsedTime = System.currentTimeMillis() - dumpBeginTime;
		outl(dumpUsedTime + " ms.");

		// For CAM-logger, alle uavsluttede CAM-records (dvs. alle steder hvor til er null)
		if (DUMP_CAM) {
			out("  cam...");
			dumpBeginTime = System.currentTimeMillis();
			rs = Database.query("SELECT camid,netboxid,module,port,mac,misscnt FROM cam WHERE (end_time = 'infinity' OR misscnt >= 0) AND netboxid IS NOT NULL");
			while (rs.next()) {
				String key = rs.getString("netboxid")+":"+rs.getString("module")+":"+rs.getString("port")+":"+rs.getString("mac");
				if (unclosedCam.put(key, new String[] { rs.getString("camid"), rs.getString("misscnt") } ) != null) {
					errl("Error, found duplicate in cam for key: " + key);
				}
			}
			dumpUsedTime = System.currentTimeMillis() - dumpBeginTime;
			outl(dumpUsedTime + " ms.");
		}


		String qNettel;

		qNettel = "_all";
		//qNettel = "_new";
		//qNettel = "_sw";
		//qNettel = "_gw";
		//qNettel = "_kant";
		//qNettel = "_cat-ios";
		//qNettel = "_cdp";
		//qNettel = "voll-sw";
		//qNettel = "sb-353-sw"; // NO NAV AREA
		//qNettel = "kjemi-gw";
		//qNettel = "hyper-sw";
		//qNettel = "voll-sby-981-h";
		//qNettel = "hb-301-sw2";
		//qNettel = "tekno-sw2";
		//qNettel = "kjemi-382s-sw2";
		//qNettel = "itea-ans3-230-h"; // HP
		//qNettel = "hf-stud-802-h";
		//qNettel = "hf-ans-806-h";
		//qNettel = "kjemi-370-sw";
		//qNettel  = "blasal-sw2";
		//qNettel = "kjemi-gsw";
		//qNettel = "sb-gsw";
		//qNettel = "mts-646-sw";

		Database.setDefaultKeepOpen(true);
		if (qNettel.equals("_new")) {
			//rs = Database.query("SELECT ip,ro,boksid,typeid,typegruppe,kat,sysName FROM boks NATURAL JOIN type WHERE NOT EXISTS (SELECT boksid FROM swp_boks WHERE boksid=boks.boksid) AND (kat='KANT' or kat='SW') ORDER BY boksid");
		} else
		if (qNettel.equals("_all")) {
			rs = Database.query("SELECT ip,ro,netboxid,typename,typegroupid,catid,sysName FROM netbox JOIN type USING(typeid) WHERE catid IN ('SW','KANT','GW','GSW') AND up='y' AND ro IS NOT NULL");
		} else
		if (qNettel.equals("_gw")) {
			//rs = Database.query("SELECT ip,ro,boksid,typeid,typegruppe,kat,sysName FROM boks NATURAL JOIN type WHERE kat='GW'");
		} else
		if (qNettel.equals("_sw")) {
			//rs = Database.query("SELECT ip,ro,boksid,typeid,typegruppe,kat,sysName FROM boks NATURAL JOIN type WHERE kat='SW'");
		} else
		if (qNettel.equals("_kant")) {
			//rs = Database.query("SELECT ip,ro,boksid,typeid,typegruppe,kat,sysName FROM boks NATURAL JOIN type WHERE kat='KANT'");
		} else {
			rs = Database.query("SELECT ip,ro,netboxid,typename,typegroupid,catid,sysName FROM netbox JOIN type USING(typeid) WHERE sysName='"+qNettel+"'");
			//rs = Database.query("SELECT ip,ro,boksid,typeid,typegruppe,kat,sysName FROM boks NATURAL JOIN type WHERE prefiksid in (2089,1930) AND boksid != 241");
			//rs = Database.query("SELECT ip,ro,boksid,typeid,typegruppe,kat,sysName FROM boks NATURAL JOIN type WHERE typegruppe in ('cat-sw', 'ios-sw')");
		}
		Database.setDefaultKeepOpen(false);

		Stack bdStack = new Stack();
		while (rs.next()) {
			BoksData bd = new BoksData();
			bd.ip = rs.getString("ip");
			bd.cs_ro = rs.getString("ro");
			bd.boksId = rs.getString("netboxid");
			bd.boksTypegruppe = rs.getString("typegroupid");
			bd.boksType = rs.getString("typename");
			bd.sysName = rs.getString("sysname");
			bd.kat = rs.getString("catid");
			bdStack.push(bd);
		}
		int antBd = bdStack.size();

		// Sett datastrukturer for alle tråder
		QueryBoks.VERBOSE_OUT = VERBOSE_OUT;
		QueryBoks.DEBUG_OUT = DEBUG_OUT;
		QueryBoks.DB_UPDATE = DB_UPDATE;
		QueryBoks.DB_COMMIT = DB_COMMIT;

		QueryBoks.macBoksId = macBoksId;
		QueryBoks.boksIdName = boksIdName;
		QueryBoks.boksidKat = boksidKat;
		QueryBoks.boksidType = boksidType;
		QueryBoks.sysnameMap = sysnameMap;

		QueryBoks.spanTreeBlocked = spanTreeBlocked;

		QueryBoks.cdpBoks = cdpBoks;
		QueryBoks.vlanBoksid = vlanBoksid;

		QueryBoks.setFoundBoksBakSwp(foundBoksBakSwp);

		QueryBoks.unclosedCam = unclosedCam;
		QueryBoks.safeCloseBoksid = safeCloseBoksid;
		QueryBoks.watchMacs = watchMacs;

		// Indikerer om en tråd er ferdig
		QueryBoks.initThreadDone(NUM_THREADS);

		// Lag trådene
		long beginTime = System.currentTimeMillis();
		Thread[] threads = new Thread[NUM_THREADS];
		int digits = String.valueOf(NUM_THREADS-1).length();
		for (int i=0; i < NUM_THREADS; i++) {
			threads[i] = new QueryBoks(i, format(i, digits), bdStack, antBd, swp, swp_d);
			threads[i].start();
		}

		for (int i=0; i < NUM_THREADS; i++) {
			try {
				threads[i].join();
			} catch (InterruptedException e) {
				errl("Error, got InterruptedException: " + e.getMessage() );
			}
		}
		long usedTime = System.currentTimeMillis() - beginTime;

		// Sjekk om det er enheter som har forsvunnet
		int missinc=0,remcnt=0;
		Iterator iter = swp_d.values().iterator();
		while (iter.hasNext()) {
			HashMap hm = (HashMap)iter.next();
			String swp_boksid = (String)hm.get("swp_netboxid");
			String boksid = (String)hm.get("netboxid");
			if (!safeCloseBoksid.contains(boksid)) continue;

			// Dersom boksen bak er nede skal vi ikke slette
			String boksbak = (String)hm.get("to_netboxid");
			if (downBoksid.contains(boksbak)) continue;

			int misscnt = Integer.parseInt((String)hm.get("misscnt"));
			misscnt++;

			if (misscnt > MAX_MISSCNT) {
				remcnt++;
				// Slett record fra swp_boks
				if (DB_UPDATE) Database.update("DELETE FROM swp_netbox WHERE swp_netboxid = '"+swp_boksid+"'");
				if (DB_COMMIT) Database.commit(); else Database.rollback();
			} else {
				missinc++;
				// Øk misscnt med 1
				if (DB_UPDATE) Database.update("UPDATE swp_netbox SET misscnt=misscnt+1 WHERE swp_netboxid = '"+swp_boksid+"'");
				if (DB_COMMIT) Database.commit(); else Database.rollback();
			}

		}
		int swpResetCnt = QueryBoks.getSwpResetMisscnt();
		outl("swp_netbox: A total of " + prependSpace(missinc,4) + " units were missed,   " + prependSpace(swpResetCnt,4) + " units were reset,   " + prependSpace(remcnt,4) + " units were removed.");

		int[] camCnt = finishCam(MAX_MISSCNT);
		int camMissinc = camCnt[0];
		int camRemCnt = camCnt[1];
		int camResetCnt = QueryBoks.getCamResetMisscnt();
		outl("cam       : A total of " + prependSpace(camMissinc,4) + " records were missed, " + prependSpace(camResetCnt,4) + " records were reset, " + prependSpace(camRemCnt,4) + " records were closed.");

		ArrayList boksReport = QueryBoks.boksReport;
		Collections.sort(boksReport);

		digits = String.valueOf(Math.min(SHOW_TOP, boksReport.size())).length();
		for (int i=0; i < SHOW_TOP && i < boksReport.size(); i++) {
			BoksReport br = (BoksReport)boksReport.get(i);
			outl(format(i+1, digits)+": " + formatTime(br.getUsedTime()) + ", " + br.getBoksData().sysName + " (" + br.getBoksData().boksType + ") (" + br.getBoksData().ip + ")");
		}

		Database.closeConnection();
		outl("All done, time used: " + formatTime(usedTime) + ".");

		// Create a job-finished file
		try {
			String curDir = System.getProperty("user.dir");
			char sep = File.separatorChar;
			File f = new File(curDir+sep+"job-finished");
			f.createNewFile() ;
		} catch (SecurityException e) {
			errl("Error, cannot write to user.dir: " + e.getMessage() );
		} catch (IOException e) {
			errl("Error, got IOException: " + e.getMessage() );
		}

		outflush();
		errflush();
		System.exit(0);


	}

	// Lukker records i CAM-tabellen
	private static int[] finishCam(final int MAX_MISSCNT) {
		// Nå går vi gjennom og lukker alle records vi ikke har funnet igjen
		int missInc=0,remCnt=0;
		Iterator iter = unclosedCam.entrySet().iterator();
		while (iter.hasNext()) {
			Map.Entry me = (Map.Entry)iter.next();
			String key = (String)me.getKey();
			StringTokenizer st = new StringTokenizer(key, ":");

			String boksid = st.nextToken();
			if (!safeCloseBoksid.contains(boksid)) continue;

			String[] s = (String[])me.getValue();
			String camid = s[0];
			int misscnt = Integer.parseInt(s[1]);
			misscnt++;

			if (misscnt > MAX_MISSCNT) {
				// Nå skal vi virkelig lukke denne recorden
				if (DB_UPDATE) {
					try {
						String[] updateFields = {
							"misscnt", "null"
						};
						String[] condFields = {
							"camid", camid
						};
						if (DB_UPDATE) Database.update("cam", updateFields, condFields);
						if (DB_COMMIT) Database.commit(); else Database.rollback();
					} catch (SQLException e) {
						outl("  finishCam(): Closing record in cam, SQLException: " + e.getMessage() );
					}
				}
				remCnt++;
			} else {
				// Misscnt-feltet økes med en; dersom det var 0 fra før skal til settes til NOW()
				if (DB_UPDATE) {
					try {
						String[] updateFields;
						if (misscnt == 1) {
							String[] sa = {
								"end_time", "NOW()",
								"misscnt", String.valueOf(misscnt)
							};
							updateFields = sa;
						} else {
							String[] sa = {
								"misscnt", String.valueOf(misscnt)
							};
							updateFields = sa;
						}
						String[] condFields = {
							"camid", camid
						};
						if (DB_UPDATE) Database.update("cam", updateFields, condFields);
						if (DB_COMMIT) Database.commit(); else Database.rollback();
					} catch (SQLException e) {
						outl("  finishCam(): Semi-closing record in cam, SQLException: " + e.getMessage() );
					}
				}
				missInc++;
			}
		}
		return new int[] { missInc, remCnt };
	}

	private static String format(long i, int n) {
		DecimalFormat nf = new DecimalFormat("#");
		nf.setMinimumIntegerDigits(n);
		return nf.format(i);
	}
	private static String prependSpace(long i, int n) {
		StringBuffer sb = new StringBuffer(String.valueOf(i));
		int c = n-sb.length();
		while (c > 0) {
			sb.insert(0, " ");
			c--;
		}
		return sb.toString();
	}

	public static String formatTime(long t)
	{
		long h = t / (60 * 60 * 1000);
		t %= 60 * 60 * 1000;

		long m = t / (60 * 1000);
		t %= 60 * 1000;

		long s = t / (1000);
		t %= 1000;

		long ms = t;

		return format(h,2)+":"+format(m,2)+":"+format(s,2)+"."+format(ms,3);
	}

	private static HashMap getHashFromResultSet(ResultSet rs, ResultSetMetaData md, boolean convertNull) throws SQLException {
		HashMap hm = new HashMap();
		for (int i=md.getColumnCount(); i > 0; i--) {
			String val = rs.getString(i);
			hm.put(md.getColumnName(i), (convertNull&&val==null)?"":val);
		}
		return hm;
	}

	private static String[] netelKat = { "GSW", "GW", "SW", "KANT" };
	private static Set netelSet = new HashSet();
	public static boolean isNetel(String kat) {
		if (netelSet.isEmpty()) for (int i=0;i<netelKat.length;++i) netelSet.add(netelKat[i]);
		return netelSet.contains(kat.toUpperCase());
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

	private static void out(Object o) { System.out.print(o); }
	private static void outl(Object o) { System.out.println(o); }
	private static void outflush() { System.out.flush(); }
	private static void err(Object o) { System.err.print(o); }
	private static void errl(Object o) { System.err.println(o); }
	private static void errflush() { System.err.flush(); }

}




















