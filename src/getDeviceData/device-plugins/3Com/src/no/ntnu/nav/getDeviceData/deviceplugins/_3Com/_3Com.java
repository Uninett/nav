package no.ntnu.nav.getDeviceData.deviceplugins._3Com;

import java.util.*;

import no.ntnu.nav.logger.*;
import no.ntnu.nav.SimpleSnmp.*;
import no.ntnu.nav.ConfigParser.*;
import no.ntnu.nav.getDeviceData.Netbox;
import no.ntnu.nav.getDeviceData.deviceplugins.*;
import no.ntnu.nav.getDeviceData.dataplugins.*;
import no.ntnu.nav.getDeviceData.dataplugins.Module.*;
import no.ntnu.nav.getDeviceData.dataplugins.Swport.*;

/**
 * DeviceHandler for collecting switch port data from 3Com switches.
 */

public class _3Com implements DeviceHandler
{
	private static boolean VERBOSE_OUT = false;

	private SimpleSnmp sSnmp;

	public int canHandleDevice(Netbox nb) {
		int v = nb.getTypegroup() != null && 
			(nb.getTypegroup().equals("3hub") ||
			 nb.getTypegroup().equals("3ss") ||
			 nb.getTypegroup().equals("3ss9300")) ? ALWAYS_HANDLE : NEVER_HANDLE;	
		Log.d("3COM_CANHANDLE", "CHECK_CAN_HANDLE", "Can handle device: " + v);
		return v;
	}

	public void handleDevice(Netbox nb, SimpleSnmp sSnmp, ConfigParser cp, DataContainers containers) throws TimeoutException
	{
		Log.setDefaultSubsystem("3COM_DEVHANDLER");
		
		SwportContainer sc;
		{
			DataContainer dc = containers.getContainer("SwportContainer");
			if (dc == null) {
				Log.w("NO_CONTAINER", "No SwportContainer found, plugin may not be loaded");
				return;
			}
			if (!(dc instanceof SwportContainer)) {
				Log.w("NO_CONTAINER", "Container is not an SwportContainer! " + dc);
				return;
			}
			sc = (SwportContainer)dc;
		}

		String netboxid = nb.getNetboxidS();
		String ip = nb.getIp();
		String cs_ro = nb.getCommunityRo();
		String typegroup = nb.getTypegroup();
		String type = nb.getType();
		String sysName = nb.getSysname();
		String cat = nb.getCat();
		this.sSnmp = sSnmp;

		// Just to be sure...
		if (canHandleDevice(nb) <= 0) return;

		process3Com(netboxid, ip, cs_ro, typegroup, type, sc);

		// Commit data
		sc.commit();
	}


	/*
	 * 3COM
	 *
	 */
	private void process3Com(String netboxid, String ip, String cs_ro, String typegroup, String typeid, SwportContainer sc) throws TimeoutException
	{
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

# typegroup 3ss
    $mib{'3ss'}{mac} = '.1.3.6.1.4.1.43.10.27.1.1.1.2';
    $mib{'3ss'}{model} = '.1.3.6.1.4.1.43.10.27.1.1.1.19';
    $mib{'3ss'}{descr} = '.1.3.6.1.4.1.43.10.27.1.1.1.5';
    $mib{'3ss'}{serial} = '.1.3.6.1.4.1.43.10.27.1.1.1.13';
    $mib{'3ss'}{hw} = '.1.3.6.1.4.1.43.10.27.1.1.1.11';
    $mib{'3ss'}{sw} = '.1.3.6.1.4.1.43.10.27.1.1.1.12';


		*/


		if (typeid.equals("off8") || typeid.equals("ps40")) {
			// OID: 1.3.6.1.2.1.26.1.1.1.6.<modul>.<port>.1 = 3|4
			// 3 = oppe
			// 4 = nede
			// IfIndex = <modul><port>
			String speed = "10";
			String duplex = "half";
			String media = "10Base-T";

			// Hent listen
			String baseOid = "1.3.6.1.2.1.26.1.1.1.6";
			sSnmp.setParams(ip, cs_ro, baseOid);
			ArrayList portList = sSnmp.getAll();

			Map moduleMap = new HashMap();
			for (int i=0; i < portList.size(); i++) {
				String[] s = (String[])portList.get(i);
				StringTokenizer st = new StringTokenizer(s[0], ".");
				String modul = st.nextToken();
				Integer port;

				String portS = st.nextToken();
				try {
					port = new Integer(portS);
				} catch (NumberFormatException exp) {
					Log.w("PROCESS_3COM", "NumberFormatException when converting port " + portS + " to number, netbox: " + netboxid + ", " + exp);
					continue;
				}

				try {
					int n = Integer.parseInt(modul);
					if (n > 16) continue;
					n = port.intValue();
					if (n > 32) continue;
				} catch (NumberFormatException exp) {
					Log.d("PROCESS_3COM", "NumberFormatException when converting module " + modul + " to number, netbox: " + netboxid + ", " + exp);
					continue;
				}

				String ifindex = modul+port;

				char link = 'n';
				try {
					int n = Integer.parseInt(s[1]);
					if (n == 1 || n == 3) link = 'y';

				} catch (NumberFormatException e) {
					Log.w("PROCESS_3COM", "NumberFormatException on link: " + s[1] + ", netboxid: " + netboxid + " ifindex: " + ifindex);
					continue;
				}

				Log.d("PROCESS_3COM", "Added port, netbox: "+ netboxid +" ifindex: " + ifindex + " Modul: " + modul + " Port: " + port + " Link: " + link + " Speed: " + speed + " Duplex: " + duplex + " Media: " + media);

				String serial = "";
				String hw_ver = "";
				String sw_ver = "";

				// Create module
				SwModule m = (SwModule)moduleMap.get(modul);
				if (m == null) {
					m = sc.swModuleFactory(serial, hw_ver, sw_ver, modul);
					moduleMap.put(modul, m);
				}

				// Create swport
				Swport sw = m.swportFactory(port, ifindex, link, speed, duplex.charAt(0), media, false, "");
				
			}
		} else if (typegroup.equals("3ss9300") || typegroup.equals("3ss")) {
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
				if (typegroup.equals("3ss9300")) {
					modul = "1";
				} else {
					modul = getNumAfterWord(s[1], "unit");
					if (modul == null) continue;
				}

				String portS = getNumAfterWord(s[1], "port");
				if (portS == null) continue;

				Integer port;
				try {
					port = new Integer(portS);
				} catch (NumberFormatException exp) {
					Log.w("PROCESS_3COM", "NumberFormatException when coverting port " + portS + " to number: " + exp);
					continue;
				}

				modulPortMap.put(ifindex, new Object[] { modul, port } );
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
						Log.w("PROCESS_3COM", "Unknown mauOid: " + oid + ", netboxid: " + netboxid + " ifindex: " + ifindex);
					}
				}
			} else if (typegroup.equals("3ss9300")) {
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
						Log.w("PROCESS_3COM", "NumberFormatException on speed: " + s[1] + ", netboxid: " + netboxid + " ifindex: " + ifindex);
						continue;
					}
					String speed = String.valueOf( (speedNum/1000000) );
					String duplex = "full";
					String media = "1000Base-SX";
					mauTypeMap.put(ifindex, new String[] { speed, duplex, media } );
				}
			}

			// Så sjekker vi status for porten, up|down
			HashMap statusMap = new HashMap();
			{
				String statusOid = "1.3.6.1.2.1.2.2.1.8";
				sSnmp.setParams(ip, cs_ro, statusOid);
				ArrayList statusList = sSnmp.getAll();

				for (int i=0; i < statusList.size(); i++) {
					String[] s = (String[])statusList.get(i);
					String ifindex = s[0];
					String status;
					try {
						int n = Integer.parseInt(s[1]);
						if (n == 1) {
							status = "y";
						} else if (n == 2) {
							status = "n";
						} else if (n == 0) {
							// FIXME
							status = "n";
						} else {
							Log.w("PROCESS_3COM", "Unknown status code: " + n + ", netboxid: " + netboxid + " ifindex: " + ifindex);
							continue;
						}
					} catch (NumberFormatException e) {
						Log.w("PROCESS_3COM", "NumberFormatException for status code: " + s[1] + ", netboxid: " + netboxid + " ifindex: " + ifindex);
						continue;
					}
					statusMap.put(ifindex, status);
				}
			}


			Map moduleMap = new HashMap();

			Iterator iter = modulPortMap.entrySet().iterator();
			while (iter.hasNext()) {
				Map.Entry me = (Map.Entry)iter.next();
				String ifindex = (String)me.getKey();
				Object[] modulPort = (Object[])me.getValue();
				String modul = (String)modulPort[0];
				Integer port = (Integer)modulPort[1];

				String[] mau = (String[])mauTypeMap.get(ifindex);
				if (mau == null) {
					Log.w("PROCESS_3COM", "Could not find mauType for ifindex, netboxid: " + netboxid + " ifindex: " + ifindex);
					continue;
				}

				String status = (String)statusMap.get(ifindex);
				if (status == null) {
					Log.w("PROCESS_3COM", "Could not find status for ifindex, netboxid: " + netboxid + " ifindex: " + ifindex);
					continue;
				}

				String speed = mau[0];
				String duplex = mau[1];
				String media = mau[2];

				Log.d("PROCESS_3COM", "Added port, netboxid: " + netboxid + " ifindex: " + ifindex + " Modul: " + modul + " Port: " + port + " Status: " + status + " Speed: " + speed + " Duplex: " + duplex + " Media: " + media);

				String serial = "";
				String hw_ver = "";
				String sw_ver = "";

				// Create module
				SwModule m = (SwModule)moduleMap.get(modul);
				if (m == null) {
					m = sc.swModuleFactory(serial, hw_ver, sw_ver, modul);
					moduleMap.put(modul, m);
				}

				// Create swport
				Swport sw = m.swportFactory(port, ifindex, status.charAt(0), speed, duplex.charAt(0), media, false, "");

			}


		} else {
			Log.w("PROCESS_3COM", "Unsupported typegroup: " + typegroup + " typeid: " + typeid + " netboxid: " + netboxid);
			return;
		}

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

}
