/*
 *
 *
 *
 */

import java.io.*;
import java.util.*;
import java.net.*;
import java.text.*;

import java.sql.*;

import uk.co.westhawk.snmp.stack.*;
import uk.co.westhawk.snmp.pdu.*;


class getBoksMacsMulti
{
	public static final String navRoot = "/usr/local/nav/";
	public static final String configFile = "etc/getBoksMacs.conf";

	public static final int NUM_THREADS = 64;
	public static final int SHOW_TOP = 25;
	public static final boolean VERBOSE_OUT = false;
	public static final boolean DEBUG_OUT = false;
	public static final boolean DB_UPDATE = true;
	public static final boolean DB_COMMIT = true;

	// Felles datastrukturer som bare skal leses fra
	static HashMap macBoksId = new HashMap();
	static HashMap boksIdName = new HashMap();
	static HashMap sysnameMap = new HashMap();

	static HashMap spanTreeBlocked = new HashMap();
	static HashMap swportIfindex = new HashMap();

	static HashSet ciscoBoks = new HashSet();
	static String[] vlanList;

	public static void main(String[] args) throws SQLException
	{

		ConfigParser cp;
		try {
			cp = new ConfigParser(navRoot + configFile);
		} catch (IOException e) {
			outl("Error, could not read config file: " + navRoot + configFile);
			return;
		}
		if (!Database.openConnection(cp.get("SQLServer"), cp.get("SQLDb"), cp.get("SQLUser"), cp.get("SQLPw"))) {
			outl("Error, could not connect to database!");
			return;
		}

		// Hent kobling mellom mac<->boksid og mac<->sysName
		//ResultSet rs = Database.query("SELECT mac,boksid,sysName FROM boksmac NATURAL JOIN boks");
		ResultSet rs = Database.query("SELECT mac,boksid FROM boksmac");
		while (rs.next()) macBoksId.put(rs.getString("mac"), rs.getString("boksid"));

		// Hent kobling mellom boksid<->sysName og motsatt
		rs = Database.query("SELECT boksid,sysName,kat FROM boks");
		while (rs.next()) {
			boksIdName.put(rs.getString("boksid"), rs.getString("sysname"));
			String sysname = rs.getString("sysname");
			String kat = rs.getString("kat").toLowerCase();
			if (kat.equals("gw") || kat.equals("sw") || kat.equals("kant")) {
				// Stripp etter første '.'
				int i;
				if ( (i=sysname.indexOf('.')) != -1) {
					sysname = sysname.substring(0, i);
				}
			}
			sysnameMap.put(sysname, rs.getString("boksid"));
			//System.out.println("Lagt til: " + sysname + " kat: " + kat);
		}

		// Vi trenger å vite alle boksid+ifindex som eksisterer i swport
		rs = Database.query("SELECT DISTINCT ON (boksid,ifindex) swportid,boksid,ifindex FROM swport");
		while (rs.next()) {
			swportIfindex.put(rs.getString("boksid")+":"+rs.getString("ifindex"), rs.getString("swportid"));
		}

		// Hent alle vlan som er blokkert av spanning-tree
		rs = Database.query("SELECT swportid,boksid,ifindex,vlan FROM swportblocked NATURAL JOIN swport");
		while (rs.next()) {
			String key = rs.getString("boksid")+":"+rs.getString("vlan");
			HashMap blockedIfind;
			if (spanTreeBlocked.containsKey(key)) {
				blockedIfind = (HashMap)spanTreeBlocked.get(key);
			} else {
				blockedIfind = new HashMap();
				spanTreeBlocked.put(key, blockedIfind);
			}
			blockedIfind.put(rs.getString("ifindex"), rs.getString("swportid"));
		}

		// Denne inneholder alle "boksid:ifindex" fra swport som er trunk-porter
		/*
		QueryBoks.boksIfindexTrunkSet = new HashSet();
		rs = Database.query("SELECT boksid,ifindex FROM swport WHERE trunk='t'");
		while (rs.next()) {
			QueryBoks.boksIfindexTrunkSet.add(rs.getString("boksid")+":"+rs.getString("ifindex"));
		}
		*/

		// Mapping fra boksid, port og modul til swportid i swport
		QueryBoks.swportSwportidMap = new HashMap();
		rs = Database.query("SELECT swportid,boksid,modul,port FROM swport");
		while (rs.next()) {
			String key = rs.getString("boksid")+":"+rs.getString("modul")+":"+rs.getString("port");
			QueryBoks.swportSwportidMap.put(key, rs.getString("swportid"));
		}

		// Hent alle bokser der kat='GW'
		QueryBoks.boksGwSet = new HashSet();
		rs = Database.query("SELECT boksid FROM boks WHERE kat='GW'");
		while (rs.next()) {
			QueryBoks.boksGwSet.add(rs.getString("boksid"));
		}

		// Hent alle bokser av type 'cisco'
		rs = Database.query("SELECT boksid FROM boks NATURAL JOIN type WHERE lower(descr) LIKE '%cisco%'");
		while (rs.next()) {
			ciscoBoks.add(rs.getString("boksid"));
		}


		// Hent alle aktive vlan
		rs = Database.query("SELECT DISTINCT vlan FROM prefiks WHERE vlan IS NOT null");
		vlanList = new String[rs.getFetchSize()];
		for (int i=0; rs.next(); i++) vlanList[i] = rs.getString("vlan");

		// Alt fra swp_boks for duplikatsjekking
		HashSet swp = new HashSet();
		HashMap swp_d = new HashMap();
		rs = Database.query("SELECT swp_boksid,boksid,modul,port,boksbak FROM swp_boks");
		//rs = Database.query("SELECT swp_boksid,boksid,modul,port,boksbak FROM swp_boks JOIN boks USING (boksid) WHERE sysName='sb-sw'");
		while (rs.next()) {
			String key = rs.getString("boksid")+":"+rs.getString("modul")+":"+rs.getString("port")+":"+rs.getString("boksbak");
			String[] val = { rs.getString("swp_boksid"), rs.getString("boksid"), rs.getString("modul"), rs.getString("port"), rs.getString("boksbak") };
			swp.add(key);
			swp_d.put(key, val);
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
		//qNettel = "sb-353-sw";
		//qNettel = "hyper-sw";

		Database.setDefaultKeepOpen(true);
		if (qNettel.equals("_new")) {
			rs = Database.query("SELECT ip,ro,boksid,typeid,typegruppe,kat,sysName FROM boks NATURAL JOIN type WHERE NOT EXISTS (SELECT boksid FROM swp_boks WHERE boksid=boks.boksid) AND (kat='KANT' or kat='SW') ORDER BY boksid");
		} else
		if (qNettel.equals("_all")) {
			rs = Database.query("SELECT ip,ro,boksid,typeid,typegruppe,kat,sysName FROM boks NATURAL JOIN type WHERE kat='SW' OR kat='KANT' OR kat='GW'");
		} else
		if (qNettel.equals("_gw")) {
			rs = Database.query("SELECT ip,ro,boksid,typeid,typegruppe,kat,sysName FROM boks NATURAL JOIN type WHERE kat='GW'");
		} else
		if (qNettel.equals("_sw")) {
			rs = Database.query("SELECT ip,ro,boksid,typeid,typegruppe,kat,sysName FROM boks NATURAL JOIN type WHERE kat='SW'");
		} else
		if (qNettel.equals("_kant")) {
			rs = Database.query("SELECT ip,ro,boksid,typeid,typegruppe,kat,sysName FROM boks NATURAL JOIN type WHERE kat='KANT'");
		} else {
			rs = Database.query("SELECT ip,ro,boksid,typeid,typegruppe,kat,sysName FROM boks NATURAL JOIN type WHERE sysName='"+qNettel+"'");
		}
		Database.setDefaultKeepOpen(false);

		Stack bdStack = new Stack();
		while (rs.next()) {
			BoksData bd = new BoksData();
			bd.ip = rs.getString("ip");
			bd.cs_ro = rs.getString("ro");
			bd.boksId = rs.getString("boksid");
			bd.boksTypegruppe = rs.getString("typegruppe");
			bd.boksType = rs.getString("typeid");
			bd.sysName = rs.getString("sysname");
			bd.kat = rs.getString("kat");
			//bd.vekt = vekt;
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
		QueryBoks.sysnameMap = sysnameMap;

		QueryBoks.spanTreeBlocked = spanTreeBlocked;
		QueryBoks.swportIfindex = swportIfindex;

		QueryBoks.ciscoBoks = ciscoBoks;
		QueryBoks.vlanList = vlanList;

		// Indikerer om en tråd er ferdig
		QueryBoks.initThreadDone(NUM_THREADS);

		// Lag trådene
		long beginTime = new java.util.GregorianCalendar().getTime().getTime();
		Thread[] threads = new Thread[NUM_THREADS];
		int digits = String.valueOf(NUM_THREADS-1).length();
		for (int i=0; i < NUM_THREADS; i++) {
			threads[i] = new QueryBoks(i, format(i, digits), bdStack, antBd, swp, swp_d);
			threads[i].start();
		}

		for (int i=0; i < NUM_THREADS; i++) {
			try {
				threads[i].join();
			} catch (InterruptedException e) { }
		}
		long usedTime = new java.util.GregorianCalendar().getTime().getTime() - beginTime;

		// Sjekk om det er enheter som har forsvunnet
		Iterator iter = swp_d.values().iterator();
		if (iter.hasNext()) outl("Units no longer present:");

		int remCnt=0;
		while (iter.hasNext()) {
			String[] s = (String[]) iter.next();
			String swpid = s[0];
			String boks = (String)boksIdName.get(s[1]);
			String modul = s[2];
			String port = s[3];
			String boksbak = (String)boksIdName.get(s[4]);

			remCnt++;

			String rem = "";
			//outl("  [Rem] Boks: " + boks + " Modul: " + modul + " Port: " + port + " Boksbak: " + boksbak + rem);

			/*
			String[] s = (String[]) iter.next();
			String id = s[0];
			String nid = s[1];
			String port = s[2];
			String idbak = s[3];
			String type = s[4];

			//if (!id.equals("48")) continue;

			remCnt++;
			//db.exec("DELETE from swp_nettel WHERE id='" + id + "'");
			outl("  Rem: Nettel("+nid+"): " + nettelNavn.get(nid) + " ("+type+") Port: " + port + " idbak("+idbak+"): " + nettelNavn.get(idbak) + " (removed)");
			*/
		}
		if (remCnt>0) outl("A total of " + remCnt + " units are no longer present.");

		ArrayList boksReport = QueryBoks.boksReport;
		Collections.sort(boksReport);

		digits = String.valueOf(Math.min(SHOW_TOP, boksReport.size())).length();
		for (int i=0; i < SHOW_TOP && i < boksReport.size(); i++) {
			BoksReport br = (BoksReport)boksReport.get(i);
			outl(format(i+1, digits)+": " + formatTime(br.getUsedTime()) + ", " + br.getBoksData().sysName + " (" + br.getBoksData().boksType + ") (" + br.getBoksData().ip + ")");
		}

		Database.closeConnection();
		outl("All done, time used: " + formatTime(usedTime) + ".");
		System.exit(0);


	}

	private static String format(long i, int n)
	{
		DecimalFormat nf = new DecimalFormat("#");
		nf.setMinimumIntegerDigits(n);
		return nf.format(i);
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

		return format(h,2)+":"+format(m,2)+":"+format(s,2)+"."+format(ms,4);
	}

	private static void out(String s) { System.out.print(s); }
	private static void outl(String s) { System.out.println(s); }

}

class QueryBoks extends Thread
{
	public static boolean VERBOSE_OUT = false;
	public static boolean DEBUG_OUT = false;
	public static boolean DB_UPDATE = false;
	public static boolean DB_COMMIT = false;

	// Felles datastrukturer som bare skal leses fra
	public static HashMap macBoksId;
	public static HashMap boksIdName;
	public static HashMap sysnameMap;

	public static HashMap spanTreeBlocked;
	public static HashMap swportIfindex;

	public static HashSet ciscoBoks;

	// Inneholder alle boksid'er som er av kat=GW
	public static HashSet boksGwSet;

	// Mapping fra boksid, port og modul til swportid i swport
	public static HashMap swportSwportidMap;

	// Denne inneholder alle "boksid:ifindex" fra swport som er trunk-porter
	//public static HashSet boksIfindexTrunkSet;

	// Liste over vlan som må sjekkes på Cisco-boksene
	public static String[] vlanList;

	// Køen som inneholder alle boksene, delt mellom trådene
	Stack bdStack;
	// Hvilke tråder som er ferdig
	static boolean[] threadDone;

	// Rapport når en boks er ferdigbehandlet
	static ArrayList boksReport = new ArrayList();

	// Objekt-spesifikke data
	int num;
	String id;
	int antBd;

	HashSet swp;
	HashMap swp_d;
	HashSet foundCDPMp = new HashSet();

	SimpleSnmp sSnmp = new SimpleSnmp();

	// Konstruktør
	public QueryBoks(int num, String id, Stack bdStack, int antBd, HashSet swp, HashMap swp_d)
	{
		this.num = num;
		this.id = id;
		this.bdStack = bdStack;
		this.antBd = antBd;
		this.swp = swp;
		this.swp_d = swp_d;
	}

	public static void initThreadDone(final int NUM_THREADS)
	{
		threadDone = new boolean[NUM_THREADS];
		for (int i=0; i < threadDone.length; i++) {
			threadDone[i] = false;
		}
	}


	private static String[] modulNameShorts = {
		"FastEthernet", "Fa",
		"GigabitEthernet", "Gi"
	};
	private static String processModulName(String modul)
	{
		for (int j=0; j<modulNameShorts.length; j+=2) {
			if (modul.startsWith(modulNameShorts[j])) modul = modulNameShorts[j+1]+modul.substring(modulNameShorts[j].length(), modul.length());
		}
		return modul;
	}


	public void run()
	{
		long beginTime = new java.util.GregorianCalendar().getTime().getTime();

		while (true) {
			BoksData bd;
			int bdRemaining;
			synchronized (bdStack) {
				if (!bdStack.empty()) {
					bd = (BoksData)bdStack.pop();
					bdRemaining = bdStack.size();
				} else {
					// Stack er tom, altså er vi ferdig
					break;
				}
			}

			String ip = bd.ip;
			String cs_ro = bd.cs_ro;
			String boksId = bd.boksId;
			String boksTypegruppe = bd.boksTypegruppe;
			String boksType = bd.boksType;
			String sysName = bd.sysName;
			String kat = bd.kat;

			outla("T"+id+": Now working with("+boksId+"): " + sysName + " ("+ boksType +") ("+ ip +") ("+ bdRemaining +" of "+ antBd+" left)");
			long boksBeginTime = new java.util.GregorianCalendar().getTime().getTime();

			// Liste over alle innslagene vi evt. skal sette inn i swp_boks
			ArrayList boksListe = new ArrayList();

			// Liste over porter der vi har funnet boks via CDP
			foundCDPMp.clear();

			// OK, prøv å spørre
			try {
				// Hvis dette er Cisco utstyr trenger vi ifindexMp kobling, og vi må hente CDP info
				HashMap ifindexMp = null;
				if (boksTypegruppe.equals("cgw-nomem") ||
					boksTypegruppe.equals("cgw") ||
					boksTypegruppe.equals("ios-sw") ||
					boksTypegruppe.equals("cat-sw") ||
					boksTypegruppe.equals("cat1900-sw") ||
					boksTypegruppe.equals("catmeny-sw") ) {

					ifindexMp = fetchIfindexMpMap(ip, cs_ro, boksTypegruppe);

					boolean decodeHex = false;
					/*
					if (boksTypegruppe.equals("cat1900-sw") ||
						boksTypegruppe.equals("catmeny-sw") ) {
						decodeHex = true;
					}
					*/

					ArrayList l = processCDPNorm(boksId, ip, cs_ro, ifindexMp, decodeHex);
					boksListe.addAll(l);

				}

				if (kat.equals("GW")) {
					// GW'er behandles annerledes, vi skal oppdatere boksbak og evt. swportbak i gwport

					for (int i=0; i < boksListe.size(); i++) {

						PortBoks pm = (PortBoks)boksListe.get(i);
						String key = boksId+":"+pm;
						String remoteIf = pm.getRemoteIf();
						if (remoteIf == null) {
							outld("  Error, remoteIf is null for gw("+boksId+") " + sysName + ", boksbak: " + pm.getBoksId());
							continue;
						}

						String remoteSwportid;
						if (boksGwSet.contains(pm.getBoksId())) {
							// Link til gw, vi har da ingen swportid
							remoteSwportid = "null";
						} else {
							// Link til ikke-gw, da skal vi finne swportid
							// Hent ut modul / port
							StringTokenizer st = new StringTokenizer(remoteIf, "/");
							if (st.countTokens() != 2) {
								outld("  Error, remoteIf is not in modul/port format: " + remoteIf);
								continue;
							}

							// Finn remote swportid
							String modul = st.nextToken();
							String port = st.nextToken();

							// Hvis modul inneholder f.eks FastEther0 skal dette forkortes til Fa0
							modul = processModulName(modul);

							String remoteKey = pm.getBoksId()+":"+modul+":"+port;
							remoteSwportid = (String)swportSwportidMap.get(remoteKey);
							if (remoteSwportid == null) {
								outld("  Error, could not find swportid for ("+pm.getBoksId()+") "+boksIdName.get(pm.getBoksId())+" Modul: " + modul + " Port: " + port);
								continue;
							}
						}

						// OK, da er vi klar, oppdater gwport!
						if (boksType.equals("MSFC") ||
							boksType.equals("RSM") ) {

							if (DB_UPDATE) Database.update("UPDATE gwport SET boksbak = '"+pm.getBoksId()+"', swportbak = "+remoteSwportid+" WHERE boksid = '"+boksId+"' AND prefiksid IS NOT NULL");
							if (DB_COMMIT) Database.commit();
							outl("    ["+boksType+"] Ifindex: " + pm.getIfindex() + " Interface: " + pm.getModulS() + ", " + boksIdName.get(pm.getBoksId()) );
							continue;
						}

						String[] updateFields = {
							"boksbak", pm.getBoksId(),
							"swportbak", remoteSwportid
						};
						String[] condFields = {
							"boksid", boksId,
							"ifindex", pm.getIfindex()
						};
						if (DB_UPDATE) Database.update("gwport", updateFields, condFields);
						if (DB_COMMIT) Database.commit();
						outl("    [GW] Ifindex: " + pm.getIfindex() + " Interface: " + pm.getModulS() + ", " + boksIdName.get(pm.getBoksId()) );
					}

					long boksUsedTime = new java.util.GregorianCalendar().getTime().getTime() - beginTime;
					synchronized (boksReport) {
						boksReport.add(new BoksReport((int)boksUsedTime, bd));
					}
					continue;
				}

				// Hent inn boksbak via matching mot MAC-adresser
				ArrayList macListe = null;
				if (boksTypegruppe.equals("cat1900-sw")) {
					macListe = processCisco1900(boksId, ip, cs_ro, boksType, ifindexMp);
				} else
				if (boksTypegruppe.equals("catmeny-sw")) {
					macListe = processCisco1Q(boksId, ip, cs_ro, boksType);
				} else
				if (boksTypegruppe.equals("cat-sw") || boksTypegruppe.equals("ios-sw")) {
					// Cisco utstyr der man må hente per vlan
					macListe = processCisco2Q(boksId, ip, cs_ro, boksTypegruppe, boksType, ifindexMp);
				} else
				if (boksTypegruppe.equals("3hub") || boksTypegruppe.equals("3ss") || boksTypegruppe.equals("3ss9300")) {
					// Alt 3Com utstyr
					macListe = process3Com(boksId, ip, cs_ro, boksTypegruppe, boksType);
				} else {
					outl("  Error, unknown typegruppe: " + boksTypegruppe);
				}
				if (macListe != null) {
					// Før MAC-listen kan legges til boksListe må alle konflikter med CDP tas bort
					for (int i=0; i < macListe.size(); i++) {
						PortBoks pm = (PortBoks)macListe.get(i);
						String key = pm.getModul()+":"+pm.getPort();
						if (foundCDPMp.contains(key)) {
							// Vi har funnet CDP på denne porten, er dette en cisco enhet skal den ikke være med
							if (ciscoBoks.contains(pm.getBoksId())) {
								outl("    [DEL] Modul: " + pm.getModulS() + " Port: " + pm.getPortS() + ", " + boksIdName.get(pm.getBoksId()) );
								continue;
							}
						}
						boksListe.add(pm);
					}
				}
			} catch (SQLException se) {
				outld("*ERROR* SQLException: " + se.getMessage());
			} catch (TimeoutException te) {
				outl("T"+id+":   *ERROR*, TimeoutException: " + te.getMessage());
				outla("T"+id+":   *** GIVING UP ON: " + sysName + ", typeid: " + boksType + " ***");
				continue;
			}

			int newCnt=0,dupCnt=0;
			for (int i=0; i < boksListe.size(); i++) {

				PortBoks pm = (PortBoks)boksListe.get(i);
				String key = boksId+":"+pm;

				// En enhet kan ikke ha link til seg selv
				if (boksId.equals(pm.getBoksId())) continue;

				// Sjekk om dette er en duplikat
				if (swp.contains(key)) {
					synchronized (swp_d) {
						swp_d.remove(key);
					}
					//outl("T"+id+":    [DUP] Modul: " + pm.getModulS() + " Port: " + pm.getPortS() + ", " + getBoksMacsMulti.boksIdName.get(pm.getBoksId()) );
					dupCnt++;
					continue;
				}

				// Legg til i listen så vi ikke får duplikater
				synchronized (swp) {
					swp.add(key);
				}
				//outl("T"+id+":    ["+pm.getSource()+"] Modul: " + pm.getModulS() + " Port: " + pm.getPortS() + ", " + getBoksMacsMulti.boksIdName.get(pm.getBoksId()) );

				String[] insertData = {
					"boksid", boksId,
					"modul", pm.getModul(),
					"port", pm.getPort(),
					"boksbak", pm.getBoksId()
				};
				if (DB_UPDATE) {
					try {
						Database.insert("swp_boks", insertData);
						if (DB_COMMIT) Database.commit();
						newCnt++;
					} catch (SQLException e) {
						outld("ERROR, SQLException: " + e.getMessage() );
					}
				} else {
					newCnt++;
				}
			}
			if (newCnt > 0 || dupCnt > 0) {
				outl("T"+id+": Fount a total of " + newCnt + " new units, " + dupCnt + " duplicate units.");
			}

			long boksUsedTime = new java.util.GregorianCalendar().getTime().getTime() - boksBeginTime;
			synchronized (boksReport) {
				boksReport.add(new BoksReport((int)boksUsedTime, bd));
			}
			/*
			Database.update("UPDATE type SET snmptid = snmptid+"+usedTime+", snmpcnt = snmpcnt+1 WHERE typeid = '"+boksType+"'");
			Database.commit();
			*/
		}
		long usedTime = new java.util.GregorianCalendar().getTime().getTime() - beginTime;
		threadDone[num] = true;
		outla("T"+id+": ** Thread done, time used: " + getBoksMacsMulti.formatTime(usedTime) + ", waiting for " + getThreadsNotDone() + " **");

	}

	private String getThreadsNotDone()
	{
		StringBuffer sb = new StringBuffer();
		int startRange=0;
		boolean markLast=false;

		for (int i=0; i < threadDone.length+1; i++) {
			if (i != threadDone.length && !threadDone[i]) {
				if (!markLast) {
					startRange=i;
					markLast = true;
				}
			} else if (markLast) {
				String range = (startRange==i-1) ? String.valueOf(i-1) : startRange+"-"+(i-1);
				sb.append(","+range);
				markLast=false;
			}
		}
		if (sb.length() > 0) {
			sb.setCharAt(0, '[');
		} else {
			sb.insert(0, "[");
		}
		sb.append("]");
		return sb.toString();
	}

	/*
	 * Cisco CDP
	 *
	 */
	private ArrayList processCDPNorm(String workingOnBoksid, String ip, String cs_ro, HashMap ifindexMp, boolean decodeHex) throws SQLException, TimeoutException
	{
		ArrayList l = new ArrayList();

		String baseOid = ".1.3.6.1.4.1.9.9.23.1.2.1.1.6";
		sSnmp.setParams(ip, cs_ro, baseOid);
		ArrayList cdpList = sSnmp.getAll(true);

		if (cdpList.size() == 0) return l;

		for (int i=0; i<cdpList.size(); i++) {
			String[] macs = (String[])cdpList.get(i);

			String ifind = macs[0].substring(0, macs[0].indexOf("."));
			String[] mp = (String[])ifindexMp.get(ifind);

			if (mp == null) {
				String[] s = {
					"1",
					ifind
				};
				mp = s;
				outl("  *WARNING*: ifindex mapping not found, using Modul: " + mp[0] + " Port: " + mp[1] + " String: " + macs[1]);

			}

			//if (decodeHex || macs[1].startsWith("0x")) macs[1] = hex2ascii(macs[1]);

			String boksid = extractBoksid(macs[1]);
			if (boksid != null) {
				String sysname = (String)boksIdName.get(boksid);

				//System.out.print("Modul: " + mp[0] + " Port: " + mp[1]);
				//System.out.println("  *Sysname: " + sysname + ", boksid: " + boksid);
			} else {
				outld("  *WARNING*: Not found, ("+workingOnBoksid+") "+boksIdName.get(workingOnBoksid)+", Modul: " + mp[0] + " Port: " + mp[1] + " String: " + macs[1]);
				continue;
			}

			// Opprett record for boksen bak porten
			PortBoks pm = new PortBoks(mp[0], mp[1], boksid, "CDP");
			pm.setIfindex(ifind);
			l.add(pm);

			String key = pm.getModul()+":"+pm.getPort();
			foundCDPMp.add(key);

			// Dersom vi denne porten går fra ikke-gw (sw) til gw må vi hente remote interface og slå opp i gwport
			// slik at vi kan sette boksbak og swportbak.
			if (!boksGwSet.contains(workingOnBoksid) && boksGwSet.contains(boksid)) {
				// OK, ikke-gw -> gw
				String swportid = (String)swportIfindex.get(workingOnBoksid+":"+ifind);
				if (swportid != null) {
					// Først trenger vi å vite hvilke interf vi har i andre enden
					String remoteIf;
					{
						sSnmp.setBaseOid(".1.3.6.1.4.1.9.9.23.1.2.1.1.7."+ifind);
						ArrayList remoteIfList = sSnmp.getAll(true);
						if (remoteIfList.size() == 0) {
							outla("*ERROR*, should not happen, not found CDP remote device");
							continue;
						}
						remoteIf = ((String[])remoteIfList.get(0))[1];
						int k;
						if ( (k=remoteIf.lastIndexOf('.')) != -1) remoteIf = remoteIf.substring(0, k);
						//if (k == -1) {
						//	outld("  Not subinterface on ("+boksid+")"+boksIdName.get(boksid)+": " + remoteIf);
						//}
					}

					// Setter boksbak og swportbak for alle matchende interfacer
					int updCnt = Database.update("UPDATE gwport SET boksbak = '"+workingOnBoksid+"', swportbak = '"+swportid+"' WHERE gwportid IN (SELECT gwportid FROM gwport JOIN prefiks USING(prefiksid) WHERE vlan IS NOT NULL AND boksid='"+boksid+"' AND interf like '"+remoteIf+"%')");
					//if (updCnt > 0) {
					//	outld("  Updated " + updCnt + " rows with boksbak ("+workingOnBoksid+")"+boksIdName.get(workingOnBoksid)+", swportid " + swportid + " on ("+boksid+")"+boksIdName.get(boksid)+", " + remoteIf);
					//}

					/*
					// OK, kjenner remote interface, nå kan vi slå opp for å finne alle vlan
					// Slette vlan som ikke lenger kjører over trunken
					Database.update("DELETE FROM swportvlan WHERE swportid='"+swportid+"' AND vlan NOT IN (SELECT vlan FROM gwport JOIN prefiks USING(prefiksid) WHERE vlan IS NOT NULL AND boksid='"+boksid+"' AND interf like '"+remoteIf+"%')");

					// Kjekk SQL-setning for å finne alle trunker til gw uten vlan satt
					// SELECT swportid,boksid,sysname,ifindex,modul,port,vlan,retning FROM swport JOIN boks USING (boksid) NATURAL LEFT JOIN swportvlan WHERE trunk='t' AND vlan IS NULL AND boksbak IN (SELECT boksid FROM boks WHERE kat='GW');

					if (DEBUG_OUT) {
						boolean printMsg = false;
						ResultSet rs = Database.query("SELECT DISTINCT ON (vlan) '"+swportid+"',vlan,'g' FROM gwport JOIN prefiks USING(prefiksid) WHERE vlan IS NOT NULL AND boksid='"+boksid+"' AND interf like '"+remoteIf+"%' AND vlan NOT IN (SELECT vlan FROM swportvlan WHERE swportid='"+swportid+"')");
						// SELECT DISTINCT ON (vlan) 'swportid',vlan,'g' FROM gwport JOIN prefiks USING(prefiksid) WHERE vlan IS NOT NULL AND boksid='"+boksid+"' AND interf like '"+remoteIf+"%'
						while (rs.next()) {
							if (!printMsg) {
								outd("  Found vlans on trunk from ("+workingOnBoksid+")"+boksIdName.get(workingOnBoksid)+" to ("+boksid+")"+boksIdName.get(boksid)+", " + remoteIf + " [");
								printMsg = true;
								outd(rs.getString("vlan"));
							} else {
								outd(", " + rs.getString("vlan"));
							}
						}
						if (printMsg) outld("]");
					}

					// Så setter vi evt. nye inn i swportvlan
					Database.update("INSERT INTO swportvlan (swportid,vlan,retning) (SELECT DISTINCT ON (vlan) '"+swportid+"',vlan,'g' FROM gwport JOIN prefiks USING(prefiksid) WHERE vlan IS NOT NULL AND boksid='"+boksid+"' AND interf like '"+remoteIf+"%' AND vlan NOT IN (SELECT vlan FROM swportvlan WHERE swportid='"+swportid+"'))");
					// INSERT INTO swportvlan (swportid,vlan,retning) (SELECT DISTINCT ON (vlan) '1566',vlan,'a' FROM gwport JOIN prefiks USING(prefiksid) WHERE vlan IS NOT NULL AND boksid='28' AND interf like 'GigabitEthernet1/0/0%' AND vlan NOT IN (SELECT vlan FROM swportvlan WHERE swportid='1566'));
					*/
				}
			} else if (boksGwSet.contains(workingOnBoksid)) {
				// Vi jobber på en gw og må da hente remoteIf
				String remoteIf;
				{
					sSnmp.setBaseOid(".1.3.6.1.4.1.9.9.23.1.2.1.1.7."+ifind);
					ArrayList remoteIfList = sSnmp.getAll(true);
					if (remoteIfList.size() == 0) {
						outla("*ERROR*, should not happen, not found CDP remote device");
						continue;
					}
					remoteIf = ((String[])remoteIfList.get(0))[1];
					int k;
					if ( (k=remoteIf.lastIndexOf('.')) != -1) remoteIf = remoteIf.substring(0, k);
					//if (k == -1) {
					//	outld("  Not subinterface on ("+boksid+")"+boksIdName.get(boksid)+": " + remoteIf);
					//}
				}
				pm.setRemoteIf(remoteIf);
			}

			try {
				ResultSet rs = Database.query("SELECT COUNT(*) AS count FROM swp_boks WHERE boksid='"+workingOnBoksid+"' AND modul='"+mp[0]+"' AND port='"+mp[1]+"' AND boksbak!='"+boksid+"' AND boksbak IN (SELECT boksid FROM boks NATURAL JOIN type WHERE lower(descr) LIKE '%cisco%')");
				if (rs.next() && rs.getInt("count") > 0) {
					String sql = "DELETE FROM swp_boks WHERE boksid='"+workingOnBoksid+"' AND modul='"+mp[0]+"' AND port='"+mp[1]+"' AND boksbak!='"+boksid+"' AND boksbak IN (SELECT boksid FROM boks NATURAL JOIN type WHERE lower(descr) LIKE '%cisco%')";
					outl("MUST DELETE("+rs.getInt("count")+"): " + sql);
					if (DB_UPDATE) Database.update(sql);
					if (DB_COMMIT) Database.commit();
				}
			} catch (SQLException e) {
				outl("SQLException in processCDPNorm: " + e.getMessage());
				e.printStackTrace();
			}


			/*
			String mac = decimalToHexMac(macs[0]);
			String port = macs[1];
			if (!port.equals("0") && macBoksId.containsKey(mac)) {
				PortBoks pm = new PortBoks("1", port, (String)macBoksId.get(mac));
				l.add(pm);
			}
			*/
		}

		return l;
	}

	private String extractBoksid(String s)
	{
		// Vi skal prøve å finne en boksid ut fra strengen, som kan f.eks se slik ut:

		// 069003402(hb-sw)
		// tekno-sw200C01D80CEA4
		// ntnu-gw2.ntnu.no

		// Først prøver vi bare strengen
		if (sysnameMap.containsKey(s)) {
			return (String)sysnameMap.get(s);
		}

		// Så sjekker vi etter paranteser
		int i;
		if ( (i=s.indexOf("(")) != -1) {
			int end = s.indexOf(")");
			if (end != -1) {
				String n = s.substring(i+1, end);
				if (sysnameMap.containsKey(n)) {
					return (String)sysnameMap.get(n);
				}
				s = n;
			}
		}

		// Brute-force, legg til ett og ett tegn fra starten og sjekk
		String cur = null; // Hvis vi får flere matcher legger vi til det med flest tegn
		StringBuffer sb = new StringBuffer();
		for (i=0; i < s.length(); i++) {
			sb.append(s.charAt(i));
			if (sysnameMap.containsKey(sb.toString()) ) {
				cur = (String)sysnameMap.get(sb.toString() );
			}
		}
		if (cur != null) return cur;

		// Så tar vi strengen motsatt vei, bare for sikkerhets skyld
		sb = new StringBuffer();
		for (i=s.length()-1; i >= 0; i--) {
			sb.insert(0, s.charAt(i));
			if (sysnameMap.containsKey(sb.toString() )) {
				cur = (String)sysnameMap.get(sb.toString() );
			}
		}
		if (cur != null) return cur;

		/*
		// Så sjekker vi etter en stor blokk på slutten
		if (s.length() > 13) {
			String n = s.substring(s.length()-13, s.length());
			if (n.equals(s.toUpperCase())) {
				n = s.substring(0, s.length()-13);
				if (sysnameMap.containsKey(n)) {
					return (String)sysnameMap.get(n);
				}
			}
		}

		// Så prøver vi å strippe unna et og et punktum
		while ( (i=s.lastIndexOf(".")) != -1) {
			s = s.substring(0, i);
			if (sysnameMap.containsKey(s)) {
				return (String)sysnameMap.get(s);
			}
		}
		*/

		return null;
	}

	/*
	 * Cisco MAC
	 *
	 */
	private ArrayList processCisco1900(String boksid, String ip, String cs_ro, String boksType, HashMap ifindexMp) throws TimeoutException
	{
		ArrayList l = new ArrayList();

		String baseOid = ".1.3.6.1.2.1.17.4.3.1.2";

		// Get the list of macs
		// Vi får ut alle MAC-adressene tre ganger, under <baseOid>.1, .2 og .3. Den første kobler desimal-mac til hex-mac
		// Den andre kobler desimal-mac til port, og det er denne som brukes her. Desimal-mac'en blir konvertert til hex
		// istedenfor å hente ut i hex-format fra enheten. Den tredje angir status, dette benyttes ikke her.
		//ArrayList macList = getOIDs(ip, cs_ro, baseOid);
		sSnmp.setParams(ip, cs_ro, baseOid);
		ArrayList macList = sSnmp.getAll();


		for (int i=0; i<macList.size(); i++) {
			String[] macs = (String[])macList.get(i);

			String mac = decimalToHexMac(macs[0]);
			String ifind = macs[1];
			if (!ifind.equals("0") && macBoksId.containsKey(mac)) {
				String[] mp = (String[])ifindexMp.get(ifind);
				PortBoks pm = new PortBoks(mp[0], mp[1], (String)macBoksId.get(mac), "MAC");
				l.add(pm);
			}
		}

		return l;
	}

	private ArrayList processCisco1Q(String boksid, String ip, String cs_ro, String boksType) throws TimeoutException
	{
		ArrayList l = new ArrayList();

		//String baseOid = ".1.3.6.1.4.1.9.5.14.4.3.1.3.1";
		String baseOid = "1.3.6.1.4.1.9.5.14.4.3.1.4.1";

		// Get the list of macs
		//ArrayList macList = getOIDs(ip, cs_ro, baseOid);
		sSnmp.setParams(ip, cs_ro, baseOid);
		ArrayList macList = sSnmp.getAll();


		for (int i=0; i<macList.size(); i++) {
			String[] s = (String[])macList.get(i);

			// Kun enheter av type 1 er lokal (type 2 = remote)
			if (Integer.parseInt(s[1]) != 1) continue;

			String port = s[0].substring(0, s[0].indexOf("."));
			String deciMac = s[0].substring(s[0].indexOf(".")+1, s[0].length());

			String mac = decimalToHexMac(deciMac);
			if (macBoksId.containsKey(mac)) {

				PortBoks pm = new PortBoks("1", port, (String)macBoksId.get(mac), "MAC");
				l.add(pm);
			}
		}

		return l;
	}

	private ArrayList processCisco2Q(String boksid, String ip, String cs_ro, String typegruppe, String boksType, HashMap ifindexMp) throws TimeoutException
	{
		ArrayList l = new ArrayList();
		String ciscoIndexMapBaseOid = ".1.3.6.1.2.1.17.1.4.1.2";
		String ciscoMacBaseOid = ".1.3.6.1.2.1.17.4.3.1.2";
		String spanningTreeOid = ".1.3.6.1.2.1.17.2.15.1.3";

		// HashSet for å sjekke for duplikater
		HashSet dupCheck = new HashSet();

		// Hent macadresser for hvert vlan og knytt disse til riktig mp (port)
		int activeVlanCnt=0;
		int unitVlanCnt=0;
		for (int i=0; i < vlanList.length; i++) {
			String vlan = vlanList[i];

			// Hent porter som er i blocking (spanning-tree) mode
			//ArrayList spanningTree = getOIDs(ip, cs_ro+"@"+vlan, spanningTreeOid);
			sSnmp.setParams(ip, cs_ro+"@"+vlan, spanningTreeOid);
			ArrayList spanningTree = sSnmp.getAll();

			ArrayList mpBlocked = new ArrayList();
			for (int j=0; j < spanningTree.size(); j++) {
				String[] s = (String[])spanningTree.get(j);
				if (s[1].equals("2")) mpBlocked.add(s[0]);
			}

			// Hent macadresser på dette vlan
			//ArrayList macVlan = getOIDs(ip, cs_ro+"@"+vlan, ciscoMacBaseOid);
			sSnmp.setParams(ip, cs_ro+"@"+vlan, ciscoMacBaseOid);
			ArrayList macVlan = sSnmp.getAll();

			if (mpBlocked.size() == 0) {
				// Nå vet vi at ingen porter er blokkert på denne enheten på dette vlan
				// Vi sletter derfor fra databasen for å være sikker

				if (macVlan.size() == 0) continue;
			}

			// Lag mapping mellom ifIndex og cisco intern portindex
			//ArrayList indexList = getOIDs(ip, cs_ro+"@"+vlan, ciscoIndexMapBaseOid);
			sSnmp.setParams(ip, cs_ro+"@"+vlan, ciscoIndexMapBaseOid);
			ArrayList indexList = sSnmp.getAll();

			HashMap hIndexMap = new HashMap();
			for (int j=0; j < indexList.size(); j++) {
				String[] s = (String[])indexList.get(j);
				hIndexMap.put(s[0], s[1]);
			}

			int blockedCnt=0;
			if (mpBlocked.size() > 0) {
				HashMap blockedIfind = (HashMap)spanTreeBlocked.get(boksid+":"+vlan);
				if (blockedIfind == null) blockedIfind = new HashMap(); // Ingen porter er blokkert på dette vlan

				for (int j=0; j < mpBlocked.size(); j++) {
					String s = (String)mpBlocked.get(j);
					String ifind = (String)hIndexMap.get(s);
					if (ifind == null) continue;

					// OK, nå kan vi sjekke om denne eksisterer fra før
					String swportid = (String)blockedIfind.remove(ifind);
					if (swportid == null) {
						// Eksisterer ikke fra før, må settes inn, hvis den eksisterer i swport
						swportid = (String)swportIfindex.get(boksid+":"+ifind);
						if (swportid != null) {
							outl("    Ifindex: " + ifind + " on VLAN: " + vlan + " is now in blocking mode.");
							//String query = "INSERT INTO swportblocked (swportid,vlan) VALUES ((SELECT swportid FROM swport WHERE boksid='"+boksid+"' AND ifindex='"+ifind+"'),'"+vlan+"')";
							String query = "INSERT INTO swportblocked (swportid,vlan) VALUES ('"+swportid+"','"+vlan+"')";
							if (DB_UPDATE) {
								try {
									Database.update(query);
									if (DB_COMMIT) Database.commit();
									blockedCnt++;
								} catch (SQLException e) {
									outld("*ERROR* SQLException: " + e.getMessage());
								}
							}
						}
					} else {
						blockedCnt++;
					}
				}
				// Nå har vi tatt bort alle porter som fortsatt er blokkert, og resten er da ikke blokkert, så det må slettes
				Iterator iter = blockedIfind.values().iterator();
				while (iter.hasNext()) {
					String swportid = (String)iter.next();
					outl("    swportid: " + swportid + " on VLAN: " + vlan + " is no longer in blocking mode.");
					String query = "DELETE FROM swportblocked WHERE swportid='"+swportid+"' AND vlan='"+vlan+"'";
					if (DB_UPDATE) {
						try {
							Database.update(query);
							if (DB_COMMIT) Database.commit();
						} catch (SQLException e) {
							outld("*ERROR* SQLException: " + e.getMessage());
						}
					}
				}
			}
			if (macVlan.size() == 0) continue;
			outl("  Querying vlan: " + vlan + ", MACs: " + macVlan.size() + " Mappings: " + indexList.size() + " Blocked: " + blockedCnt + " / " + mpBlocked.size() );

			activeVlanCnt++;
			boolean b = false;
			for (int j=0; j < macVlan.size(); j++) {
				String[] s = (String[])macVlan.get(j);

				// Sjekk om vi skal ta med denne mac
				String mac = decimalToHexMac(s[0]);
				if (!macBoksId.containsKey(mac)) continue;

				// Sjekk om MAC adressen vi har funnet er dem samme som den for enheten vi spør
				// Dette skjer på C35* enhetene.
				if (boksid.equals(macBoksId.get(mac))) continue;

				// Finn ifIndex
				String ifInd = (String)hIndexMap.get(s[1]);
				if (ifInd == null) {
					outl("  WARNING! MAC: " + mac + " ("+ boksIdName.get(macBoksId.get(mac)) +") found at index: " + s[1] + ", but no ifIndex mapping exists.");
					continue;
				}

				// Finn mp
				String[] mp = (String[])ifindexMp.get(ifInd);
				if (mp == null) {
					outl("  WARNING! MAC: " + mac + " ("+ boksIdName.get(macBoksId.get(mac)) +") found at index: " + s[1] + ", ifIndex: " + ifInd + ", but no mp mapping exists.");
					continue;
				}

				//outl("  Unit: " + unit + " Port: " + port + " Mac: " + mac);
				// Legg til i listen over macer
				PortBoks pm = new PortBoks(mp[0], mp[1], (String)macBoksId.get(mac), "MAC");
				if (dupCheck.contains(boksid+":"+pm)) continue;

				dupCheck.add(boksid+":"+pm);
				l.add(pm);

				if (!b) { unitVlanCnt++; b=true; }
			}
		}
		outl("  MACs found on " + activeVlanCnt + " / " + vlanList.length + " VLANs, units on " + unitVlanCnt + ".");
		return l;
	}

	private HashMap fetchIfindexMpMap(String ip, String cs_ro, String typegruppe) throws TimeoutException
	{
		//String ciscoIndexMapBaseOid = ".1.3.6.1.2.1.17.1.4.1.2";

		// Hent kobling mellom ifIndex<->mp
		HashMap ifindexH = new HashMap();
		String ifmpBaseOid = "";
		if (typegruppe.equals("cat-sw")) {
			ifmpBaseOid = ".1.3.6.1.4.1.9.5.1.4.1.1.11";

			//ArrayList ifmpList = getOIDs(ip, cs_ro, ifmpBaseOid);
			sSnmp.setParams(ip, cs_ro, ifmpBaseOid);
			ArrayList ifmpList = sSnmp.getAll(true);

			outl("  Found " + ifmpList.size() + " ifindex<->mp mappings.");
			for (int i=0; i < ifmpList.size(); i++) {
				String[] s = (String[])ifmpList.get(i);
				StringTokenizer st = new StringTokenizer(s[0], ".");
				String[] mp = { st.nextToken(), st.nextToken() };
				ifindexH.put(s[1], mp);
				//outl("Add Modul: " + mp[0] + " Port: " + mp[1] + " ifIndex: " + s[1]);
			}

		} else
		if (typegruppe.equals("ios-sw") ||
			typegruppe.equals("cgw") ||
			typegruppe.equals("cgw-nomem") ||
			typegruppe.equals("cat1900-sw") ) {

			ifmpBaseOid = ".1.3.6.1.2.1.2.2.1.2";
			//ArrayList ifmpList = getOIDs(ip, cs_ro, ifmpBaseOid);
			sSnmp.setParams(ip, cs_ro, ifmpBaseOid);
			ArrayList ifmpList = sSnmp.getAll(true);

			outl("  Found " + ifmpList.size() + " ifindex<->mp mappings.");
			for (int i=0; i < ifmpList.size(); i++) {
				String[] s = (String[])ifmpList.get(i);
				StringTokenizer st = new StringTokenizer(s[1], "/");
				String modul = st.nextToken();
				String port = (st.hasMoreTokens()) ? st.nextToken() : "";

				// Hvis modul inneholder f.eks FastEther0 skal dette forkortes til Fa0
				modul = processModulName(modul);

				if (port.length() == 0) {
					port = modul;
					modul = "1";

					try {
						Integer.parseInt(port);
					} catch (NumberFormatException e) {
						port = s[0];
					}
				}

				String[] mp = { modul, port };
				//if (mp[1].length() == 0) mp[1] = "1";

				ifindexH.put(s[0], mp);
				//outl("Add Modul: " + mp[0] + " Port: " + mp[1] + " ifIndex: " + s[0]);
			}

		} else {
			outl("  *ERROR*! Unknown typegruppe: " + typegruppe);
			//return ifindexH;
		}
		return ifindexH;
	}

	/*
	 * 3COM
	 *
	 */
	private ArrayList process3Com(String boksid, String ip, String cs_ro, String typegruppe, String boksType) throws TimeoutException
	{
		ArrayList l = new ArrayList();

		String baseOid = "";
		if (typegruppe.equals("3ss9300")) {
			baseOid = ".1.3.6.1.4.1.43.29.4.10.8.1.5.1";
		} else
		if (typegruppe.equals("3ss")) {
			baseOid = ".1.3.6.1.4.1.43.10.22.2.1.3";
		} else
		if (typegruppe.equals("3hub")) {
			baseOid = ".1.3.6.1.4.1.43.10.9.5.1.6";
		} else {
			outl("  Unsupported typegruppe: " + typegruppe + " boksType: " + boksType);
			return l;
		}

		// Get the list of macs
		sSnmp.setParams(ip, cs_ro, baseOid);
		ArrayList macList = sSnmp.getAll();

		for (int i=0; i<macList.size(); i++) {
			String[] s = (String[])macList.get(i);

			String formatMac = formatMac(s[1].toLowerCase());
			//outl("Raw MAC: " + s[1].toLowerCase() + " Found MAC: " + formatMac);
			if (macBoksId.containsKey(formatMac)) {

				StringTokenizer st = new StringTokenizer(s[0], ".");

				String modul = st.nextToken();
				String port = st.nextToken();
				if (boksType.equals("SW9300")) modul = "1";

				PortBoks pm = new PortBoks(modul, port, (String)macBoksId.get(formatMac), "MAC");
				l.add(pm);
			}
		}

		return l;
	}

	private String decimalToHexMac(String decMac) {
		StringTokenizer st = new StringTokenizer(decMac, ".");

		String hexMac = "";
		while (st.hasMoreTokens()) {
			int t = Integer.parseInt(st.nextToken());
			String s = Integer.toHexString(t);
			if (s.length() == 1) hexMac += "0";
			hexMac += s;
		}
		return hexMac;
	}

	private String formatMac(String mac)
	{
		if (mac.startsWith("0x")) mac = mac.substring("0x".length(), mac.length());

		String newMac = "";
		StringTokenizer st = new StringTokenizer(mac);
		if (st.countTokens()==1) st = new StringTokenizer(mac, ":");
		if (st.countTokens()==1) return mac;

		while (st.hasMoreTokens()) {
			String s = st.nextToken();
			if (s.length() == 1) newMac += "0";
			newMac += s;
		}
		return newMac;
	}


	private void outa(String s) { System.out.print(s); }
	private void outla(String s) { System.out.println(s); }

	private void out(String s) { if (VERBOSE_OUT) System.out.print(s); }
	private void outl(String s) { if (VERBOSE_OUT) System.out.println(s); }

	private void outd(String s) { if (DEBUG_OUT) System.out.print(s); }
	private void outld(String s) { if (DEBUG_OUT) System.out.println(s); }
}

class BoksData
{
	public String ip;
	public String cs_ro;
	public String boksId;
	public String boksTypegruppe;
	public String boksType;
	public String sysName;
	public String kat;
	public int vekt;
}

class PortBoks
{
	String modul;
	String port;
	String boksid;
	String source;

	String ifindex;

	String remoteIf;

	public PortBoks(String modul, String port, String boksid, String source)
	{
		this.modul=modul.trim();
		this.port=port.trim();
		this.boksid=boksid.trim();
		this.source=source.trim();
	}

	public String getModulS() { return ((modul.length()==1)?" ":"")+getModul(); }
	public String getPortS() { return ((port.length()==1)?" ":"")+getPort(); }

	public String getModul() { return modul; }
	public String getPort() { return port; }
	public String getBoksId() { return boksid; }

	public String getSource() { return source; }

	public void setIfindex(String s) { ifindex = s; }
	public String getIfindex() { return ifindex; }

	public void setRemoteIf(String s) { remoteIf = s; }
	public String getRemoteIf() { return remoteIf; }

	public String toString() { return modul+":"+port+":"+boksid; }
}

class BoksReport implements Comparable
{
	int usedTime;
	BoksData bd;

	public BoksReport(int usedTime, BoksData bd)
	{
		this.usedTime = usedTime;
		this.bd = bd;
	}

	public int getUsedTime() { return usedTime; }
	public BoksData getBoksData() { return bd; }

	public int compareTo(Object o)
	{
		return new Integer(((BoksReport)o).getUsedTime()).compareTo(new Integer(usedTime));
	}
}
















