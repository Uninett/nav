/*
 * QueryBoks
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
import no.ntnu.nav.logger.*;
import no.ntnu.nav.util.*;
import no.ntnu.nav.netboxinfo.*;
import no.ntnu.nav.Database.*;
import no.ntnu.nav.SimpleSnmp.*;

/**
 * Actual data collection via SNMP.
 *
 * @version $LastChangedRevision$ $LastChangedDate$
 * @author Kristian Eide &lt;kreide@online.no&gt;
 */

public class QueryBoks extends Thread
{
	public static boolean DB_COMMIT = false;

	// Felles datastrukturer som bare skal leses fra
	public static HashMap macBoksId;
	public static HashMap boksIdName;
	public static HashMap boksidKat;
	public static HashMap boksidType;
	public static HashMap sysnameMap;
	public static Set downBoksid;

	public static HashMap spanTreeBlocked;

	public static HashSet cdpBoks;

	// Inneholder alle boksid'er som er av kat=GW
	public static HashSet boksGwSet;

	// Mapping fra boksid+ifindex swportid i swport
	public static HashMap swportidMap;
	public static Set swportNetboxSet;

	// Denne inneholder alle "boksid:ifindex" fra swport som er trunk-porter
	//public static HashSet boksIfindexTrunkSet;

	// Mengde av vlan som må sjekkes på Cisco-boksene
	public static Map vlanBoksid;

	// Hvilke porter det står en GW|SW|EDGE bak, som gitt i swp_boks-tabellen
	static HashSet foundBoksBakSwp;
	public static void setFoundBoksBakSwp(HashSet hs) { foundBoksBakSwp = hs; }

	// OID db
	public static Map oidDb;
	public static Map vlanMap;
	public static Map interfaceMap;
	public static Map mpMap;

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
	Map oidkeys;

	SimpleSnmp sSnmp;

	static long lastActivity = System.currentTimeMillis();

	// Konstruktør
	public QueryBoks(int num, String id, Stack bdStack, int antBd, HashSet swp, HashMap swp_d)
	{
		this.num = num;
		this.id = id;
		this.bdStack = bdStack;
		this.antBd = antBd;
		this.swp = swp;
		this.swp_d = swp_d;
		Log.setDefaultSubsystem("QUERYBOKS");
		this.setName("QueryBoks-" + id);
	}

	public static void initThreadDone(final int NUM_THREADS)
	{
		threadDone = new boolean[NUM_THREADS];
		for (int i=0; i < threadDone.length; i++) {
			threadDone[i] = false;
		}
	}

	private String getOid(String oidkey) {
		if (!oidkeys.containsKey(oidkey)) {
			Log.d("GET_OID", "This device does not support this oidkey: " + oidkey);
			return null;
		}
		return (String)oidkeys.get(oidkey);
	}


	public void run()
	{
		Log.setDefaultSubsystem("QUERY_NETBOX");
		Log.setThreadId(id);

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
			Log.setNetbox(bd.sysName);

			String ip = bd.ip;
			String cs_ro = bd.cs_ro;
			String boksId = bd.boksId;
			String boksType = bd.boksType;
			String sysName = bd.sysName;
			String kat = bd.kat;
			String vendor = bd.vendor;
			boolean csAtVlan = bd.csAtVlan;
			boolean cdp = bd.cdp;
			oidkeys = (Map)oidDb.get(boksId);
			if (oidkeys == null) {
				Log.d("RUN", "Missing OID keys for netbox: " + boksId + ", skipping " + sysName);
				continue;
			}

			sSnmp = SimpleSnmp.simpleSnmpFactory();
			sSnmp.setHost(ip);
			sSnmp.setCs_ro(cs_ro);

			Log.d("RUN", "Now working with("+boksId+"): " + sysName + " ("+ boksType +") ("+ ip +") ("+ bdRemaining +" of "+ antBd+" left)");
			long boksBeginTime = System.currentTimeMillis();

			// Liste over alle innslagene vi evt. skal sette inn i swp_boks
			List netboxList = new ArrayList();

			// Liste over porter der vi har funnet boks via CDP
			foundCDPMp.clear();

			// OK, prøv å spørre
			try {
				if (cdp) {
					List l = processCDP(boksId);
					netboxList.addAll(l);
				}
				
				if (kat.equalsIgnoreCase("GW")) {
					// GW'er behandles annerledes, vi skal oppdatere boksbak og evt. swportbak i gwport
					for (Iterator netboxIt = netboxList.iterator(); netboxIt.hasNext();) {
						PortBoks pm = (PortBoks)netboxIt.next();
						String remoteIf = pm.getRemoteIf();
						
						if (boksGwSet.contains(pm.getToNetboxid())) continue;
						
						String to_swportid = (String)interfaceMap.get(pm.getToNetboxid()+":"+remoteIf);
						if (pm.getRemoteIf() != null && to_swportid == null) {
							if (swportNetboxSet.contains(pm.getToNetboxid())) {
								Log.i("RUN", "Cannot find swport: ("+pm.getToNetboxid()+") "+boksIdName.get(pm.getToNetboxid())+" If: " + pm.getRemoteIf() + " (" + boksId + ")");
							} else {
								Log.i("RUN", "Link, but no swports, for: ("+pm.getToNetboxid()+") "+boksIdName.get(pm.getToNetboxid())+" If: " + pm.getRemoteIf() + " (" + boksId + ")");
							}
							continue;
						}

						// OK, da er vi klar, oppdater gwport!
						if (boksType.equals("cat6kMsfc") || // MSFC
							boksType.equals("cat6kMsfc2") || // MSFC1
							boksType.equals("cisWSX5302") || boksType.equals("Cis-WX5302") ) { // RSM
							
							Database.update("UPDATE gwport SET to_netboxid = '"+pm.getToNetboxid()+"', to_swportid = "+to_swportid+" WHERE gwportid IN (SELECT gwportid FROM module JOIN gwport USING(moduleid) JOIN gwportprefix USING(gwportid) WHERE netboxid = '"+boksId+"')");
							if (DB_COMMIT) Database.commit(); else Database.rollback();
							Log.d("RUN", "["+boksType+"] Ifindex: " + pm.getIfindex() + " Interface: " + remoteIf + ", " + boksIdName.get(pm.getToNetboxid()) );
							continue;
						}
					
						Database.update("UPDATE gwport SET to_netboxid = '"+pm.getToNetboxid()+"', to_swportid = "+to_swportid+" WHERE moduleid IN (SELECT moduleid FROM module WHERE netboxid = '"+boksId+"') AND ifindex='" + pm.getIfindex() + "'");
						if (DB_COMMIT) Database.commit(); else Database.rollback();
						
						Log.d("RUN", "[GW] Ifindex: " + pm.getIfindex() + " Interface: " + remoteIf + ", " + boksIdName.get(pm.getToNetboxid()) );
					}
				
					long boksUsedTime = System.currentTimeMillis() - boksBeginTime;
					synchronized (boksReport) {
						boksReport.add(new BoksReport((int)boksUsedTime, bd));
					}
					continue;
				}
				
				// Hent inn boksbak via matching mot MAC-adresser
				List macList = new ArrayList();
				// tag
				
				macList.addAll(processMacEntry(boksId, ip, cs_ro, boksType, csAtVlan));
				
				/*
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
				*/
				
				// Før MAC-listen kan legges til boksListe må alle konflikter med CDP tas bort
				for (Iterator macIt = macList.iterator(); macIt.hasNext();) {
					PortBoks pm = (PortBoks)macIt.next();
					String ifindex = pm.getIfindex();
					if (foundCDPMp.contains(ifindex)) {
						// Vi har funnet CDP på denne porten, støtter denne også CDP tar vi den bort
						if (cdpBoks.contains(pm.getToNetboxid())) {
							Log.d("RUN", "[CDP-DEL] ifindex: " + ifindex + ", " + boksIdName.get(pm.getToNetboxid()) );
							continue;
						}
					}
					netboxList.add(pm);
				}
			} catch (SQLException se) {
				Log.d("RUN", "SQLException: " + se.getMessage());
				System.err.println("SQLException: " + se.getMessage());
				if (se.getMessage() != null && se.getMessage().indexOf("Exception: java.net.SocketException") != -1) {
					// Mistet kontakten med serveren, abort
					Log.d("RUN", "Lost contact with backend, fatal error!");
					System.err.println("QueryBoks.run(): Exiting...");
					System.exit(2);
				}
				se.printStackTrace(System.err);
			} catch (TimeoutException te) {
				Log.d("RUN", "*** GIVING UP ON: " + sysName + ", typename: " + boksType + " ***");
				continue;
			} catch (NullPointerException exp) {
				Log.w("RUN", "NullPointerException, aborting thread. Exception: " + exp.getMessage());
				exp.printStackTrace(System.err);
			} catch (Exception exp) {
				Log.e("RUN", "Fatal error, aborting. Exception: " + exp.getMessage());
				exp.printStackTrace(System.err);
				System.exit(1);
			} finally {
				sSnmp.destroy();
				sSnmp = null;
			}

			Collections.sort(netboxList);
			int newCnt=0,dupCnt=0;
			List printList = new ArrayList();
			for (Iterator netboxIt = netboxList.iterator(); netboxIt.hasNext();) {
				PortBoks pm = (PortBoks)netboxIt.next();
				String key = boksId+":"+pm;
				String new_to_swportid = (String)interfaceMap.get(pm.getToNetboxid()+":"+pm.getRemoteIf());

				// En enhet kan ikke ha link til seg selv
				if (boksId.equals(pm.getToNetboxid())) continue;

				// Dersom boksen bak er nede skal vi ikke endre
				if (downBoksid.contains(pm.getToNetboxid())) continue;

				if (pm.getRemoteIf() != null && new_to_swportid == null) {
					if (swportNetboxSet.contains(pm.getToNetboxid())) {
						Log.i("RUN", "Cannot find swport: ("+pm.getToNetboxid()+") "+boksIdName.get(pm.getToNetboxid())+" If: " + pm.getRemoteIf() + " (" + boksId + ")");
					} else {
						Log.i("RUN", "Link, but no swports, for: ("+pm.getToNetboxid()+") "+boksIdName.get(pm.getToNetboxid())+" If: " + pm.getRemoteIf() + " (" + boksId + ")");
					}
				}

				// Sjekk om dette er en duplikat
				if (swp.contains(key)) {
					String swp_boksid = null, to_swportid = null;
					int misscnt=0;
					synchronized (swp_d) {
						if (swp_d.containsKey(key)) {
							HashMap hm = (HashMap)swp_d.remove(key);
							swp_boksid = (String)hm.get("swp_netboxid");
							misscnt = Integer.parseInt((String)hm.get("misscnt"));
							to_swportid = (String)hm.get("to_swportid");
						} else {
							// Dup
							continue;
						}
					}
					if (swp_boksid != null && misscnt > 0) {
						// Nå må vi også resette misscnt i recorden i swp_boks
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
							Log.d("RUN", "Reseting swp_netboxid: " + swp_boksid + " in swp_netbox, SQLException: " + e.getMessage() );
						}
						swpIncResetMisscnt();
					}

					if (new_to_swportid != null) {
						// Nå må vi sjekke om ifindex feltet har endret seg
						if (!new_to_swportid.equals(to_swportid)) {
							try {
								if (swp_boksid == null || swp_boksid.length() == 0) {
									System.err.println("swp_boksid null for " + key + " swp: " + swp.contains(key) + " swp_d: " + swp_d.get(key));
								}
								String[] upd = {
									"to_swportid", new_to_swportid
								};
								String[] where = {
									"swp_netboxid", swp_boksid
								};
								Database.update("swp_netbox", upd, where);
								if (DB_COMMIT) Database.commit(); else Database.rollback();
							} catch (SQLException e) {
								System.err.println("Update modulbak/portbak in swp_boks, swp_boksid: " + swp_boksid + ", to_ifindex: " + pm.getRemoteIf() + "\n  SQLException: " + e.getMessage() );
								e.printStackTrace(System.err);
							}
						}
					}

					//String s = "T"+id+":    [DUP] Modul: " + pm.getModulS() + " Port: " + pm.getPortS() + ", " + getBoksMacs.boksIdName.get(pm.getBoksId());
					//printList.add(s);
					dupCnt++;
					continue;
				}

				// Legg til i listen så vi ikke får duplikater
				synchronized (swp) {
					swp.add(key);
				}
				//outl("T"+id+":    ["+pm.getSource()+"] Modul: " + pm.getModulS() + " Port: " + pm.getPortS() + ", " + getBoksMacs.boksIdName.get(pm.getBoksId()) );


				boolean verify1=true, verify2=true;
				if ((verify1=verifyNetboxid(boksId)) && (verify2=verifyNetboxid(pm.getToNetboxid()))) {
					String[] ins = {
						"netboxid", boksId,
						"ifindex", pm.getIfindex(),
						"to_netboxid", pm.getToNetboxid(),
						"to_swportid", new_to_swportid
					};
					
					try {
						Database.insert("swp_netbox", ins);
						if (DB_COMMIT) Database.commit(); else Database.rollback();
						newCnt++;
					} catch (SQLException e) {
						Log.d("RUN", "Insert into swp_netbox ("+key+"), SQLException: " + e.getMessage() );
						e.printStackTrace(System.err);
					}
				} else {
					if (!verify1) Log.d("VERIFY_NETBOXID", "Verify netboxid ("+boksId+") failed");
					if (!verify2) Log.d("VERIFY_NETBOXID", "Verify to netboxid ("+pm.getToNetboxid()+") failed");
				}
			}

			/*
				Collections.sort(printList);
				for (Iterator j=printList.iterator(); j.hasNext();) {
				outl(String.valueOf(j.next()));
				}
			*/
			
			if (newCnt > 0 || dupCnt > 0) {
				Log.d("RUN", "Fount a total of " + newCnt + " new units, " + dupCnt + " duplicate units.");
			}
			
			long boksUsedTime = System.currentTimeMillis() - boksBeginTime;
			synchronized (boksReport) {
				boksReport.add(new BoksReport((int)boksUsedTime, bd));
			}
			
			lastActivity = System.currentTimeMillis();
		}
		
		long usedTime = System.currentTimeMillis() - beginTime;
		threadDone[num] = true;
		Log.freeThread();
		Log.d("RUN", "** Thread done, time used: " + getBoksMacs.formatTime(usedTime) + ", waiting for " + getThreadsNotDone() + " **");
	}

	private boolean verifyNetboxid(String netboxid) {
		try {
			ResultSet rs = Database.query("SELECT netboxid FROM netbox WHERE netboxid='"+netboxid+"'");
			if (rs.next()) return true;
		} catch (SQLException e) {
			Log.d("VERIFY_NETBOXID", "Verify netboxid ("+netboxid+"), SQLException: " + e.getMessage() );
			e.printStackTrace(System.err);
		}
		Log.w("VERIFY_NETBOXID", "Netbox ("+netboxid+") " + boksIdName.get(netboxid) + " no longer exists!");
		return false;
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
	private ArrayList processCDPCisco(String workingOnBoksid, String ip, String cs_ro, HashMap ifindexMp) throws SQLException, TimeoutException
	{

	}

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
	/*
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
*/

	/*
	 * Shared CDP processing
	 *
	 */
	private List processCDP(String workingOnBoksid) throws SQLException, TimeoutException {
		List l = new ArrayList();

		List cdpList = sSnmp.getAll(getOid("cdpNeighbour"), true, 1);
		if (cdpList == null || cdpList.isEmpty()) {
			Log.d("PROCESS_CDP", "cdpList is " + cdpList + " for netboxid: " + workingOnBoksid + " OID: " + getOid("cdpNeighbour") );
			return l;
		}

		// Vi har fått noe via CDP, da kan vi trygt lukke CAM records
		safeCloseBoksidAdd(workingOnBoksid);

		Map remoteIfMap = sSnmp.getAllMap(getOid("cdpRemoteIf"), true, 1);

		Log.d("PROCESS_CDP", "cdpList.size: " + cdpList.size());
		if (remoteIfMap == null) {
			remoteIfMap = new HashMap();
			Log.w("PROCESS_CDP", "Box supports cdpNeighbour, but not cdpRemoteIf. Run OID test again?");
		} else {
			if (cdpList.size() != remoteIfMap.size()) Log.d("PROCESS_CDP", "cdpList != remoteIfMap ("+cdpList.size()+" != "+remoteIfMap.size()+").");
		}

		// Hent liste over alle gamle ifindekser slik at vi kan slette de som ikke lenger eksisterer
		List unrecognizedCDP = new ArrayList();
		Set oldUnrecIfind = new HashSet();
		for (Iterator it = NetboxInfo.get(workingOnBoksid, "unrecognizedCDP", null); it.hasNext();) {
			String[] s = (String[])it.next();
			oldUnrecIfind.add(s[0]);
		}

		for (Iterator it = cdpList.iterator(); it.hasNext();) {
			String[] cdps = (String[])it.next();
			String ifindex = cdps[0];
			String remoteName = cdps[1];
			String remoteIf = (String)remoteIfMap.get(ifindex);

			String[] netboxidA = extractNetboxid(remoteName);
			if (netboxidA == null) {
				Log.d("PROCESS_CDP", "Not found, ("+workingOnBoksid+") "+boksIdName.get(workingOnBoksid)+", Ifindex: " + ifindex + " String: " + remoteName);
				unrecognizedCDP.add(new String[] { ifindex, remoteName });
				oldUnrecIfind.remove(ifindex);
				continue;
			}
			String netboxid = netboxidA[0];
			String sysname = (String)boksIdName.get(netboxid);

			// Opprett record for boksen bak porten
			PortBoks pm = new PortBoks(ifindex, netboxid, "CDP");
			if (netboxidA.length > 1) {
				// Vi har også med modulnummer
				String zero = "";
				try {
					if (Integer.parseInt(remoteIf) < 10) zero = "0";
				} catch (NumberFormatException exp) { }
				remoteIf = (Integer.parseInt(netboxidA[1])+1) + zero + remoteIf;
			}
			pm.setRemoteIf(remoteIf);
			l.add(pm);

			foundCDPMp.add(ifindex);
			Log.d("PROCESS_CDP", "Ifindex: " + ifindex + " CDP: " + sysname + " remoteIf: " + remoteIf);

			// Nå vet vi at vi har funnet en boks via CDP bak denne porten, og da kan det ikke være andre Cisco eller HP-enheter bak her
			try {
				ResultSet rs = Database.query("SELECT COUNT(*) AS count FROM swp_netbox WHERE netboxid='"+workingOnBoksid+"' AND ifindex='"+ifindex+"' AND to_netboxid!='"+pm.getToNetboxid()+"' AND to_netboxid IN (SELECT netboxid FROM netbox JOIN type USING(typeid) WHERE cdp='t')");
				if (rs.next() && rs.getInt("count") > 0) {
					String sql = "DELETE FROM swp_netbox WHERE netboxid='"+workingOnBoksid+"' AND ifindex='"+ifindex+"' AND to_netboxid!='"+pm.getToNetboxid()+"' AND to_netboxid IN (SELECT netboxid FROM netbox JOIN type USING(typeid) WHERE cdp='t')";
					Log.d("PROCESS_CDP", "MUST DELETE("+rs.getInt("count")+"): " + sql);
					Database.update(sql);
					if (DB_COMMIT) Database.commit(); else Database.rollback();
				}
			} catch (SQLException e) {
				Log.d("PROCESS_CDP", "SQLException: " + e.getMessage());
				e.printStackTrace(System.err);
			}
			
			// Dersom denne porten går fra ikke-gw (sw,kant) til gw må vi slå remote interface opp i gwport
			// slik at vi kan sette boksbak og swportbak.
			if (!boksGwSet.contains(workingOnBoksid) && boksGwSet.contains(pm.getToNetboxid())) {
				// OK, ikke-gw -> gw
				String swportid = (String)swportidMap.get(workingOnBoksid+":"+ifindex);
				if (swportid != null) {
					// Setter boksbak og swportbak for alle matchende interfacer
					Log.d("PROCESS_CDP", "Updating boksbak("+workingOnBoksid+"), swportbak("+swportid+") for gw: " + boksIdName.get(netboxid)+", rIf: " + remoteIf);
					Database.update("UPDATE gwport SET to_netboxid = '"+workingOnBoksid+"', to_swportid = '"+swportid+"' WHERE moduleid IN (SELECT moduleid FROM module WHERE netboxid='"+netboxid+"') AND interface = '"+remoteIf+"'");
					if (DB_COMMIT) Database.commit(); else Database.rollback();
				}
			}
			
		}
		
		for (Iterator it = unrecognizedCDP.iterator(); it.hasNext();) {
			// Write this to netboxinfo
			String[] s = (String[])it.next();
			NetboxInfo.put(workingOnBoksid, "unrecognizedCDP", s[0], s[1]);
		}
		for (Iterator it = oldUnrecIfind.iterator(); it.hasNext();) {
			String ifindex = (String)it.next();
			NetboxInfo.remove(workingOnBoksid, "unrecognizedCDP", ifindex);
		}
		
		return l;
	}
		

	private String[] extractNetboxid(String s)
	{
		// Vi skal prøve å finne en boksid ut fra CDP strengen, som kan f.eks se slik ut:

		// 069003402(hb-sw)
		// tekno-sw200C01D80CEA4
		// ntnu-gw2.ntnu.no

		// HP
		// mar-ans-601-1(000a57-b8d3c0)

		String[] r;

		// Først prøver vi bare strengen
		if (sysnameMap.containsKey(s)) {
			return new String[] { (String)sysnameMap.get(s) };
		}

		// Så sjekker vi etter paranteser
		int i;
		if ( (i=s.indexOf("(")) != -1) {
			int end = s.indexOf(")");
			if (end != -1) {
				String n = s.substring(i+1, end);
				if (sysnameMap.containsKey(n)) {
					return new String[] { (String)sysnameMap.get(n) };
				}
				if ( (r=extractNetboxid(n)) != null) return r;
				s = s.substring(0, i);
			}
		}

		// No match so far, check if this is a HP stack member (-#)
		if (s.matches(".*-\\d")) {
			String sn = s.substring(0, s.length()-2);
			if ((r=extractNetboxid(sn)) != null) {
				return new String[] { r[0], s.substring(s.length()-1, s.length()) };
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
		if (cur != null) return new String[] { cur };

		// Så tar vi strengen motsatt vei, bare for sikkerhets skyld
		sb = new StringBuffer();
		for (i=s.length()-1; i >= 0; i--) {
			sb.insert(0, s.charAt(i));
			if (sysnameMap.containsKey(sb.toString() )) {
				cur = (String)sysnameMap.get(sb.toString() );
			}
		}
		if (cur != null) return new String[] { cur };

		return null;
	}


	
	private List processMacEntry(String netboxid, String ip, String cs_ro, String type, boolean csAtVlan) throws TimeoutException {
		List l = new ArrayList();

		// HashSet for å sjekke for duplikater
		HashSet dupCheck = new HashSet();
		HashSet foundBoksBak = new HashSet();

		// Hent macadresser for hvert vlan og knytt disse til ifindex
		int activeVlanCnt=0;
		int unitVlanCnt=0;

		Set vlanSet;
		if (csAtVlan) {
			vlanSet = (Set)vlanBoksid.get(netboxid);
			if (vlanSet == null) {
				Log.d("PROCESS_MAC", "Missing vlanSet for netboxid: " + netboxid + ", aborting");
				return l;
			}
		} else {
			vlanSet = new HashSet();
			vlanSet.add("");
		}

		// Så vi ikke venter så lenge dersom vi ikke får svar fra et vlan
		sSnmp.setTimeoutLimit(1);

		for (Iterator it = vlanSet.iterator(); it.hasNext();) {
			String vlan = String.valueOf(it.next());
			String useCs = cs_ro + (vlan.length() == 0 ? "" : "@"+vlan);
			sSnmp.setParams(ip, useCs, "1");

			Log.d("MAC_ENTRY", "Fetching vlan: " + vlan);

			// Hent porter som er i blocking (spanning-tree) mode
			List stpList;
			try {
				List mpBlocked = new ArrayList();

				stpList = sSnmp.getAll(getOid("stpPortState"));
				if (stpList != null) {
					for (Iterator stpIt = stpList.iterator(); stpIt.hasNext();) {
						String[] s = (String[])stpIt.next();
						if (s[1].equals("2")) mpBlocked.add(s[0]);
					}
					
					if (mpBlocked.size() == 0) {
						// Nå vet vi at ingen porter er blokkert på denne enheten på dette vlan
						HashMap blockedIfind = (HashMap)spanTreeBlocked.get(netboxid+":"+vlan);
						if (blockedIfind != null) {
							// Slett eksisterende innslag i databasen
							try {
								Log.d("MAC_ENTRY", "All ports on " + boksIdName.get(netboxid) + " are now non-blocking");
								String sql = "DELETE FROM swportblocked WHERE EXISTS (SELECT swportid FROM swport JOIN module USING(moduleid) WHERE netboxid="+netboxid+" AND swportblocked.swportid=swportid)";
								if (csAtVlan) sql += " AND vlan='"+vlan+"'";
								Database.update(sql);
								if (DB_COMMIT) Database.commit(); else Database.rollback();
							} catch (SQLException e) {
								Log.d("MAC_ENTRY", "While deleting from swportblocked ("+netboxid+","+vlan+"): SQLException: " + e.getMessage());
								e.printStackTrace(System.err);
							}
						}
					}
				}

				// Hent macadresser på dette vlan
				List macVlan = sSnmp.getAll(getOid("macPortEntry"));

				Map portIndexMap = null;
				if (macVlan == null) {
					// Try 3Com SS mac
					macVlan = sSnmp.getAll(getOid("3cSSMac"));
					if (macVlan != null) {
						// We need to rewrite the list to match macPortEntry format, as well as create a portIndexMap
						List newMacVlan = new ArrayList();
						portIndexMap = new HashMap();
						for (Iterator macIt = macVlan.iterator(); macIt.hasNext();) {
							String[] s = (String[])macIt.next();
							String[] mp = s[0].split("\\.");
							int module = Integer.parseInt(mp[0]);
							int port = Integer.parseInt(mp[1]);
							String ifindex = module + (port<10?"0":"") + port;
							newMacVlan.add(new String[] { util.join(mp, ".", 2), ifindex });
							portIndexMap.put(ifindex, ifindex);
						}
						macVlan = newMacVlan;
					}
				}

				if (mpBlocked.isEmpty() && (macVlan == null || macVlan.isEmpty())) continue;
						
				// Hent mapping mellom ifIndex og intern portindex
				if (portIndexMap == null) {
					portIndexMap = sSnmp.getAllMap(getOid("basePortIfIndex"));
				}

				if (portIndexMap != null) {
					int blockedCnt=0;
					if (mpBlocked.size() > 0) {
						Map blockedIfind = (Map)spanTreeBlocked.get(netboxid+":"+vlan);
						if (blockedIfind == null) blockedIfind = new HashMap(); // Ingen porter er blokkert på dette vlan
							
						for (Iterator blockIt = mpBlocked.iterator(); blockIt.hasNext();) {
							String s = (String)blockIt.next();
							String ifindex = (String)portIndexMap.get(s);
							if (ifindex == null) continue;
								
							// OK, nå kan vi sjekke om denne eksisterer fra før
							String swportid = (String)blockedIfind.remove(ifindex);
							if (swportid == null) {
								// Eksisterer ikke fra før, må settes inn, hvis den eksisterer i swport
								swportid = (String)swportidMap.get(netboxid+":"+ifindex);
								if (swportid != null) {
									// Find correct vlan
									String dbVlan = (vlan.length() == 0 ? (String)vlanMap.get(netboxid+":"+ifindex) : vlan);
									if (dbVlan == null) {
										Log.d("MAC_ENTRY", "Netboxid: " + netboxid + " blocked ifindex: " + ifindex + " is missing VLAN for swportid: " + swportid);
										continue;
									}
									Log.d("MAC_ENTRY", "Ifindex: " + ifindex + " on VLAN: " + dbVlan + " ("+vlan+") is now in blocking mode (swportid="+swportid+")");
									try {
										String[] ins = {
											"swportid", swportid,
											"vlan", dbVlan
										};
										Database.insert("swportblocked", ins);
										if (DB_COMMIT) Database.commit(); else Database.rollback();
										blockedCnt++;
									} catch (SQLException e) {
										Log.d("MAC_ENTRY", "SQLException: " + e.getMessage());
										e.printStackTrace(System.err);
									}
								} else {
									Log.d("MAC_ENTRY", "Missing swportid for ifindex " + ifindex + " on boks: " + boksIdName.get(netboxid));
								}
							} else {
								blockedCnt++;
							}
						}
						// Nå har vi tatt bort alle porter som fortsatt er blokkert, og resten er da ikke blokkert, så de må slettes
						for (Iterator iter = blockedIfind.entrySet().iterator(); iter.hasNext();) {
							Map.Entry me = (Map.Entry)iter.next();
							String swportid = (String)me.getKey();
							String ifindex = (String)me.getValue();
							String dbVlan = (vlan.length() == 0 ? (String)vlanMap.get(netboxid+":"+ifindex) : vlan);
							String sql = "DELETE FROM swportblocked WHERE swportid='"+swportid+"'";
							if (dbVlan == null) {
								Log.d("MAC_ENTRY", "swportid: " + swportid + " (vlan not found, ifindex: " + ifindex+") is no longer in blocking mode.");
							} else {
								sql += " AND vlan='"+dbVlan+"'";
							}
							Log.d("MAC_ENTRY", "swportid: " + swportid + " on VLAN: " + dbVlan + " ("+vlan+") is no longer in blocking mode.");
							try {
								Database.update(sql);
								if (DB_COMMIT) Database.commit(); else Database.rollback();
							} catch (SQLException e) {
								Log.d("MAC_ENTRY", "SQLException: " + e.getMessage());
								e.printStackTrace(System.err);
							}
						}
					}
					if (macVlan == null || macVlan.size() == 0) continue;

					if (!csAtVlan) vlan = "[all]";
					Log.d("MAC_ENTRY", "Querying vlan: " + vlan + ", MACs: " + macVlan.size() + " Mappings: " + portIndexMap.size() + " Blocked: " + blockedCnt + " / " + mpBlocked.size() );
						
					activeVlanCnt++;
					boolean b = false;
					for (Iterator vlanIt = macVlan.iterator(); vlanIt.hasNext();) {
						String[] s = (String[])vlanIt.next();
						String mac = decimalToHexMac(s[0]);
						if (mac.length() != 12) {
							Log.d("PROCESS_MAC", "Wrong length: " + s[0] + " vs " + mac);
						}
						//Log.d("MAC_ENTRY", "Found mac: " + mac + " portIndex: " + s[1] + "("+ boksIdName.get(macBoksId.get(mac)) +")");
							
						// Sjekk om MAC adressen vi har funnet er dem samme som den for enheten vi spør
						// Dette skjer på C35* enhetene.
						if (netboxid.equals(macBoksId.get(mac))) continue;
							
						// Finn ifIndex
						String ifindex = (String)portIndexMap.get(s[1]);
						if (ifindex == null) {
							if (!"0".equals(s[1])) {
								Log.d("MAC_ENTRY", "MAC: " + mac + " (" + s[0] + ") ("+ boksIdName.get(macBoksId.get(mac)) +") found at index: " + s[1] + ", but no ifIndex mapping exists.");
							}
							continue;
						}
							
						// Nå har vi funnet minst en MAC fra denne enheten, og da sier vi at den er oppe og aktiv,
						safeCloseBoksidAdd(netboxid);
							
						// Prosesser Mac (CAM)
						processMac(netboxid, ifindex, mac);
							
						// Sjekk om vi skal ta med denne mac
						if (!macBoksId.containsKey(mac)) continue;
						String to_netboxid = (String)macBoksId.get(mac);
							
						String to_cat = (String)boksidKat.get(to_netboxid);
						if (to_cat == null || isNetel(to_cat)) {
							foundBoksBak.add(ifindex);
						}

						PortBoks pm = new PortBoks(ifindex, to_netboxid, "MAC");
						if (dupCheck.contains(netboxid+":"+pm)) continue;
						dupCheck.add(netboxid+":"+pm);

						l.add(pm);							
					}
				}

			} catch (TimeoutException te) {
				// Vi gjør ingenting her, ikke svar på dette vlan
				continue;
			}

		}
		// Nå kan vi sjekke om CAM-køen skal settes inn i cam-tabellen eller ikke
		runCamQueue(netboxid, foundBoksBak);

		sSnmp.setDefaultTimeoutLimit();

		Log.d("MAC_ENTRY", "MACs found on " + activeVlanCnt + " / " + vlanSet.size() + " VLANs, units on " + unitVlanCnt + ".");
		return l;
	}

	
	/*
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
		List l;
		//String ciscoIndexMapBaseOid = ".1.3.6.1.2.1.17.1.4.1.2";

		// Hent kobling mellom ifIndex<->mp
		HashMap ifindexH = new HashMap();
		
		if (l != null) {
			outl("  Found " + l.size() + " ifindex<->mp mappings.");
			for (int i=0; i < l.size(); i++) {
				String[] s = (String[])l.get(i);
				StringTokenizer st = new StringTokenizer(s[0], ".");
				String[] mp = { st.nextToken(), st.nextToken() };
				ifindexH.put(s[1], mp);
			}			
		} else {
			l = sSnmp.getAll(nb.getOid("ifDescr"), true);
			if (l != null) {
				outl("  Found " + l + " ifindex<->mp mappings.");
				for (int i=0; i < l.size(); i++) {
					String[] s = (String[])l.get(i);
					
					if (s[1] == null || s[1].length() == 0) {
						outla("QueryBoks.fetchIfindexMpMap(): mp is '" + s[1] + "' for ip: "+ip+" ifindex: " + s[0]);
						continue;
					}
					
					String[] mp = stringToMp(Integer.parseInt(s[0]), s[1]);
					
					ifindexH.put(s[0], mp);
				}
			}
		}
		return ifindexH;
	}
	private int[] stringToMp(int ifindex, String s)
	{
		return stringToMp(ifindex, s, 1);
	}
	private int[] stringToMp(int ifindex, String s, int defaultModule)
	{
		int module, port;
		Matcher m = Pattern.compile(".*(\\d+).*(\\d+).*").matcher(s);
		if (m.matches()) {
			module = Integer.parseInt(m.group(1));
			port = Integer.parseInt(m.group(2));
		} else {
			module = defaultModule;
			m = Pattern.compile(".*(\\d+).*").matcher(s);
			if (m.maches()) {
				port = Integer.parseInt(m.group(1));
			} else {
				port = ifindex;
			}
		}

		return new int[] { module, port };
	}

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

	/*
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
	*/


	/*
	 * CAM-logger
	 *
	 */
	private void processMac(String netboxid, String ifindex, String mac) {
		// Først sjekker vi om vi har en uavsluttet CAM-record for denne MAC'en
		String key = netboxid+":"+ifindex.trim()+":"+mac.trim();

		// Ignorer duplikater
		if (!dupeMacSet.add(key)) return;

		// Sjekk mot watchMacs
		if (watchMacs.contains(mac)) {
			reportWatchMac(netboxid, ifindex, mac);
		}

		String[] s;
		synchronized (unclosedCam) {
			s = (String[])unclosedCam.get(key);
		}

		if (s != null) {
			// Har CAM-record, og siden vi fant MAC'en igjen her så skal den fortsatt være åpen dersom
			// det ikke er en boks bak denne porten
			camResetQueue.add(new String[] { ifindex, key, s[0], s[1] } );

		} else {
			// Nei, da er denne MAC'en ny på porten, og vi må sette inn en record i cam-tabellen
			s = (String[])mpMap.get(netboxid+":"+ifindex);
			if (s == null) s = new String[2];
			String[] insertData = {
				"netboxid", netboxid,
				"sysname", (String)boksIdName.get(netboxid),
				"ifindex", ifindex,
				"module", s[0],
				"port", s[1],
				"mac", mac.trim(),
				"start_time", "NOW()"
			};
			camInsertQueue.add(insertData);
		}
	}
	private void runCamQueue(String netboxid, Set foundBoksBak) {
		// Først resetter vi eksisterende records der vi ikke har boksbak
		for (Iterator it = camResetQueue.iterator(); it.hasNext();) {
			String[] s = (String[])it.next();
			String ifindex = s[0];
			String camKey = s[1];

			if (foundBoksBak.contains(ifindex) || foundCDPMp.contains(ifindex) || foundBoksBakSwp.contains(netboxid+":"+ifindex)) {
				//outld("    runCamQueue: Skipping reset of port: " + mp + " ("+foundBoksBak.contains(mp)+","+foundCDPMp.contains(mp)+","+foundBoksBakSwp.contains(boksid+":"+mp)+")");
				continue;
			}

			synchronized (unclosedCam) {
				unclosedCam.remove(camKey);
			}
			String camid = s[2];
			int misscnt = 1;
			try {
				misscnt = Integer.parseInt(s[3]);
			} catch (NumberFormatException e) {
			}

			if (misscnt > 0) {
				// til-feltet må settes tilbake til infinity, og misscnt tilbake til 0
				String[] updateFields = {
					"end_time", "infinity",
					"misscnt", "0"
				};
				String[] condFields = {
					"camid", camid
				};
				try {
					Database.update("cam", updateFields, condFields);
					if (DB_COMMIT) Database.commit(); else Database.rollback();
				} catch (SQLException e) {
					Log.d("RUN_CAM_QUEUE", "SQLException: Cannot update record in cam: " + e.getMessage());
					e.printStackTrace(System.err);
				}
			}
			camIncResetMisscnt();
		}
		camResetQueue.clear();

		// Så setter vi inn evt. nye records i cam
		for (int i=0; i < camInsertQueue.size(); i++) {
			String[] insertData = (String[])camInsertQueue.get(i);
			String ifindex = insertData[5];
			if (foundBoksBak.contains(ifindex) || foundCDPMp.contains(ifindex) || foundBoksBakSwp.contains(netboxid+":"+ifindex)) {
				//outld("    Skipping port: " + key + " ("+foundBoksBak.contains(key)+","+foundCDPMp.contains(key)+","+foundBoksBakSwp.contains(boksid+":"+key)+")");
				continue;
			}

			if (verifyNetboxid(insertData[1])) {
				try {
					Database.insert("cam", insertData);
					if (DB_COMMIT) Database.commit(); else Database.rollback();
					camNewCnt++;
				} catch (SQLException e) {
					Log.d("RUN_CAM_QUEUE", "SQLException: Cannot update record in cam: " + e.getMessage());
					e.printStackTrace(System.err);
				}
			} else {
				Log.d("VERIFY_NETBOXID", "While insert cam, verify netboxid ("+insertData[1]+") failed");
			}
		}
		camInsertQueue.clear();
	}
	private void safeCloseBoksidAdd(String netboxid) {
		// Nå har vi funnet minst en MAC fra denne enheten, og da sier vi at den er oppe og aktiv,
		// og vi kan lukke CAM-record på den
		synchronized (safeCloseBoksid) {
			if (!safeCloseBoksid.contains(netboxid)) {
				safeCloseBoksid.add(netboxid);
			}
		}
	}

	private void reportWatchMac(String boksid, String ifindex, String mac) {
		String s = 	"The following watched MAC has been found: " + mac + "\n" +
					"\n"+
					"At " + boksIdName.get(boksid) + ", Ifindex: " + ifindex + "\n" +
					"\n"+
					"Please check watchMacs.conf for whom to contact about this particular MAC";

		Log.emergency("REPORT_WATCH_MACS", s);
		System.err.println(s);
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

	/*
	private static void outa(String s) { System.out.print(s); }
	private static void outla(String s) { System.out.println(s); }

	private static void oute(Object s) { if (ERROR_OUT) System.err.print(s); }
	private static void outle(Object s) { if (ERROR_OUT) System.err.println(s); }

	private static void out(String s) { if (VERBOSE_OUT) System.out.print(s); }
	private static void outl(String s) { if (VERBOSE_OUT) System.out.println(s); }

	private static void outd(String s) { if (DBUG_OUT) System.out.print(s); }
	private static void outld(String s) { if (DEBUG_OUT) System.out.println(s); }

	private static void err(Object o) { System.err.print(o); }
	private static void errl(Object o) { System.err.println(o); }
	private static void errflush() { System.err.flush(); }
	*/
}
