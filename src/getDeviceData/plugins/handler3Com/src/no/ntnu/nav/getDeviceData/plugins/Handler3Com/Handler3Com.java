package no.ntnu.nav.getDeviceData.plugins.Handler3Com;

import no.ntnu.nav.SimpleSnmp.*;
import no.ntnu.nav.ConfigParser.*;
import no.ntnu.nav.getDeviceData.plugins.*;
import java.util.*;

public class Handler3Com implements DeviceHandler
{
	private static boolean VERBOSE_OUT = true;
	private static boolean DEBUG_OUT = true;

	private SimpleSnmp sSnmp;

	public int canHandleDevice(BoksData bd)
	{
		return (bd.getTypegruppe() != null &&
				(bd.getTypegruppe().equals("3hub") ||
				bd.getTypegruppe().equals("3ss") ||
				bd.getTypegruppe().equals("3ss9300"))) ? 1 : 0;
	}

	public void handle(BoksData bd, SimpleSnmp sSnmp, ConfigParser cp, DeviceDataList ddList) throws TimeoutException
	{
		String boksid = bd.getBoksid();
		String ip = bd.getIp();
		String cs_ro = bd.getCommunityRo();
		String boksTypegruppe = bd.getTypegruppe();
		String boksType = bd.getType();
		String sysName = bd.getSysname();
		String kat = bd.getKat();
		this.sSnmp = sSnmp;

		// Just to be sure...
		if (canHandleDevice(bd) <= 0) return;

		List moduleDataList = process3Com(boksid, ip, cs_ro, boksTypegruppe, boksType);

		for (Iterator it=moduleDataList.iterator(); it.hasNext();) {
			ModuleData md = (ModuleData)it.next();
			ddList.addModuleData(md);
		}
	}

	/*
	 * 3COM
	 *
	 */
	private ArrayList process3Com(String boksid, String ip, String cs_ro, String typegruppe, String typeid) throws TimeoutException
	{
		ArrayList l = new ArrayList();
		typeid = typeid.toLowerCase();

		/*
		PS40:
		=====
		Kan finne oppe/nede med .1.3.6.1.2.1.26.1.1.1.6.<unit>.<port>.1 = 3|4
		3 = oppe
		4 = nede

		Synes man her skal lage en ifindex av typen
		 unit1port15 har ifindex 115
		speed og duplex: for ps40 har vi jo bare halv duplex, speed 10, forutsatt
		 at porten er oppe.

		SWxx00
		======

		$mib{'3ss'}{mac} = '.1.3.6.1.4.1.43.10.27.1.1.1.2';
		$mib{'3ss'}{model} = '.1.3.6.1.4.1.43.10.27.1.1.1.19';
		$mib{'3ss'}{descr} = '.1.3.6.1.4.1.43.10.27.1.1.1.5';
		$mib{'3ss'}{serial} = '.1.3.6.1.4.1.43.10.27.1.1.1.13';
		$mib{'3ss'}{hw} = '.1.3.6.1.4.1.43.10.27.1.1.1.11';
		$mib{'3ss'}{sw} = '.1.3.6.1.4.1.43.10.27.1.1.1.12';

	IfIndex:
		Tolkes fra ifDescr:
		.1.3.6.1.2.1.2.2.1.2.ifindex = tekststring av litt diverse typer. Må
		plukke ut de som inneholder ordene 'unit' og 'port'. Tungvint, men har
		ikke noe bedre :(

		SW9300: SuperStack II Switch 9300, manuf: 3Com, Gigabit-Ethernet Port 1
		SW3300: RMON:10/100 Port 13 on Unit 4
		SW1100: RMON:V2 Port 1 on Unit 2

	Speed & Duplex
		kan finnes fra ifMauType:
		.1.3.6.1.2.1.26.2.1.1.3.ifindex.1 = oid

		SW9300: N/A
		SW3300: 26.4.16 / enterprises.43.18.8.2.3
		SW1100: 26.4.10

		26.4.3 : FOIRL         10 HD
		26.4.10: 10BaseTHD     10 HD
		26.4.11: 10BaseTFD     10 FD
		26.4.15: 100BaseTXHD  100 HD
		26.4.16: 100BaseTXFD  100 FD
		26.4.17: 100BaseFXHD  100 HD
		26.4.18: 100BaseFXFD  100 FD
		enterprises.43.18.8.2.3: 1000 FD TP
		enterprises.43.18.8.2.7: 1000 FD Fiber SX

	Speed:
		.1.3.6.1.2.1.2.2.1.5

		SW9300: Gauge32: 1000000000

	Up/down:
		.1.3.6.1.2.1.2.2.1.8

		SW9300:
		1 = up
		2 = down

		*/


		if (typeid.equals("off8") || typeid.equals("ps40")) {
			// OID: 1.3.6.1.2.1.26.1.1.1.6.<modul>.<port>.1 = 3|4
			// 3 = oppe
			// 4 = nede
			// IfIndex = <modul><port>
			String speed = "10";
			char duplex = 'h';
			String media = "10Base-T";

			// Hent listen
			String baseOid = "1.3.6.1.2.1.26.1.1.1.6";
			sSnmp.setParams(ip, cs_ro, baseOid);
			ArrayList portList = sSnmp.getAll();

			for (int i=0; i < portList.size(); i++) {
				String[] s = (String[])portList.get(i);
				StringTokenizer st = new StringTokenizer(s[0], ".");
				String modul = st.nextToken();
				String port = st.nextToken();
				try {
					int n = Integer.parseInt(modul);
					if (n > 16) continue;
					n = Integer.parseInt(port);
					if (n > 32) continue;
				} catch (NumberFormatException e) {
					errl("  process3Com(): boksid: " + boksid + " modul: " + modul + " port: " + port + " NumberFormatException on modul|port: " + modul+"|"+port);
					continue;
				}
				String ifindex = modul+port;

				char link = 'n';
				try {
					int n = Integer.parseInt(s[1]);
					if (n == 1 || n == 3) link = 'y';
				} catch (NumberFormatException e) {
					errl("  process3Com(): boksid: " + boksid + " ifindex: " + ifindex + " NumberFormatException on status: " + s[1]);
					continue;
				}

				outl("  Added portData("+boksid+"): ifindex: " + ifindex + " Modul: " + modul + " Port: " + port + " Link: " + link + " Speed: " + speed + " Duplex: " + duplex + " Media: " + media);

				SwportData sd = new SwportData(port, ifindex, link, speed, duplex, media, false, "");
				l.add(sd);
			}
		} else if (typegruppe.equals("3ss9300") || typegruppe.equals("3ss")) {
			// IfIndex: 1.3.6.1.2.1.2.2.1.2.ifindex = tekststring
			String ifIndexOid = "1.3.6.1.2.1.2.2.1.2";
			sSnmp.setParams(ip, cs_ro, ifIndexOid);
			ArrayList modulPortList = sSnmp.getAll(true);
			HashMap modulPortMap = new HashMap();
			for (int i=0; i < modulPortList.size(); i++) {
				String[] s = (String[])modulPortList.get(i);
				String ifindex = s[0];

				// Hent ut modul og port
				String modul;
				String port;
				if (typegruppe.equals("3ss9300")) {
					modul = "1";
				} else {
					modul = getNumAfterWord(s[1], "unit");
					if (modul == null) continue;
				}

				port = getNumAfterWord(s[1], "port");
				if (port == null) continue;

				modulPortMap.put(ifindex, new String[] { modul, port } );
			}

			HashMap mauTypeMap = new HashMap();
			if (typeid.equals("sw3300") || typeid.equals("sw1100")) {
				/*
				kan finnes fra ifMauType:
				.1.3.6.1.2.1.26.2.1.1.3.ifindex.1 = oid

				SW9300: N/A
				SW3300: 26.4.16 / enterprises.43.18.8.2.3
				SW1100: 26.4.10

				26.4.10: 10BaseTHD     10 HD
				26.4.11: 10BaseTFD     10 FD
				26.4.15: 100BaseTXHD  100 HD
				26.4.16: 100BaseTXFD  100 FD
				26.4.17: 100BaseFXHD  100 HD
				26.4.18: 100BaseFXFD  100 FD

			    1.3.6.1.4.1.43.18.8.2.2: 1000 BASE-SX / 1000Mbps FD
			    1.3.6.1.4.1.43.18.8.2.3: 1000 BASE-SX / 1000Mbps FD
			    1.3.6.1.4.1.43.18.8.2.7: 1000 BASE-T / 1000Mbps FD
			    1.3.6.1.4.1.43.18.8.2.9: 1000 BASE-T / 1000Mbps FD
				*/
				String _10BaseT = "10Base-T";
				if (typeid.equals("sw3300")) _10BaseT = "100Base-TX"; // 3300 har bare 100Mbit-porter

				HashMap oidMap = new HashMap();
				String pre = "1.3.6.1.2.1.26.4.";
				oidMap.put(pre+"3", new String[] { "10", "half", "FOIRL" } );
				oidMap.put(pre+"10", new String[] { "10", "half", _10BaseT } );
				oidMap.put(pre+"11", new String[] { "10", "full", _10BaseT } );
				oidMap.put(pre+"15", new String[] { "100", "half", "100Base-TX" } );
				oidMap.put(pre+"16", new String[] { "100", "full", "100Base-TX" } );
				oidMap.put(pre+"17", new String[] { "100", "half", "100Base-FX" } );
				oidMap.put(pre+"18", new String[] { "100", "full", "100Base-FX" } );
				pre = "1.3.6.1.4.1.43.18.8.2.";
				oidMap.put(pre+"2", new String[] { "1000", "full", "1000Base-SX" } );
				oidMap.put(pre+"3", new String[] { "1000", "full", "1000Base-SX" } );
				oidMap.put(pre+"7", new String[] { "1000", "full", "1000Base-T" } );
				oidMap.put(pre+"9", new String[] { "1000", "full", "1000Base-T" } );

				String mauOid = "1.3.6.1.2.1.26.2.1.1.3";
				sSnmp.setParams(ip, cs_ro, mauOid);
				ArrayList mauTypeList = sSnmp.getAll(false);

				for (int i=0; i < mauTypeList.size(); i++) {
					String[] s = (String[])mauTypeList.get(i);
					StringTokenizer st = new StringTokenizer(s[0], ".");
					String ifindex = st.nextToken();
					String oid = s[1];
					if (oidMap.containsKey(oid)) {
						mauTypeMap.put(ifindex, oidMap.get(oid));
					} else {
						errl("  process3Com: boksid: " + boksid + " ifindex: " + ifindex + " Unknown mauOid: " + oid);
					}
				}
			} else if (typegruppe.equals("3ss9300")) {
				// .1.3.6.1.2.1.2.2.1.5
				// SW9300: Gauge32: 1000000000
				String speedOid = "1.3.6.1.2.1.2.2.1.5";
				sSnmp.setParams(ip, cs_ro, speedOid);
				ArrayList speedList = sSnmp.getAll();

				for (int i=0; i < speedList.size(); i++) {
					String[] s = (String[])speedList.get(i);
					String ifindex = s[0];
					long speedNum;
					try {
						speedNum = Long.parseLong(s[1]);
					} catch (NumberFormatException e) {
						errl("  process3Com: boksid: " + boksid + " ifindex: " + ifindex + " NumberFormatException on speed: " + s[1]);
						continue;
					}
					String speed = String.valueOf( (speedNum/1000000) );
					String duplex = "full";
					String media = "1000Base-SX";
					mauTypeMap.put(ifindex, new String[] { speed, duplex, media } );
				}
			}

			// Så sjekker vi status for porten, up|down
			HashMap linkMap = new HashMap();
			{
				String linkOid = "1.3.6.1.2.1.2.2.1.8";
				sSnmp.setParams(ip, cs_ro, linkOid);
				ArrayList linkList = sSnmp.getAll();

				for (int i=0; i < linkList.size(); i++) {
					String[] s = (String[])linkList.get(i);
					String ifindex = s[0];
					String link;
					try {
						int n = Integer.parseInt(s[1]);
						if (n == 1) {
							link = "yes"; // up
						} else if (n == 2) {
							link = "no"; // down
						} else if (n == 0) {
							// FIXME
							link = "no"; // down
						} else {
							errl("  process3Com: boksid: " + boksid + " ifindex: " + ifindex + " Unknown link code: " + n);
							continue;
						}
					} catch (NumberFormatException e) {
						errl("  process3Com: boksid: " + boksid + " ifindex: " + ifindex + " NumberFormatException for link code: " + s[1]);
						continue;
					}
					linkMap.put(ifindex, link);
				}
			}



			Iterator iter = modulPortMap.entrySet().iterator();
			while (iter.hasNext()) {
				Map.Entry me = (Map.Entry)iter.next();
				String ifindex = (String)me.getKey();
				String[] modulPort = (String[])me.getValue();
				String modul = modulPort[0];
				String port = modulPort[1];

				String[] mau = (String[])mauTypeMap.get(ifindex);
				if (mau == null) {
					errl("  process3Com: boksid: " + boksid + " ifindex: " + ifindex + " Could not find mauType for ifindex");
					continue;
				}


				if (!linkMap.containsKey(ifindex)) {
					errl("  process3Com: boksid: " + boksid + " ifindex: " + ifindex + " Could not find status for ifindex");
					continue;
				}
				char link = ((String)linkMap.get(ifindex)).charAt(0);

				String speed = mau[0];
				char duplex = mau[1].charAt(0);
				String media = mau[2];

				outl("  Added portData("+boksid+"): ifindex: " + ifindex + " Modul: " + modul + " Port: " + port + " Link: " + link + " Speed: " + speed + " Duplex: " + duplex + " Media: " + media);

				SwportData sd = new SwportData(port, ifindex, link, speed, duplex, media, false, "");
				l.add(sd);
			}

		} else {
			errl("  process3Com: boksid: " + boksid + " Unsupported typegruppe: " + typegruppe + " typeid: " + typeid);
			return l;
		}

		return l;
	}

	private static String getNumAfterWord(String s, String word) {
		s = s.toLowerCase();
		int i=0;
		while ( (i=s.indexOf(word, i)) >= 0) {
			int begin = s.indexOf(' ', i);
			if (begin < 0) return null;
			String t = s.substring(begin, s.length()).trim();

			int end = t.indexOf(' ');
			if (end >= 0) t = t.substring(0, end);

			try {
				int n = Integer.parseInt(t);
				return String.valueOf(n);
			} catch (NumberFormatException e) {
			}
		}

		return null;
	}

	private static void outa(String s) { System.out.print(s); }
	private static void outla(String s) { System.out.println(s); }

	private static void out(String s) { if (VERBOSE_OUT) System.out.print(s); }
	private static void outl(String s) { if (VERBOSE_OUT) System.out.println(s); }

	private static void outd(String s) { if (DEBUG_OUT) System.out.print(s); }
	private static void outld(String s) { if (DEBUG_OUT) System.out.println(s); }

	private static void err(Object o) { System.err.print(o); }
	private static void errl(Object o) { System.err.println(o); }
	private static void errflush() { System.err.flush(); }

}