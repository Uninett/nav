/*******************
*
* $Id: QueryBoks.java,v 1.7 2003/06/25 14:49:05 kristian Exp $
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


public class QueryBoks extends Thread
{
	public static boolean ERROR_OUT = true;
	public static boolean VERBOSE_OUT = false;
	public static boolean DEBUG_OUT = false;
	public static boolean DB_UPDATE = false;
	public static boolean DB_COMMIT = false;

	// Felles datastrukturer som bare skal leses fra
	public static HashMap macBoksId;
	public static HashMap boksIdName;
	public static HashMap boksidKat;
	public static HashMap boksidType;
	public static HashMap sysnameMap;

	public static HashMap spanTreeBlocked;

	public static HashSet cdpBoks;

	// Inneholder alle boksid'er som er av kat=GW
	public static HashSet boksGwSet;

	// Mapping fra boksid, port og modul til swportid i swport
	public static HashMap swportSwportidMap;

	// Denne inneholder alle "boksid:ifindex" fra swport som er trunk-porter
	//public static HashSet boksIfindexTrunkSet;

	// Mengde av vlan som må sjekkes på Cisco-boksene
	public static Map vlanBoksid;

	// Hvilke porter det står en GW|SW|KANT bak, som gitt i swp_boks-tabellen
	static HashSet foundBoksBakSwp;
	public static void setFoundBoksBakSwp(HashSet hs) { foundBoksBakSwp = hs; }

	// For CAM-loggeren
	public static HashMap unclosedCam;
	public static HashSet safeCloseBoksid;
	public static HashSet watchMacs;
	// Per-tråd variabler for CAM
	private List camInsertQueue = new ArrayList();
	private List camResetQueue = new ArrayList();
	private Set dupeMacSet = new HashSet(); // For å unngå at duplikate rapporteringer gir duplikater i tabellen

	private int camNewCnt;

	// Hvor mange records i swp_boks som er resatt
	private static int swpResetMisscnt = 0;
	synchronized private static void swpIncResetMisscnt() {
		swpResetMisscnt++;
	}
	public static int getSwpResetMisscnt() { return swpResetMisscnt; }

	// Hvor mange records i cam som er resatt
	private static int camResetMisscnt = 0;
	synchronized private static void camIncResetMisscnt() {
		camResetMisscnt++;
	}
	public static int getCamResetMisscnt() { return camResetMisscnt; }

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

	SimpleSnmp sSnmp = SimpleSnmp.simpleSnmpFactory();

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
		"GigabitEthernet", "Gi",
		"Ethernet", "Eth"
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
		long beginTime = System.currentTimeMillis();

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
			long boksBeginTime = System.currentTimeMillis();

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
					boksTypegruppe.equals("cgsw") ||
					boksTypegruppe.equals("ios-sw") ||
					boksTypegruppe.equals("cat-sw") ||
					boksTypegruppe.equals("cL3-sw") ||
					boksTypegruppe.equals("cat1900-sw") ||
					boksTypegruppe.equals("catmeny-sw") ) {

					outld("Fetching Ifindex <-> mp mapping");
					ifindexMp = fetchIfindexMpMap(ip, cs_ro, boksTypegruppe);

					/*
					if (boksTypegruppe.equals("cat1900-sw") ||
						boksTypegruppe.equals("catmeny-sw") ) {
						decodeHex = true;
					}
					*/

					outld("Starting CDP processing for Cisco");
					ArrayList l = processCDPCisco(boksId, ip, cs_ro, ifindexMp);
					outld("Done processing CDP for Cisco");
					boksListe.addAll(l);

				}

				// HP støtter også CDP
				if (boksTypegruppe.equals("hpsw")) {
					ArrayList l = processCDPHP(boksId, ip, cs_ro, ifindexMp);
					outld("Done processing CDP for HP");
					boksListe.addAll(l);
				}

				if (kat.equalsIgnoreCase("GW")) {
					// GW'er behandles annerledes, vi skal oppdatere boksbak og evt. swportbak i gwport

					for (int i=0; i < boksListe.size(); i++) {

						PortBoks pm = (PortBoks)boksListe.get(i);
						String key = boksId+":"+pm;
						String remoteIf = pm.getRemoteIf();
						if (remoteIf == null) {
							outla("  Error, remoteIf is null for gw("+boksId+") " + sysName + ", boksbak: " + pm.getBoksId());
							continue;
						}

						String remoteSwportid;
						if (boksGwSet.contains(pm.getBoksId())) {
							// Link til gw, vi har da ingen swportid
							remoteSwportid = "null";
						} else {
							// Link til ikke-gw, da skal vi finne swportid
							// Hent ut modul / port
							/*
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
							*/
							String[] mp = stringToMp("", remoteIf);

							String remoteKey = pm.getBoksId()+":"+mp[0]+":"+mp[1];
							remoteSwportid = (String)swportSwportidMap.get(remoteKey);
							if (remoteSwportid == null) {
								outla("  Error, could not find swportid for ("+pm.getBoksId()+") "+boksIdName.get(pm.getBoksId())+" Modul: " + mp[0] + " Port: " + mp[1]);
								continue;
							}
						}

						// OK, da er vi klar, oppdater gwport!
						if (boksType.equals("MSFC") ||
							boksType.equals("MSFC1") ||
							boksType.equals("RSM") ) {

							if (DB_UPDATE) Database.update("UPDATE gwport SET to_netboxid = '"+pm.getBoksId()+"', to_swportid = "+remoteSwportid+" WHERE moduleid IN (SELECT moduleid FROM module WHERE netboxid = '"+boksId+"') AND prefixid IS NOT NULL");
							if (DB_COMMIT) Database.commit(); else Database.rollback();
							outl("    ["+boksType+"] Ifindex: " + pm.getIfindex() + " Interface: " + pm.getModulS() + ", " + boksIdName.get(pm.getBoksId()) );
							continue;
						}

						/* Can ikke brukes mer da vi trenger data fra module
						String[] updateFields = {
							"to_netboxid", pm.getBoksId(),
							"to_swportid", remoteSwportid
						};
						String[] condFields = {
							"netboxid", boksId,
							"ifindex", pm.getIfindex()
						};
						if (DB_UPDATE) Database.update("gwport", updateFields, condFields);						
						*/

						if (DB_UPDATE) Database.update("UPDATE gwport SET to_netboxid = '"+pm.getBoksId()+"', to_swportid = "+remoteSwportid+" WHERE moduleid IN (SELECT moduleid FROM module WHERE netboxid = '"+boksId+"') AND ifindex='"+pm.getIfindex());

						if (DB_COMMIT) Database.commit(); else Database.rollback();
						outl("    [GW] Ifindex: " + pm.getIfindex() + " Interface: " + pm.getModulS() + ", " + boksIdName.get(pm.getBoksId()) );
					}

					long boksUsedTime = System.currentTimeMillis() - boksBeginTime;
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
				} else
				if (boksTypegruppe.equals("hpsw")) {
					// Alt HP utstyr
					macListe = processHP(boksId, ip, cs_ro, boksTypegruppe, boksType);
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
							if (cdpBoks.contains(pm.getBoksId())) {
								outld("T"+id+":  [CDP-DEL] Modul: " + pm.getModulS() + " Port: " + pm.getPortS() + ", " + boksIdName.get(pm.getBoksId()) );
								continue;
							}
						}
						boksListe.add(pm);
					}
				}
			} catch (SQLException se) {
				outle("T"+id+":  QueryBoks.run(): SQLException: " + se.getMessage());
				outla("T"+id+":  QueryBoks.run(): SQLException: " + se.getMessage());
				if (se.getMessage() != null && se.getMessage().indexOf("Exception: java.net.SocketException") != -1) {
					// Mistet kontakten med serveren, abort
					outla("T"+id+":  QueryBoks.run(): Lost contact with backend, fatal error!");
					outla("T"+id+":  QueryBoks.run(): Exiting...");
					System.exit(2);
				}
				se.printStackTrace(System.err);
			} catch (TimeoutException te) {
				outl("T"+id+":   *ERROR*, TimeoutException: " + te.getMessage());
				outla("T"+id+":   *** GIVING UP ON: " + sysName + ", typename: " + boksType + " ***");
				continue;
			} catch (Exception exp) {
				outle("T"+id+":  QueryBoks.run(): Fatal error, aborting. Exception: " + exp.getMessage());
				outla("T"+id+":  QueryBoks.run(): Fatal error, aborting. Exception: " + exp.getMessage());
				exp.printStackTrace(System.err);
				outla("T"+id+":  QueryBoks.run(): Exiting...");
				System.exit(1);
			}

			Collections.sort(boksListe);
			int newCnt=0,dupCnt=0;
			List printList = new ArrayList();
			for (int i=0; i < boksListe.size(); i++) {

				PortBoks pm = (PortBoks)boksListe.get(i);
				String key = boksId+":"+pm;

				// En enhet kan ikke ha link til seg selv
				if (boksId.equals(pm.getBoksId())) continue;

				// Sjekk om dette er en duplikat
				if (swp.contains(key)) {
					String swp_boksid = null, modulbak = null, portbak = null;
					int misscnt=0;
					synchronized (swp_d) {
						if (swp_d.containsKey(key)) {
							HashMap hm = (HashMap)swp_d.remove(key);
							swp_boksid = (String)hm.get("swp_netboxid");
							misscnt = Integer.parseInt((String)hm.get("misscnt"));
							modulbak = (String)hm.get("to_module");
							if (modulbak == null && hm.containsKey("to_module")) modulbak = "";
							portbak = (String)hm.get("to_port");
							if (portbak == null && hm.containsKey("to_port")) portbak = "";
						}
					}
					if (swp_boksid != null && misscnt > 0) {
						// Nå må vi også resette misscnt i recorden i swp_boks
						if (DB_UPDATE) {
							try {
								String[] updateFields = {
									"misscnt", "0"
								};
								String[] condFields = {
									"swp_netboxid", swp_boksid
								};
								Database.update("swp_netbox", updateFields, condFields);
								if (DB_COMMIT) Database.commit(); else Database.rollback();
							} catch (SQLException e) {
								outle("  QueryBoks.run(): Reseting swp_netboxid: " + swp_boksid + " in swp_netbox, SQLException: " + e.getMessage() );
							}
						}
						swpIncResetMisscnt();
					}

					if (modulbak != null && portbak != null) {
						// Nå må vi sjekke om modulbak og/eller portbak feltene har endret seg
						//errl("Link to: " + getBoksMacs.boksIdName.get(pm.getBoksId()) + " remoteModul: " + pm.getRemoteModul() + " modulbak: " + modulbak);
						if (!pm.getRemoteModul().equals(modulbak) || !pm.getRemotePort().equals(portbak)) {
							if (DB_UPDATE) {
								try {
									String[] updateFields = {
										"to_module", pm.getRemoteModul().length()==0 ? "null" : pm.getRemoteModul(),
										"to_port", pm.getRemotePort().length()==0 ? "null" : pm.getRemotePort()
									};
									String[] condFields = {
										"swp_netboxid", swp_boksid
									};
									Database.update("swp_netbox", updateFields, condFields);
									if (DB_COMMIT) Database.commit(); else Database.rollback();
								} catch (SQLException e) {
									outle("  QueryBoks.run(): Update modulbak/portbak in swp_boks, swp_boksid: " + swp_boksid + ", modulbak: " + pm.getRemoteModul() + ", portbak: " + pm.getRemotePort() + "\n  SQLException: " + e.getMessage() );
								}
							}
						}
					}

					//outl("T"+id+":    [DUP] Modul: " + pm.getModulS() + " Port: " + pm.getPortS() + ", " + getBoksMacs.boksIdName.get(pm.getBoksId()) );
					String s = "T"+id+":    [DUP] Modul: " + pm.getModulS() + " Port: " + pm.getPortS() + ", " + getBoksMacs.boksIdName.get(pm.getBoksId());
					printList.add(s);
					dupCnt++;
					continue;
				}

				// Legg til i listen så vi ikke får duplikater
				synchronized (swp) {
					swp.add(key);
				}
				outl("T"+id+":    ["+pm.getSource()+"] Modul: " + pm.getModulS() + " Port: " + pm.getPortS() + ", " + getBoksMacs.boksIdName.get(pm.getBoksId()) );

				String[] insertData;
				String rModul = pm.getRemoteModul();
				String rPort = pm.getRemotePort();
				if (rModul != null && rModul.length() > 0 && rPort != null && rPort.length() > 0) {
					String[] s = {
						"netboxid", boksId,
						"module", pm.getModul(),
						"port", pm.getPort(),
						"to_netboxid", pm.getBoksId(),
						"to_module", rModul,
						"to_port", rPort
					};
					insertData = s;
				} else {
					String[] s = {
						"netboxid", boksId,
						"module", pm.getModul(),
						"port", pm.getPort(),
						"to_netboxid", pm.getBoksId()
					};
					insertData = s;
				}
				if (DB_UPDATE) {
					try {
						Database.insert("swp_netbox", insertData);
						if (DB_COMMIT) Database.commit(); else Database.rollback();
						newCnt++;
					} catch (SQLException e) {
						errl("ERROR, Insert into swp_netbox ("+key+"), SQLException: " + e.getMessage() );
					}
				} else {
					newCnt++;
				}
			}

			Collections.sort(printList);
			for (Iterator j=printList.iterator(); j.hasNext();) {
				outl(String.valueOf(j.next()));
			}

			if (newCnt > 0 || dupCnt > 0) {
				outl("T"+id+": Fount a total of " + newCnt + " new units, " + dupCnt + " duplicate units.");
			}

			long boksUsedTime = System.currentTimeMillis() - boksBeginTime;
			synchronized (boksReport) {
				boksReport.add(new BoksReport((int)boksUsedTime, bd));
			}
		}
		long usedTime = System.currentTimeMillis() - beginTime;
		threadDone[num] = true;
		outla("T"+id+": ** Thread done, time used: " + getBoksMacs.formatTime(usedTime) + ", waiting for " + getThreadsNotDone() + " **");

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
	 * Cisco CDP specific processing
	 *
	 */
	private ArrayList processCDPCisco(String workingOnBoksid, String ip, String cs_ro, HashMap ifindexMp) throws SQLException, TimeoutException
	{
		ArrayList l = new ArrayList();

		String cdpOid = ".1.3.6.1.4.1.9.9.23.1.2.1.1.6";
		sSnmp.setParams(ip, cs_ro, cdpOid);
		ArrayList cdpList = sSnmp.getAll(true);
		if (cdpList.size() == 0) return l;

		// Vi har fått noe via CDP, da kan vi trygt lukke CAM records
		safeCloseBoksidAdd(workingOnBoksid);

		String remoteIfOid = ".1.3.6.1.4.1.9.9.23.1.2.1.1.7";
		sSnmp.setParams(ip, cs_ro, remoteIfOid);
		ArrayList cdpRMpList = sSnmp.getAll(true);

		outld("In processCDPCisco(), cdpList.size: " + cdpList.size());
		if (cdpList.size() != cdpRMpList.size()) outla("  *WARNING*: cdpList != cdpRMpList ("+cdpList.size()+" != "+cdpRMpList.size()+").");

		for (int i=0; i<cdpList.size(); i++) {
			String[] cdps = (String[])cdpList.get(i);

			String ifind = cdps[0].substring(0, cdps[0].indexOf("."));
			String[] mp = (String[])ifindexMp.get(ifind);

			if (mp == null) {
				String[] s = {
					"1",
					ifind
				};
				mp = s;
				outla("  *WARNING*: ifindex mapping not found, using Modul: " + mp[0] + " Port: " + mp[1] + " String: " + cdps[1]);
			}

			// Hent ut mp på andre siden
			if (cdpRMpList.size() <= i) continue;
			String[] remoteIf = (String[])cdpRMpList.get(i);

			// c1900 har port 25 og 26 som A og B
			remoteIf[1] = remoteIf[1].trim();
			if (remoteIf[1].equals("A") || remoteIf[1].equals("B")) {
				remoteIf[1] = ""+ (26 + remoteIf[1].charAt(0) - 'A');
			}

			// Opprett record for boksen bak porten
			PortBoks pm = processCDP(workingOnBoksid, cdps[1], ifind, mp[0], mp[1], remoteIf[1].trim() );
			if (pm == null) continue;
			pm.setIfindex(ifind);
			l.add(pm);

			outld("processCDPCisco:  Modul: " + pm.getModulS() + " Port: " + pm.getPortS() + "  CDP: " + boksIdName.get(pm.getBoksId()));
		}

		return l;
	}

	/*
	 * HP CDP specific processing
	 *
	 */
	private ArrayList processCDPHP(String workingOnBoksid, String ip, String cs_ro, HashMap ifindexMp) throws SQLException, TimeoutException
	{
		ArrayList l = new ArrayList();

		/*
		 * Først henter vi ut antall i stack'en med MIB:
		 *
		 * .1.3.6.1.4.1.11.2.14.11.5.1.10.4.1.1
		 *
		 * Denne gir ut et tall for hvert member, 0 er commanderen
		 *
		 */
		String stackOid = "1.3.6.1.4.1.11.2.14.11.5.1.10.4.1.1";
		String cdpOid = ".1.3.6.1.4.1.9.9.23.1.2.1.1.6";
		String remoteIfOid = ".1.3.6.1.4.1.9.9.23.1.2.1.1.7";
		ArrayList stackList;

		// Henter først antallet i stack'en:
		sSnmp.setParams(ip, cs_ro, stackOid);
		stackList = sSnmp.getAll();

		if (stackList.isEmpty()) stackList.add(new String[] { "", "0" });
		outld("processCDPHP: stackList.size: " + stackList.size() );

		for (int i=stackList.size()-1; i >= 0; i--) {
			String[] stack = (String[])stackList.get(i);

			String modul = stack[1];
			//String modul = String.valueOf(i+1);
			outld("processCDPHP:   modul: " + modul);

			// Get the list of macs
			sSnmp.setParams(ip, cs_ro+(!stack[1].equals("0")?"@sw"+stack[1]:""), cdpOid);
			ArrayList cdpList = sSnmp.getAll(true);
			if (cdpList.size() == 0) continue;

			// Vi har fått noe via CDP, da kan vi trygt lukke CAM records
			safeCloseBoksidAdd(workingOnBoksid);

			sSnmp.setParams(ip, cs_ro+(!stack[1].equals("0")?"@sw"+stack[1]:""), remoteIfOid);
			ArrayList cdpRMpList = sSnmp.getAll(true);

			outld("In processCDPCDP(), cdpList.size: " + cdpList.size());
			if (cdpList.size() != cdpRMpList.size()) outla("  *WARNING*: cdpList != cdpRMpList ("+cdpList.size()+" != "+cdpRMpList.size()+").");

			for (int j=0; j<cdpList.size(); j++) {
				String[] cdps = (String[])cdpList.get(j);

				String port = cdps[0].substring(0, cdps[0].indexOf("."));

				// Hent ut mp på andre siden
				if (cdpRMpList.size() <= j) continue;
				String[] remoteIf = (String[])cdpRMpList.get(j);

				// Opprett record for boksen bak porten
				PortBoks pm = processCDP(workingOnBoksid, cdps[1], port, modul, port, remoteIf[1].trim() );
				if (pm == null) continue;
				pm.setIfindex(port);
				l.add(pm);

				outld("processCDPHP:  Modul: " + pm.getModulS() + " Port: " + pm.getPortS() + "  CDP: " + boksIdName.get(pm.getBoksId()));
			}
		}

		return l;
	}

	/*
	 * Shared CDP processing
	 *
	 */
	private PortBoks processCDP(String workingOnBoksid, String cdpString, String ifindex, String modul, String port, String remoteIf) throws SQLException
	{
		String boksid = extractBoksid(cdpString);
		String hpModul = null;
		if (boksid != null) {
			String sysname = (String)boksIdName.get(boksid);
		} else {
			// Her kan det være en HP bak, og da har vi en rask hack for NTNU-nettverket der -<tall> byttes til -h
			boolean b = true;

			// Stripp alt innenfor ( )
			int k=0;
			if ( (k=cdpString.indexOf("(")) != -1) {
				int end = cdpString.indexOf(")");
				if (end != -1) {
					String s = cdpString.substring(0, k)+cdpString.substring(end+1, cdpString.length());

					// Sjekk etter -<tall>
					if ( (k=s.lastIndexOf("-")) != -1) {
						if (s.length() > k && isDigit(s.charAt(k+1))) {
							hpModul = String.valueOf(s.charAt(k+1));

							s = s.substring(0, k+1)+"h"+s.substring(k+2, s.length());
							boksid = extractBoksid(s);
							if (boksid == null) {
								if (!hpModul.equals("0")) {
									errl("  *NTNU* At " + boksIdName.get(workingOnBoksid)+" Modul: " + modul + " Port: " + port+ ", Possible HP member("+cdpString+"), but commander("+s+") not found");
								}
								return null;
							}
							b = false;
							//errl("Modul: " + modul + " Port: " + port + ", found commander " + s + " for member("+hpModul+") " + cdpString);
						}
					}
				}
			}



			if (b) {
				outla("  *WARNING*: Not found, ("+workingOnBoksid+") "+boksIdName.get(workingOnBoksid)+", Modul: " + modul + " Port: " + port + " String: " + cdpString);
				return null;
			}
		}

		// Opprett record for boksen bak porten
		PortBoks pm = new PortBoks(modul, port, boksid, "CDP");
		//pm.setIfindex(ifind);
		//l.add(pm);

		String key = pm.getModul()+":"+pm.getPort();
		foundCDPMp.add(key);

		// Nå vet vi at vi har funnet en boks via CDP bak denne porten, og da kan det ikke være andre Cisco eller HP-enheter bak her
		try {
			//ResultSet rs = Database.query("SELECT COUNT(*) AS count FROM swp_boks WHERE boksid='"+workingOnBoksid+"' AND modul='"+modul+"' AND port='"+port+"' AND boksbak!='"+boksid+"' AND boksbak IN (SELECT boksid FROM boks NATURAL JOIN type WHERE (lower(descr) LIKE '%cisco%' OR typegruppe='hpsw'))");
			ResultSet rs = Database.query("SELECT COUNT(*) AS count FROM swp_netbox WHERE netboxid='"+workingOnBoksid+"' AND module='"+modul+"' AND port='"+port+"' AND to_netboxid!='"+boksid+"' AND to_netboxid IN (SELECT netboxid FROM netbox JOIN type USING(typeid) WHERE cdp='t')");
			if (rs.next() && rs.getInt("count") > 0) {
				//String sql = "DELETE FROM swp_boks WHERE boksid='"+workingOnBoksid+"' AND modul='"+modul+"' AND port='"+port+"' AND boksbak!='"+boksid+"' AND boksbak IN (SELECT boksid FROM boks NATURAL JOIN type WHERE (lower(descr) LIKE '%cisco%' OR typegruppe='hpsw'))";
				String sql = "DELETE FROM swp_netbox WHERE netboxid='"+workingOnBoksid+"' AND module='"+modul+"' AND port='"+port+"' AND to_netboxid!='"+boksid+"' AND to_netboxid IN (SELECT netboxid FROM netbox JOIN type USING(typeid) WHERE cdp='t')";
				outl("MUST DELETE("+rs.getInt("count")+"): " + sql);
				if (DB_UPDATE) Database.update(sql);
				if (DB_COMMIT) Database.commit(); else Database.rollback();
			}
		} catch (SQLException e) {
			outle("SQLException in processCDPNorm: " + e.getMessage());
			e.printStackTrace(System.err);
		}

		/*
		// Hent ut mp på andre siden
		if (cdpRMpList.size() <= i) continue;
		String[] remoteIf = (String[])cdpRMpList.get(i);
		*/
		String rIf = remoteIf;
		{
			int k;
			if ( (k=rIf.lastIndexOf('.')) != -1) rIf = rIf.substring(0, k);
		}


		// Dersom denne porten går fra ikke-gw (sw,kant) til gw må vi slå remote interface opp i gwport
		// slik at vi kan sette boksbak og swportbak.
		if (!boksGwSet.contains(workingOnBoksid) && boksGwSet.contains(boksid)) {
			// OK, ikke-gw -> gw
			String swportid = (String)swportSwportidMap.get(workingOnBoksid+":"+modul+":"+port);
			if (swportid != null) {
				// Setter boksbak og swportbak for alle matchende interfacer
				outl("  Updating boksbak("+workingOnBoksid+"), swportbak("+swportid+") for gw: " + boksIdName.get(boksid)+", rIf: " + rIf);
				//if (DB_UPDATE) Database.update("UPDATE gwport SET boksbak = '"+workingOnBoksid+"', swportbak = '"+swportid+"' WHERE gwportid IN (SELECT gwportid FROM gwport JOIN prefiks USING(prefiksid) WHERE vlan IS NOT NULL AND boksid='"+boksid+"' AND interf like '"+rIf+"%')");
				if (DB_UPDATE) Database.update("UPDATE gwport SET to_netboxid = '"+workingOnBoksid+"', to_swportid = '"+swportid+"' WHERE  moduleid IN (SELECT moduleid FROM module WHERE netboxid='"+boksid+"') AND interface = '"+rIf+"'");
				if (DB_COMMIT) Database.commit(); else Database.rollback();
			}
		} else if (boksGwSet.contains(workingOnBoksid)) {
			pm.setRemoteIf(rIf);
		} else {
			// Nå har vi ikke-gw -> ikke-gw, da setter vi remoteMp
			String[] remoteMp;

			// Er det en HP i andre enden, + at remoteIf ikke inneholder modul?
			String s = (String)boksidType.get(boksid);
			if (remoteIf.indexOf("/") == -1 && s != null && s.equals("2524")) {
				// Default-modul skal nå settes
				if (hpModul == null) hpModul = "0";
				remoteMp = stringToMp(ifindex, remoteIf, hpModul);
				//errl("  Link til hp, hpModul: " + hpModul + " Remote Modul: " + remoteMp[0] + " Port: " + remoteMp[1]);
			} else {
				remoteMp = stringToMp(ifindex, remoteIf);

				/*
				if (((String)boksidKat.get(boksid)).equals("GSW")) {
					// Modul skal nå være et tall, strip Gi
					if (remoteMp[0].startsWith("Gi")) remoteMp[0] = remoteMp[0].substring(2, remoteMp[0].length());
					else if (remoteMp[0].startsWith("Fa")) remoteMp[0] = remoteMp[0].substring(2, remoteMp[0].length());
				}
				*/

			}
			pm.setRemoteMp(remoteMp);
		}

		return pm;
	}


	private String extractBoksid(String s)
	{
		// Vi skal prøve å finne en boksid ut fra CDP strengen, som kan f.eks se slik ut:

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
				if ( (n=extractBoksid(n)) != null) return n;
				s = s.substring(0, i);
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

		HashSet foundBoksBak = new HashSet();

		for (int i=0; i<macList.size(); i++) {
			String[] macs = (String[])macList.get(i);

			String mac = decimalToHexMac(macs[0]);
			String ifind = macs[1];
			if (!ifind.equals("0")) {
				String[] mp = (String[])ifindexMp.get(ifind);
				if (mp == null) {
					outla("processCisco1900: Error, " + boksIdName.get(boksid) + "("+boksid+"), could not find mp for ifindex: " + ifind);
					continue;
				}
				String modul = mp[0];
				String port = mp[1];

				// Nå har vi funnet minst en MAC fra denne enheten, og da sier vi at den er oppe og aktiv,
				safeCloseBoksidAdd(boksid);

				// Prosesser Mac-adressen (CAM)
				processMac(boksid, modul, port, mac);

				if (macBoksId.containsKey(mac)) {
					String boksidBak = (String)macBoksId.get(mac);
					String boksBakKat = (String)boksidKat.get(boksidBak);
					if (boksBakKat == null || isNetel(boksBakKat)) {
						foundBoksBak.add(modul+":"+port);
					}
					PortBoks pm = new PortBoks(modul, port, boksidBak, "MAC");
					l.add(pm);
				}
			}
		}

		// Nå kan vi sjekke om CAM-køen skal settes inn i cam-tabellen eller ikke
		runCamQueue(boksid, foundBoksBak);

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

		// Modul er alltid 1 på denne typen enhet
		String modul = "1";

		HashSet foundBoksBak = new HashSet();

		for (int i=0; i<macList.size(); i++) {
			String[] s = (String[])macList.get(i);

			// Kun enheter av type 1 er lokal (type 2 = remote)
			if (Integer.parseInt(s[1]) != 1) continue;

			String port = s[0].substring(0, s[0].indexOf("."));
			String deciMac = s[0].substring(s[0].indexOf(".")+1, s[0].length());

			String mac = decimalToHexMac(deciMac);

			// Nå har vi funnet minst en MAC fra denne enheten, og da sier vi at den er oppe og aktiv,
			safeCloseBoksidAdd(boksid);

			// Prosesser Mac (CAM)
			processMac(boksid, modul, port, mac);

			if (macBoksId.containsKey(mac)) {
				String boksidBak = (String)macBoksId.get(mac);
				String boksBakKat = (String)boksidKat.get(boksidBak);
				if (boksBakKat == null || isNetel(boksBakKat)) {
					foundBoksBak.add(modul+":"+port);
				}
				PortBoks pm = new PortBoks(modul, port, boksidBak, "MAC");
				l.add(pm);
			}
		}

		// Nå kan vi sjekke om CAM-køen skal settes inn i cam-tabellen eller ikke
		runCamQueue(boksid, foundBoksBak);

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
		HashSet foundBoksBak = new HashSet();

		// Hent macadresser for hvert vlan og knytt disse til riktig mp (port)
		int activeVlanCnt=0;
		int unitVlanCnt=0;
		Set vlanSet = (Set)vlanBoksid.get(boksid);
		if (vlanSet == null) return l;

		// Så vi ikke venter så lenge dersom vi ikke får svar fra et vlan
		sSnmp.setTimeoutLimit(1);

		for (Iterator it = vlanSet.iterator(); it.hasNext();) {
			String vlan = String.valueOf(it.next());

			out("  Fetch vlan: " + vlan + "...");

			// Hent porter som er i blocking (spanning-tree) mode
			//ArrayList spanningTree = getOIDs(ip, cs_ro+"@"+vlan, spanningTreeOid);
			sSnmp.setParams(ip, cs_ro+"@"+vlan, spanningTreeOid);
			ArrayList spanningTree;
			try {
				spanningTree = sSnmp.getAll();
			} catch (TimeoutException te) {
				// Vi gjør ingenting her, ikke svar på dette vlan
				outl("timeout");
				continue;
			}
			outl("ok");

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
				HashMap blockedIfind = (HashMap)spanTreeBlocked.get(boksid+":"+vlan);
				if (blockedIfind != null) {
					// Slett eksisterende innslag i databasen
					try {
						outl("    All ports on " + sysnameMap.get(boksid) + " are now non-blocking");
						Database.update("DELETE FROM swportblocked WHERE EXISTS (SELECT swportid FROM swport JOIN module USING(moduleid) WHERE netboxid="+boksid+" AND swportblocked.swportid=swportid) AND vlan='"+vlan+"'");
						if (DB_COMMIT) Database.commit(); else Database.rollback();
					} catch (SQLException e) {
						outld("*ERROR* While deleting from swportblocked ("+boksid+","+vlan+"): SQLException: " + e.getMessage());
					}
				}

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
						// Finn porten
						String[] mp = (String[])ifindexMp.get(ifind);
						if (mp == null) {
							errl("    Error, mp not found for ifIndex: " + ifind + " on boks: " + boksIdName.get(boksid));
							continue;
						}
						swportid = (String)swportSwportidMap.get(boksid+":"+mp[0]+":"+mp[1]);
						if (swportid != null) {
							outl("    Ifindex: " + ifind + " on VLAN: " + vlan + " is now in blocking mode.");
							//String query = "INSERT INTO swportblocked (swportid,vlan) VALUES ((SELECT swportid FROM swport WHERE boksid='"+boksid+"' AND ifindex='"+ifind+"'),'"+vlan+"')";
							String query = "INSERT INTO swportblocked (swportid,vlan) VALUES ('"+swportid+"','"+vlan+"')";
							if (DB_UPDATE) {
								try {
									Database.update(query);
									if (DB_COMMIT) Database.commit(); else Database.rollback();
									blockedCnt++;
								} catch (SQLException e) {
									outld("*ERROR* SQLException: " + e.getMessage());
								}
							}
						} else {
							outla("    Error, swportid is null for mp=["+mp[0]+","+mp[1]+"] on boks: " + boksIdName.get(boksid));
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
							if (DB_COMMIT) Database.commit(); else Database.rollback();
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
				String mac = decimalToHexMac(s[0]);

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
				String modul = mp[0];
				String port = mp[1];

				// Nå har vi funnet minst en MAC fra denne enheten, og da sier vi at den er oppe og aktiv,
				safeCloseBoksidAdd(boksid);

				// Prosesser Mac (CAM)
				processMac(boksid, modul, port, mac);

				// Sjekk om vi skal ta med denne mac
				if (!macBoksId.containsKey(mac)) continue;
				String boksidBak = (String)macBoksId.get(mac);

				String boksBakKat = (String)boksidKat.get(boksidBak);
				if (boksBakKat == null || isNetel(boksBakKat)) {
					foundBoksBak.add(modul+":"+port);
				}

				//outl("  Unit: " + unit + " Port: " + port + " Mac: " + mac);
				// Legg til i listen over macer
				if (modul == null || port == null || boksidBak == null) {
					errl("--**-- errError modul|port|boksidBak null, boksid: " + boksid + " ifInd: " + ifInd + " modul: " + modul + " port: " + port + " boksidBak: "+ boksidBak);
					continue;
				}
				PortBoks pm = new PortBoks(modul, port, boksidBak, "MAC");
				if (dupCheck.contains(boksid+":"+pm)) continue;

				dupCheck.add(boksid+":"+pm);
				l.add(pm);

				if (!b) { unitVlanCnt++; b=true; }
			}
		}
		// Nå kan vi sjekke om CAM-køen skal settes inn i cam-tabellen eller ikke
		runCamQueue(boksid, foundBoksBak);

		sSnmp.setDefaultTimeoutLimit();

		outl("  MACs found on " + activeVlanCnt + " / " + vlanSet.size() + " VLANs, units on " + unitVlanCnt + ".");
		return l;
	}

	private HashMap fetchIfindexMpMap(String ip, String cs_ro, String typegruppe) throws TimeoutException
	{
		//String ciscoIndexMapBaseOid = ".1.3.6.1.2.1.17.1.4.1.2";

		// Hent kobling mellom ifIndex<->mp
		HashMap ifindexH = new HashMap();
		String ifmpBaseOid = "";
		if (typegruppe.equals("cat-sw") ||
			typegruppe.equals("cgsw")) {
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
				/*
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
				*/

				if (s[1] == null || s[1].length() == 0) {
					outla("QueryBoks.fetchIfindexMpMap(): mp is '" + s[1] + "' for ip: "+ip+" ifindex: " + s[0]);
					continue;
				}

				String[] mp = stringToMp(s[0], s[1]);

				ifindexH.put(s[0], mp);
				//outl("Add Modul: " + mp[0] + " Port: " + mp[1] + " ifIndex: " + s[0]);
			}

		} else {
			outl("  *ERROR*! Unknown typegruppe: " + typegruppe);
			//return ifindexH;
		}
		return ifindexH;
	}
	private String[] stringToMp(String ifindex, String s)
	{
		return stringToMp(ifindex, s, "1");
	}
	private String[] stringToMp(String ifindex, String s, String defaultModul)
	{
		StringTokenizer st = new StringTokenizer(s, "/");
		String modul = st.nextToken();
		String port = (st.hasMoreTokens()) ? st.nextToken() : "";

		// Hvis modul inneholder f.eks FastEther0 skal dette forkortes til Fa0
		modul = processModulName(modul);

		if (port.length() == 0) {
			port = modul;
			modul = defaultModul;
			if (modul == null || modul.length() == 0) {
				errl("stringToMp error, defaultModul: " + defaultModul+"|, ifindex: " + ifindex + " s: " + s);
			}

			try {
				Integer.parseInt(port);
			} catch (NumberFormatException e) {
				port = ifindex;
			}
		}

		return new String[] { modul, port };
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

		// Angir om vi har funnet en boks bak porten, gjør vi det skal CAM-data ikke logges på porten
		HashSet foundBoksBak = new HashSet();

		// Get the list of macs
		sSnmp.setParams(ip, cs_ro, baseOid);
		ArrayList macList;
		try {
			macList = sSnmp.getAll();
		} catch (NullPointerException e) {
			errl("  NullPointerException in QueryBoks.process3Com: boksid: " + boksid + " ip: " + ip + " boksType: " + boksType);
			e.printStackTrace(System.err);
			return l;
		}


		for (int i=0; i<macList.size(); i++) {
			String[] s = (String[])macList.get(i);

			String formatMac = formatMac(s[1].toLowerCase());
			//outl("Raw MAC: " + s[1].toLowerCase() + " Found MAC: " + formatMac);

			// Nå har vi funnet minst en MAC fra denne enheten, og da sier vi at den er oppe og aktiv,
			safeCloseBoksidAdd(boksid);

			// For testing av CAM
			//if (formatMac.equals("006097af1d45")) continue;

			StringTokenizer st = new StringTokenizer(s[0], ".");
			String modul = st.nextToken();
			String port = st.nextToken();
			if (boksType.equals("SW9300")) modul = "1";

			// Prosesser Mac (CAM)
			processMac(boksid, modul, port, formatMac);


			if (macBoksId.containsKey(formatMac)) {
				String boksidBak = (String)macBoksId.get(formatMac);
				String boksBakKat = (String)boksidKat.get(boksidBak);
				if (boksBakKat == null || isNetel(boksBakKat)) {
					foundBoksBak.add(modul+":"+port);
				}
				PortBoks pm = new PortBoks(modul, port, boksidBak, "MAC");
				l.add(pm);
			}
		}

		// Nå kan vi sjekke om CAM-køen skal settes inn i cam-tabellen eller ikke
		runCamQueue(boksid, foundBoksBak);

		return l;
	}

	/*
	 * HP
	 *
	 */
	private ArrayList processHP(String boksid, String ip, String cs_ro, String typegruppe, String boksType) throws TimeoutException
	{
		ArrayList l = new ArrayList();

		/*
		 * Først henter vi ut antall i stack'en med MIB:
		 *
		 * .1.3.6.1.4.1.11.2.14.11.5.1.10.4.1.1
		 *
		 * Denne gir ut et tall for hvert member, 0 er alltid til stedet og er commanderen
		 *
		 *
		 * .1.3.6.1.2.1.17.4.3.1.1.<desimal-mac> = <hex-mac>
         * .1.3.6.1.2.1.17.4.3.1.2.<desimal-mac> = portnummer
         * .1.3.6.1.2.1.17.4.3.1.3.<desimal-mac> = status
		 *
		 * Kun status=3 er interessant, da disse er MAC'ene switchen "lærer"
		 *
		 */

		String stackOid = "1.3.6.1.4.1.11.2.14.11.5.1.10.4.1.1";
		//String hexMacOid = "1.3.6.1.2.1.17.4.3.1.1";
		//String portMacOid = "1.3.6.1.2.1.17.4.3.1.2";
		//String statusMacOid = "1.3.6.1.2.1.17.4.3.1.3";
		String macOid = "1.3.6.1.2.1.17.4.3.1";

		// Angir om vi har funnet en boks bak porten, gjør vi det skal CAM-data ikke logges på porten
		HashSet foundBoksBak = new HashSet();

		ArrayList stackList, macList;

		try {
			// Henter først antallet i stack'en:
			sSnmp.setParams(ip, cs_ro, stackOid);
			stackList = sSnmp.getAll();

			if (stackList.isEmpty()) stackList.add(new String[] { "", "0" });
			outld("processHP: stackList.size: " + stackList.size() );

			for (int i=stackList.size()-1; i >= 0; i--) {
				String[] s = (String[])stackList.get(i);

				String modul = s[1];
				//String modul = String.valueOf(i+1);
				outld("processHP:   modul: " + modul);

				// Get the list of macs
				sSnmp.setParams(ip, cs_ro+(!s[1].equals("0")?"@sw"+s[1]:""), macOid);
				macList = sSnmp.getAll();

				// Først dytter vi all MAC inn i en hash
				HashMap macMap = new HashMap();
				int j;
				for (j=0; j<macList.size(); j++) {
					s = (String[])macList.get(j);

					String oidType = s[0].substring(0, s[0].indexOf("."));
					String key = s[0].substring(s[0].indexOf(".")+1, s[0].length());
					if (Integer.parseInt(oidType) != 1) break;

					String formatMac = formatMac(s[1].toLowerCase());
					macMap.put(key, formatMac);

					outld("processHP:     Key: " + key + " MAC: " + formatMac);

					// Nå har vi funnet minst en MAC fra denne enheten, og da sier vi at den er oppe og aktiv,
					safeCloseBoksidAdd(boksid);
				}

				// Hent port-nummer for hver MAC
				HashMap portMap = new HashMap();
				for (; j<macList.size(); j++) {
					s = (String[])macList.get(j);

					String oidType = s[0].substring(0, s[0].indexOf("."));
					String key = s[0].substring(s[0].indexOf(".")+1, s[0].length());
					if (Integer.parseInt(oidType) != 2) break;

					portMap.put(key, new Integer(s[1]));
				}

				// Til slutt går vi gjennom og registrerer alle MAC der status=3
				for (; j<macList.size(); j++) {
					s = (String[])macList.get(j);

					String oidType = s[0].substring(0, s[0].indexOf("."));
					String key = s[0].substring(s[0].indexOf(".")+1, s[0].length());
					if (Integer.parseInt(oidType) != 3) {
						errl("In processHP, boksid: " + boksid + ", oidType not in (1,2,3) found!!");
						return l;
					}

					if (Integer.parseInt(s[1]) != 3) continue;

					if (!macMap.containsKey(key) || !portMap.containsKey(key)) {
						//errl("In processHP, boksid: " + boksid + ", macMap("+macMap.containsKey(key)+") or portMap("+portMap.containsKey(key)+") not found for key: " + key);
						//errl("  macMap.size: " + macMap.size() + " + portMap.size: " + portMap.size() + " macs: " + (macList.size()-macMap.size()-portMap.size()));
						outla("In processHP, boksid: " + boksid + ", macMap("+macMap.containsKey(key)+") or portMap("+portMap.containsKey(key)+") not found for key: " + key);
						continue;
					}

					String formatMac = (String)macMap.get(key);
					String port = String.valueOf((Integer)portMap.get(key));

					// Prosesser Mac (CAM)
					processMac(boksid, modul, port, formatMac);

					if (macBoksId.containsKey(formatMac)) {
						String boksidBak = (String)macBoksId.get(formatMac);
						String boksBakKat = (String)boksidKat.get(boksidBak);
						if (boksBakKat == null || isNetel(boksBakKat)) {
							foundBoksBak.add(modul+":"+port);
						}
						outld("processHP:     Modul: " + modul + " Port: " + port + " boks: " + boksIdName.get(boksidBak));
						PortBoks pm = new PortBoks(modul, port, boksidBak, "MAC");
						l.add(pm);
					} else {
						outld("processHP:     Modul: " + modul + " Port: " + port + "  MAC: " + formatMac);
					}
				}

			}

		} catch (NullPointerException e) {
			errl("  NullPointerException in QueryBoks.processHP: boksid: " + boksid + " ip: " + ip + " boksType: " + boksType);
			e.printStackTrace(System.err);
			return l;
		}

		// Nå kan vi sjekke om CAM-køen skal settes inn i cam-tabellen eller ikke
		runCamQueue(boksid, foundBoksBak);

		return l;
	}


	/*
	 * CAM-logger
	 *
	 */
	private void processMac(String boksid, String modul, String port, String mac) {
		// Først sjekker vi om vi har en uavsluttet CAM-record for denne MAC'en
		String key = boksid+":"+modul.trim()+":"+port.trim()+":"+mac.trim();

		// Ignorer duplikater
		if (!dupeMacSet.add(key)) return;

		// Sjekk mot watchMacs
		if (watchMacs.contains(mac)) {
			reportWatchMac(boksid, modul, port, mac);
		}

		String[] s;
		synchronized (unclosedCam) {
			s = (String[])unclosedCam.get(key);
		}

		if (s != null) {
			// Har CAM-record, og siden vi fant MAC'en igjen her så skal den fortsatt være åpen dersom
			// det ikke er en boks bak denne porten
			camResetQueue.add(new String[] { modul.trim()+":"+port.trim(), key, s[0], s[1] } );

		} else {
			// Nei, da er denne MAC'en ny på porten, og vi må sette inn en record i cam-tabellen
			String[] insertData = {
				"netboxid", boksid,
				"sysname", (String)boksIdName.get(boksid),
				"module", modul.trim(),
				"port", port.trim(),
				"mac", mac.trim(),
				"start_time", "NOW()"
			};
			camInsertQueue.add(insertData);
		}
	}
	private void runCamQueue(String boksid, HashSet foundBoksBak) {
		// Først resetter vi eksisterende records der vi ikke har boksbak
		for (Iterator it = camResetQueue.iterator(); it.hasNext();) {
			String[] s = (String[])it.next();
			String mp = s[0];
			String camKey = s[1];

			if (foundBoksBak.contains(mp) || foundCDPMp.contains(mp) || foundBoksBakSwp.contains(boksid+":"+mp)) {
				//outld("    runCamQueue: Skipping reset of port: " + mp + " ("+foundBoksBak.contains(mp)+","+foundCDPMp.contains(mp)+","+foundBoksBakSwp.contains(boksid+":"+mp)+")");
				continue;
			}

			synchronized (unclosedCam) {
				unclosedCam.remove(camKey);
			}
			String camid = s[2];
			int misscnt = Integer.parseInt(s[3]);

			if (misscnt > 0) {
				// til-feltet må settes tilbake til infinity, og misscnt tilbake til 0
				String[] updateFields = {
					"end_time", "infinity",
					"misscnt", "0"
				};
				String[] condFields = {
					"camid", camid
				};
				if (DB_UPDATE) {
					try {
						Database.update("cam", updateFields, condFields);
						if (DB_COMMIT) Database.commit(); else Database.rollback();
					} catch (SQLException e) {
						outle("  SQLException in QueryBoks.processMac(): Cannot update record in cam: " + e.getMessage());
					}
				}
				camIncResetMisscnt();
			}
		}
		camResetQueue.clear();

		// Så setter vi inn evt. nye records i cam
		for (int i=0; i < camInsertQueue.size(); i++) {
			String[] insertData = (String[])camInsertQueue.get(i);
			String key = insertData[5]+":"+insertData[7]; // modul+port
			if (foundBoksBak.contains(key) || foundCDPMp.contains(key) || foundBoksBakSwp.contains(boksid+":"+key)) {
				//outld("    Skipping port: " + key + " ("+foundBoksBak.contains(key)+","+foundCDPMp.contains(key)+","+foundBoksBakSwp.contains(boksid+":"+key)+")");
				continue;
			}

			if (DB_UPDATE) {
				try {
					if (DB_UPDATE) Database.insert("cam", insertData);
					if (DB_COMMIT) Database.commit(); else Database.rollback();
					camNewCnt++;
				} catch (SQLException e) {
					outld("ERROR, SQLException: " + e.getMessage() );
				}
			}
		}
		camInsertQueue.clear();
	}
	private void safeCloseBoksidAdd(String boksid) {
		// Nå har vi funnet minst en MAC fra denne enheten, og da sier vi at den er oppe og aktiv,
		// og vi kan lukke CAM-record på den
		synchronized (safeCloseBoksid) {
			if (!safeCloseBoksid.contains(boksid)) {
				safeCloseBoksid.add(boksid);
				//System.out.println("Boksid: " + boksid + " added to safeCloseBoksid");
			}
		}
	}

	private void reportWatchMac(String boksid, String modul, String port, String mac) {
		String s = 	"The following watched MAC has been found: " + mac + "\n" +
					"\n"+
					"At " + boksIdName.get(boksid) + ", Module: " + modul + " Port: " + port + "\n" +
					"\n"+
					"Please check watchMacs.conf for whom to contact about this particular MAC";

		errl(s);
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

	private static boolean isDigit(char c)
	{
		return c >= '0' && c <= '9';
	}

	private static boolean isNetel(String kat) { return getBoksMacs.isNetel(kat); }


	private static void outa(String s) { System.out.print(s); }
	private static void outla(String s) { System.out.println(s); }

	private static void oute(Object s) { if (ERROR_OUT) System.err.print(s); }
	private static void outle(Object s) { if (ERROR_OUT) System.err.println(s); }

	private static void out(String s) { if (VERBOSE_OUT) System.out.print(s); }
	private static void outl(String s) { if (VERBOSE_OUT) System.out.println(s); }

	private static void outd(String s) { if (DEBUG_OUT) System.out.print(s); }
	private static void outld(String s) { if (DEBUG_OUT) System.out.println(s); }

	private static void err(Object o) { System.err.print(o); }
	private static void errl(Object o) { System.err.println(o); }
	private static void errflush() { System.err.flush(); }
}
