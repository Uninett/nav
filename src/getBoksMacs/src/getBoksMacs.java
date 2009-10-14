/*
 * getBoksMacs
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

import java.io.*;
import java.util.*;
import java.net.*;
import java.text.*;

import java.sql.*;

import no.ntnu.nav.ConfigParser.*;
import no.ntnu.nav.Database.*;
import no.ntnu.nav.SimpleSnmp.*;
import no.ntnu.nav.logger.*;
import no.ntnu.nav.Path;

/**
 * getBoksMacs collects CAM and CDP data from routers/switches
 *
 * @version $LastChangedRevision$ $LastChangedDate$
 * @author Kristian Eide &lt;kreide@online.no&gt;
 */

class getBoksMacs
{
	public static final String configFile = (Path.sysconfdir + "/getBoksMacs.conf").replace('/', File.separatorChar);
	public static final String watchMacsFile = (Path.sysconfdir + "/watchMacs.conf").replace('/', File.separatorChar);
	public static final String scriptName = "getBoksMacs";
	public static final String logFile = (Path.localstatedir + "/log/getBoksMacs.log").replace('/', File.separatorChar);

	public static int NUM_THREADS = 24;
	public static final int SHOW_TOP = 25;

	public static final boolean DB_COMMIT = true;

	public static final boolean DUMP_CAM = true;

	/*
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
		String cf = null;
		String qNetbox = null;
		// Check arguments
		if (args.length > 0) {
			try {
				NUM_THREADS = Integer.parseInt(args[0]);
			} catch (NumberFormatException e) {
				// Assume this argument is a netbox name
				qNetbox = args[0].trim();
				System.out.println("Overriding netbox: " + qNetbox);
				// Is next arg number of threads?
				if (args.length > 1) {
					try {
						NUM_THREADS = Integer.parseInt(args[1]);
					} catch (NumberFormatException ee) {
						// Assume this argument is the name of the config file
						File f = new File(args[0]);
						if (f.exists() && !f.isDirectory()) {
							cf = f.getAbsolutePath();
							System.out.println("Overriding configfile: " + f.getAbsolutePath());
						}
						// Is next arg number of threads?
						if (args.length > 2) {
							try {
								NUM_THREADS = Integer.parseInt(args[2]);
								System.out.println("Overriding number of threads: " + NUM_THREADS);
							} catch (NumberFormatException eee) {
								System.out.println("Error, unrecognized argument: " + args[2]);
								return;
							}
						}
					}
				}
			}
			if (NUM_THREADS > 128) {
				System.out.println("Error, more than 128 threads not recommended, re-compile needed.");
				return;
			}
		}

		// Init logger
		Log.init(logFile, "getBoksData");

		Log.i("INIT", "============ getBoksData starting ============");
		Log.i("INIT", "Running with " + NUM_THREADS + " thread"+(NUM_THREADS>1?"s":"")+".");

		ConfigParser cp;
		try {
			if (cf == null) cf = configFile;
			cp = new ConfigParser(cf);
		} catch (IOException e) {
			Log.e("INIT", "Could not read config file: " + cf);
			return;
		}
		if (!Database.openConnection(scriptName, "nav")) {
			Log.e("INIT", "Could not connect to database!");
			return;
		}

		// Set MAX_MISSCNT
		int MAX_MISSCNT = 3;
		if (cp != null) {
			String s = cp.get("MaxMisscnt");
			if (s != null) {
				try {
					MAX_MISSCNT = Integer.parseInt(s);
				} catch (NumberFormatException e) {
					errl("Warning, MaxMisscnt must be a number: " + s);
				}
			}
		}

		// Load watchMacs
		try {
			int wmcnt=0;
			BufferedReader bf = new BufferedReader(new FileReader(watchMacsFile));
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
		ResultSet rs = Database.query("SELECT netboxid,REPLACE(mac::text, ':', '') AS mac FROM netboxmac");
		while (rs.next()) {
			macBoksId.put(rs.getString("mac"), rs.getString("netboxid"));
		}
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
			sysnameMap.put(sysname, rs.getString("netboxid"));

			// Ta med denne også for sikkerhets skyld
			String kat = rs.getString("catid").toLowerCase();
			if (isNetel(kat)) {
				// Stripp etter første '.'
				int i;
				if (sysname != null && (i=sysname.indexOf('.')) != -1) {
					sysname = sysname.substring(0, i);
					sysnameMap.put(sysname, rs.getString("netboxid"));
				}
			}
		}

		// Alle (HP) stacknames
		rs = Database.query("SELECT netboxid,val AS stackname FROM netboxinfo WHERE var='stackName'");
		while (rs.next()) {
			sysnameMap.put(rs.getString("stackname"), rs.getString("netboxid"));
		}

		// Og så alle "ekte" sysname
		rs = Database.query("SELECT netboxid,val AS sysname FROM netboxinfo WHERE var='sysname'");
		while (rs.next()) {
			sysnameMap.put(rs.getString("sysname"), rs.getString("netboxid"));
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
		QueryBoks.swportidMap = new HashMap();
		QueryBoks.swportNetboxSet = new HashSet();
		rs = Database.query("SELECT swportid,netboxid,ifindex FROM swport JOIN module USING(moduleid)");
		while (rs.next()) {
			String key = rs.getString("netboxid")+":"+rs.getString("ifindex");
			QueryBoks.swportidMap.put(key, rs.getString("swportid"));
			QueryBoks.swportNetboxSet.add(rs.getString("netboxid"));
		}
		dumpUsedTime = System.currentTimeMillis() - dumpBeginTime;
		outl(dumpUsedTime + " ms.");

		// Hent alle vlan som er blokkert av spanning-tree
		out("  swportblocked...");
		dumpBeginTime = System.currentTimeMillis();
		rs = Database.query("SELECT swportid,netboxid,ifindex,cs_at_vlan,swportblocked.vlan FROM swportblocked JOIN swport USING(swportid) JOIN module USING(moduleid) JOIN netbox USING(netboxid) JOIN type USING(typeid)");
		while (rs.next()) {
			String vlan = (rs.getBoolean("cs_at_vlan") ? rs.getString("vlan") : "");
			String key = rs.getString("netboxid")+":"+vlan;
			HashMap blockedIfind;
			if ( (blockedIfind=(HashMap)spanTreeBlocked.get(key)) == null) spanTreeBlocked.put(key, blockedIfind = new HashMap());
			blockedIfind.put(rs.getString("ifindex"), rs.getString("swportid"));
		}
		dumpUsedTime = System.currentTimeMillis() - dumpBeginTime;
		outl(dumpUsedTime + " ms.");


		getActiveVlansFromDB();


		// Alt fra swp_boks for duplikatsjekking
		out("  swp_boks...");
		dumpBeginTime = System.currentTimeMillis();
		HashSet swp = new HashSet();
		HashMap swp_d = new HashMap();
		rs = Database.query("SELECT swp_netboxid,netboxid,ifindex,to_netboxid,to_swportid,misscnt FROM swp_netbox");
		ResultSetMetaData rsmd = rs.getMetaData();
		//rs = Database.query("SELECT swp_boksid,boksid,modul,port,boksbak FROM swp_boks JOIN boks USING (boksid) WHERE sysName='sb-sw'");
		while (rs.next()) {
			String key = rs.getString("netboxid")+":"+rs.getString("ifindex")+":"+rs.getString("to_netboxid");
			swp.add(key);

			HashMap hm = getHashFromResultSet(rs, rsmd, false);
			swp_d.put(key, hm);

			// Vi trenger å vite om det befinner seg en GW|SW|KANT bak en gitt enhet
			String boksBakKat = (String)boksidKat.get(rs.getString("to_netboxid"));
			if (boksBakKat == null || isNetel(boksBakKat)) {
				foundBoksBakSwp.add(rs.getString("netboxid")+":"+rs.getString("ifindex"));
			}

		}
		dumpUsedTime = System.currentTimeMillis() - dumpBeginTime;
		outl(dumpUsedTime + " ms.");

		// Fetch OID db
		out("  OID db...");
		dumpBeginTime = System.currentTimeMillis();
		QueryBoks.oidDb = new HashMap();
		Map oidDb = QueryBoks.oidDb;
		rs = Database.query("SELECT netboxid,oidkey,snmpoid FROM netbox JOIN netboxsnmpoid USING(netboxid) JOIN snmpoid USING(snmpoidid)");
		while (rs.next()) {
			Map m;
			String nid = rs.getString("netboxid");
			if ( (m=(Map)oidDb.get(nid)) == null) oidDb.put(nid, m = new HashMap());
			m.put(rs.getString("oidkey"), rs.getString("snmpoid"));
		}
		dumpUsedTime = System.currentTimeMillis() - dumpBeginTime;
		outl(dumpUsedTime + " ms.");

		// netboxid+ifindex -> vlan
		QueryBoks.vlanMap = new HashMap();
		Map vlanMap = QueryBoks.vlanMap;
		rs = Database.query("SELECT netboxid,ifindex,vlan FROM swport JOIN module USING(moduleid) WHERE trunk='f' AND vlan IS NOT NULL");
		while (rs.next()) {
			vlanMap.put(rs.getString("netboxid")+":"+rs.getString("ifindex"), rs.getString("vlan"));
		}

		// netboxid+interface -> swportid
		QueryBoks.interfaceMap = new HashMap();
		Map interfaceMap = QueryBoks.interfaceMap;
		rs = Database.query("SELECT netboxid,ifindex,interface,swportid FROM swport JOIN module USING(moduleid) ORDER BY ifindex DESC");
		while (rs.next()) {
			interfaceMap.put(rs.getString("netboxid")+":"+rs.getString("ifindex"), rs.getString("swportid"));
			if (rs.getString("interface") != null) {
				interfaceMap.put(rs.getString("netboxid")+":"+rs.getString("interface"), rs.getString("swportid"));
			}
		}

		QueryBoks.mpMap = new HashMap();
		Map mpMap = QueryBoks.mpMap;
		rs = Database.query("SELECT netboxid,ifindex,module,interface FROM swport JOIN module USING(moduleid) WHERE interface IS NOT NULL");
		while (rs.next()) {
			mpMap.put(rs.getString("netboxid")+":"+rs.getString("ifindex"), new String[] { rs.getString("module"), rs.getString("interface") } );
		}


		// For CAM-logger, alle uavsluttede CAM-records (dvs. alle steder hvor til er null)
		if (DUMP_CAM) {
			out("  cam...");
			dumpBeginTime = System.currentTimeMillis();
			rs = Database.query("SELECT camid,netboxid,ifindex,REPLACE(mac::text, ':', '') AS mac,misscnt FROM cam WHERE (end_time = 'infinity' OR misscnt >= 0) AND netboxid IS NOT NULL ORDER BY end_time");
			while (rs.next()) {
				String key = rs.getString("netboxid")+":"+rs.getString("ifindex")+":"+rs.getString("mac");
				String[] oldkey;
				if ( (oldkey=(String[])unclosedCam.put(key, new String[] { rs.getString("camid"), rs.getString("misscnt") } )) != null) {
					// Set misscnt = NULL
					String camid = oldkey[0];
					Database.update("UPDATE cam SET misscnt = NULL, end_time = CASE end_time WHEN 'infinity' THEN now() ELSE end_time END WHERE camid='"+camid+"'");
					errl("Error, found duplicate in cam for key: " + key + " (camid: " + camid + ")");

/*
DELETE FROM cam WHERE end_time='infinity' AND (netboxid,ifindex,mac) IN (SELECT netboxid,ifindex,mac FROM cam WHERE end_time='infinity' GROUP BY netboxid,ifindex,mac HAVING COUNT(camid) > 1) AND start_time NOT IN (SELECT MIN(start_time) AS start_time FROM cam WHERE end_time='infinity' GROUP BY netboxid,ifindex,mac HAVING COUNT(camid) > 1)

SELECT * FROM cam WHERE end_time='infinity' AND (netboxid,ifindex,mac) IN (SELECT netboxid,ifindex,mac FROM cam WHERE end_time='infinity' GROUP BY netboxid,ifindex,mac HAVING COUNT(camid) > 1) AND start_time NOT IN (SELECT MIN(start_time) AS start_time FROM cam WHERE end_time='infinity' GROUP BY netboxid,ifindex,mac HAVING COUNT(camid) > 1)

if duplikat
  if ny record har end_time=infinity
     sett misscnt = NULL for eksisterende record
     legg ny record i hash
  else
     sett misscnt = NULL for record som har eldst end_time

*/
				}
			}
			dumpUsedTime = System.currentTimeMillis() - dumpBeginTime;
			outl(dumpUsedTime + " ms.");
		}

		//Database.setDefaultKeepOpen(true);
		if (qNetbox == null) {
			rs = Database.query("SELECT ip,ro,netboxid,typename,catid,sysName,vendorid,cdp,cs_at_vlan FROM netbox JOIN type USING(typeid) WHERE catid IN ('SW','EDGE','WLAN','GW','GSW') AND up='y' AND ro IS NOT NULL");
		} else
		if (qNetbox.equals("_gw")) {
			//rs = Database.query("SELECT ip,ro,boksid,typeid,typegruppe,kat,sysName FROM boks NATURAL JOIN type WHERE kat='GW'");
		} else
		if (qNetbox.equals("_sw")) {
			//rs = Database.query("SELECT ip,ro,boksid,typeid,typegruppe,kat,sysName FROM boks NATURAL JOIN type WHERE kat='SW'");
		} else
		if (qNetbox.equals("_kant")) {
			//rs = Database.query("SELECT ip,ro,boksid,typeid,typegruppe,kat,sysName FROM boks NATURAL JOIN type WHERE kat='EDGE'");
		} else {
			rs = Database.query("SELECT ip,ro,netboxid,typename,catid,sysName,vendorid,cdp,cs_at_vlan FROM netbox JOIN type USING(typeid) WHERE sysName='"+qNetbox+"' AND ro IS NOT NULL");
			//rs = Database.query("SELECT ip,ro,boksid,typeid,typegruppe,kat,sysName FROM boks NATURAL JOIN type WHERE prefiksid in (2089,1930) AND boksid != 241");
			//rs = Database.query("SELECT ip,ro,boksid,typeid,typegruppe,kat,sysName FROM boks NATURAL JOIN type WHERE typegruppe in ('cat-sw', 'ios-sw')");
		}
		//Database.setDefaultKeepOpen(false);

		Stack bdStack = new Stack();
		while (rs.next()) {
			BoksData bd = new BoksData();
			bd.ip = rs.getString("ip");
			bd.cs_ro = rs.getString("ro");
			bd.boksId = rs.getString("netboxid");
			bd.boksType = rs.getString("typename");
			bd.sysName = rs.getString("sysname");
			bd.kat = rs.getString("catid");
			bd.vendor = rs.getString("vendorid");
			bd.cdp = rs.getBoolean("cdp");
			bd.csAtVlan = rs.getBoolean("cs_at_vlan");
			bdStack.push(bd);
		}
		int antBd = bdStack.size();

		// Sett datastrukturer for alle tråder
		QueryBoks.DB_COMMIT = DB_COMMIT;

		QueryBoks.macBoksId = macBoksId;
		QueryBoks.boksIdName = boksIdName;
		QueryBoks.boksidKat = boksidKat;
		QueryBoks.boksidType = boksidType;
		QueryBoks.sysnameMap = sysnameMap;
		QueryBoks.downBoksid = downBoksid;

		QueryBoks.spanTreeBlocked = spanTreeBlocked;

		QueryBoks.cdpBoks = cdpBoks;
		QueryBoks.vlanBoksid = vlanBoksid;

		QueryBoks.oidDb = oidDb;

		QueryBoks.setFoundBoksBakSwp(foundBoksBakSwp);

		QueryBoks.unclosedCam = unclosedCam;
		QueryBoks.safeCloseBoksid = safeCloseBoksid;
		QueryBoks.watchMacs = watchMacs;

		// Indikerer om en tråd er ferdig
		QueryBoks.initThreadDone(NUM_THREADS);

		// Start activity monitor, every minute
		Timer activityTimer = new Timer();
		activityTimer.schedule(new ActivityMonitorTask(), 60 * 1000, 60 * 1000);

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
				Database.update("DELETE FROM swp_netbox WHERE swp_netboxid = '"+swp_boksid+"'");
				if (DB_COMMIT) Database.commit(); else Database.rollback();
			} else {
				missinc++;
				// Øk misscnt med 1
				Database.update("UPDATE swp_netbox SET misscnt=misscnt+1 WHERE swp_netboxid = '"+swp_boksid+"'");
				if (DB_COMMIT) Database.commit(); else Database.rollback();
			}

		}
		int swpResetCnt = QueryBoks.getSwpResetMisscnt();
		Log.d("STATS", "swp_netbox: A total of " + prependSpace(missinc,4) + " units were missed,   " + prependSpace(swpResetCnt,4) + " units were reset,   " + prependSpace(remcnt,4) + " units were removed.");

		int[] camCnt = finishCam(MAX_MISSCNT);
		int camMissinc = camCnt[0];
		int camRemCnt = camCnt[1];
		int camResetCnt = QueryBoks.getCamResetMisscnt();
		Log.d("STATS", "cam       : A total of " + prependSpace(camMissinc,4) + " records were missed, " + prependSpace(camResetCnt,4) + " records were reset, " + prependSpace(camRemCnt,4) + " records were closed.");

		ArrayList boksReport = QueryBoks.boksReport;
		Collections.sort(boksReport);

		digits = String.valueOf(Math.min(SHOW_TOP, boksReport.size())).length();
		for (int i=0; i < SHOW_TOP && i < boksReport.size(); i++) {
			BoksReport br = (BoksReport)boksReport.get(i);
			Log.d("STATS", format(i+1, digits)+": " + formatTime(br.getUsedTime()) + ", " + br.getBoksData().sysName + " (" + br.getBoksData().boksType + ") (" + br.getBoksData().ip + ")");
		}

		Database.closeConnection();
		Log.d("STATS", "All done, time used: " + formatTime(usedTime) + ".");

		// Create a job-finished file
		try {
			char sep = File.separatorChar;
			File f = new File(Path.localstatedir+sep+"run"+sep+"boksmacs-finished.flag");
			f.createNewFile() ;
		} catch (SecurityException e) {
			errl("Error, cannot write to user.dir: " + e.getMessage() );
		} catch (IOException e) {
			errl("Cannot create job-finished, got IOException: " + e.getMessage() );
		}

		outflush();
		errflush();
		System.exit(0);


	}

	private static void getActiveVlansFromDB() throws SQLException {
		long dumpBeginTime;
		long dumpUsedTime;
		ResultSet rs;
		// Hent alle aktive vlan
		out("  vlan...");
		dumpBeginTime = System.currentTimeMillis();
		// Get VLANs from netbox_vtpvlan and swportvlan, or fall back to using swportallowedvlan
		{
			rs = Database.query("SELECT netboxid,vtpvlan FROM netbox_vtpvlan");
			while (rs.next()) {
				Set s;
				String boksid = rs.getString("netboxid");
				if ( (s=(Set)vlanBoksid.get(boksid)) == null) vlanBoksid.put(boksid, s = new TreeSet());
				s.add(new Integer(rs.getInt("vtpvlan")));
			}
			Set vtpBoksid = vlanBoksid.keySet();
			rs = Database.query("SELECT DISTINCT netboxid,vlan.vlan FROM module JOIN swport USING(moduleid) JOIN swportvlan USING(swportid) JOIN vlan USING(vlanid)");
			while (rs.next()) {
				Set s;
				String boksid = rs.getString("netboxid");
				if ( (s=(Set)vlanBoksid.get(boksid)) == null) vlanBoksid.put(boksid, s = new TreeSet());
				s.add(new Integer(rs.getInt("vlan")));
			}
			
			rs = Database.query("SELECT DISTINCT vlan FROM vlan WHERE vlan IS NOT NULL");
			List tmp = new ArrayList();
			while (rs.next()) tmp.add(new Integer(rs.getInt("vlan")));
			int[] vlanList = new int[tmp.size()];
			{
				int i=0;
				for (Iterator it=tmp.iterator(); it.hasNext(); i++) vlanList[i] = ((Integer)it.next()).intValue();
			}

			rs = Database.query("SELECT netboxid,hexstring FROM swport JOIN module USING(moduleid) JOIN swportallowedvlan USING (swportid)");
			while (rs.next()) {
				String boksid = rs.getString("netboxid");
				if (!vtpBoksid.contains(boksid)) {
					Set s;
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
		}
		rs = Database.query("SELECT DISTINCT netboxid,vlan FROM swport JOIN module USING(moduleid) WHERE trunk='f' AND vlan IS NOT NULL");
		while (rs.next()) {
			Set s;
			String boksid = rs.getString("netboxid");
			if ( (s=(Set)vlanBoksid.get(boksid)) == null) vlanBoksid.put(boksid, s = new TreeSet());
			s.add(new Integer(rs.getInt("vlan")));
		}
		dumpUsedTime = System.currentTimeMillis() - dumpBeginTime;
		outl(dumpUsedTime + " ms.");
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
			int misscnt=0;
			try {
				misscnt = Integer.parseInt(s[1]);
			} catch (NumberFormatException e) {
			}
			misscnt++;

			if (misscnt > MAX_MISSCNT) {
				// Nå skal vi virkelig lukke denne recorden
				try {
					String[] updateFields = {
						"misscnt", "null"
					};
					String[] condFields = {
						"camid", camid
					};
					Database.update("cam", updateFields, condFields);
					if (DB_COMMIT) Database.commit(); else Database.rollback();
				} catch (SQLException e) {
					outl("  finishCam(): Closing record in cam, SQLException: " + e.getMessage() );
				}
				remCnt++;
			} else {
				// Misscnt-feltet økes med en; dersom det var 0 fra før skal til settes til NOW()
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
					Database.update("cam", updateFields, condFields);
					if (DB_COMMIT) Database.commit(); else Database.rollback();
				} catch (SQLException e) {
					outl("  finishCam(): Semi-closing record in cam, SQLException: " + e.getMessage() );
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

	private static String[] netelKat = { "GSW", "GW", "SW", "EDGE", "WLAN" };
	private static Set netelSet = new HashSet();
	public static boolean isNetel(String kat) {
		if (netelSet.isEmpty()) for (int i=0;i<netelKat.length;++i) netelSet.add(netelKat[i]);
		return netelSet.contains(kat.toUpperCase());
	}

	private static boolean isAllowedVlan(String hexstr, int vlan)
	{
		if (hexstr.length() >= 256) {
			return isAllowedVlanFwd(hexstr, vlan);
		}
		return isAllowedVlanRev(hexstr, vlan);
	}

	private static boolean isAllowedVlanFwd(String hexstr, int vlan)
	{
		if (vlan < 0 || vlan > 4095) return false;
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

class ActivityMonitorTask extends TimerTask {
	public void run() {
		if (QueryBoks.lastActivity < (System.currentTimeMillis() - 60*60*1000)) {
			// No activity in the last hour, exit
			System.err.println("Exiting due to no activity in the last hour");
			System.err.flush();
			System.exit(1);
		}
	}
}



















