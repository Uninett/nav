package no.ntnu.nav.getDeviceData.deviceplugins._3Com;

import java.util.*;
import java.util.regex.*;

import no.ntnu.nav.logger.*;
import no.ntnu.nav.SimpleSnmp.*;
import no.ntnu.nav.ConfigParser.*;
import no.ntnu.nav.getDeviceData.Netbox;
import no.ntnu.nav.getDeviceData.deviceplugins.*;
import no.ntnu.nav.getDeviceData.dataplugins.*;
import no.ntnu.nav.getDeviceData.dataplugins.Module.*;
import no.ntnu.nav.getDeviceData.dataplugins.Swport.*;

/**
 * <p>
 * DeviceHandler for collecting switch port data from 3Com switches.
 * </p>
 *
 * <p>
 * This plugin handles the following OID keys:
 * </p>
 *
 * <p>
 * <ui>
 *  <li>3cIfDescr</li>
 *  <li>3cPS40PortState</li>
 *  <li>3cIfMauType</li>
 *  <li>3cSerial</li>
 *  <li>3cHwVer</li>
 *  <li>3cSwVer</li>
 * </ul>
 * </p>
 *
 */

public class _3Com implements DeviceHandler
{
	private static String[] canHandleOids = {
		"3cIfDescr",
		"3cPS40PortState",
		"3cIfMauType",
		"3cSerial",
		"3cHwVer",
		"3cSwVer"
	};

	private SimpleSnmp sSnmp;

	public int canHandleDevice(Netbox nb) {
		int v = nb.isSupportedOids(canHandleOids) ? ALWAYS_HANDLE : NEVER_HANDLE;
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
		String type = nb.getType();
		String sysName = nb.getSysname();
		String cat = nb.getCat();
		this.sSnmp = sSnmp;

		process3Com(nb, netboxid, ip, cs_ro, type, sc);

		// Commit data
		sc.commit();
	}


	/*
	 * 3COM
	 *
	 */
	private void process3Com(Netbox nb, String netboxid, String ip, String cs_ro, String type, SwportContainer sc) throws TimeoutException {
		type = type.toLowerCase();

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

		if (type.equals("off8") || type.equals("ps40")) {
			// OID: 1.3.6.1.2.1.26.1.1.1.6.<modul>.<port>.1 = 3|4
			// 3 = oppe
			// 4 = nede
			// IfIndex = <modul><port>
			String speed = "10";
			String duplex = "half";
			String media = "10Base-T";

			// Hent listen
			List portList = sSnmp.getAll(nb.getOid("3cPS40PortState"));
			if (portList != null) {
				for (Iterator it = portList.iterator(); it.hasNext();) {
					String[] s = (String[])it.next();
					String portState = s[1];
					s = s[0].split(".");
					String module = s[0];
					String ifindex = module+s[1];

					Integer port;
					try {
						port = new Integer(s[1]);
						if (port.intValue() > 32) continue;
					} catch (NumberFormatException exp) {
						Log.w("PROCESS_3COM", "NumberFormatException when converting port " + s[1] + " to number, netbox: " + netboxid + ", " + exp);
						continue;
					}

					try {
						int n = Integer.parseInt(module);
						if (n > 16) continue;
					} catch (NumberFormatException exp) {
						Log.d("PROCESS_3COM", "NumberFormatException when converting module " + module + " to number, netbox: " + netboxid + ", " + exp);
						continue;
					}

					char link = 'n';
					try {
						int n = Integer.parseInt(portState);
						if (n == 1 || n == 3) link = 'y';						
					} catch (NumberFormatException e) {
						Log.w("PROCESS_3COM", "NumberFormatException on link: " + portState + ", netboxid: " + netboxid + " ifindex: " + ifindex);
						continue;
					}

					SwModule m = sc.swModuleFactory(module);
					Swport swp = m.swportFactory(ifindex);

					swp.setPort(port);
					swp.setLink(link);
					swp.setSpeed(speed);
					swp.setDuplex(duplex.charAt(0));
					swp.setMedia(media);

					Log.d("PROCESS_3COM", "Added port, netbox: "+ netboxid +", " + swp);
				}				
			}
			return;
		}

		List l;

		// Module data
		l = sSnmp.getAll(nb.getOid("3cSerial"), true, false);
		if (l != null) {
			for (Iterator it = l.iterator(); it.hasNext();) {
				String[] s = (String[])it.next();
				sc.swModuleFactory(s[0]).setSerial(s[1]);
				Log.d("PROCESS_3COM", "Module: " + s[0] + " Serial: " + s[1]);
			}
		}

		l = sSnmp.getAll(nb.getOid("3cHwVer"), true, false);
		if (l != null) {
			for (Iterator it = l.iterator(); it.hasNext();) {
				String[] s = (String[])it.next();
				sc.swModuleFactory(s[0]).setHwVer(s[1]);
			}
		}

		l = sSnmp.getAll(nb.getOid("3cSwVer"), true, false);
		if (l != null) {
			for (Iterator it = l.iterator(); it.hasNext();) {
				String[] s = (String[])it.next();
				sc.swModuleFactory(s[0]).setSwVer(s[1]);
			}
		}

		// Fetch ifDescr
		List ifDescrList = sSnmp.getAll(nb.getOid("3cIfDescr"), true, true);
		if (ifDescrList != null) {
			for (Iterator it = ifDescrList.iterator(); it.hasNext();) {
				String[] s = (String[])it.next();
				String ifindex = s[0];
				String ifdescr = s[1];

				// Use regex for extracting unit and port
				Matcher m = Pattern.compile("Port (\\d+)\\b").matcher(ifdescr);
				if (!m.find()) continue;
				String port = m.group(1);

				String module = "1";
				m = Pattern.compile("Unit (\\d+)\\b").matcher(ifdescr);
				if (m.find()) module = m.group(1);

				SwModule swm = sc.swModuleFactory(module);
				Swport swp = swm.swportFactory(ifindex);
				swp.setPort(new Integer(port));

				// Special case for 3Com 9300 which only has FD gigabit ports
				if (type.equals("sw9300")) {
					swp.setDuplex('f');
					swp.setMedia("1000Base-SX");
				}
			}
		}

		// Fetch mauType
		List mauTypeList = sSnmp.getAll(nb.getOid("3cIfMauType"));
		if (mauTypeList != null) {
			String _10BaseT = "10Base-T";
			if (type.equals("sw3300")) _10BaseT = "100Base-TX"; // 3300 har bare 100Mbit-porter
			
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
			
			for (Iterator it = mauTypeList.iterator(); it.hasNext();) {
				String[] s = (String[])it.next();
				String ifindex = s[0].split("\\.")[0];
				String mauTypeOid = s[1];

				if (oidMap.containsKey(mauTypeOid)) {
					s = (String[])oidMap.get(mauTypeOid);
					Swport swp = sc.swportFactory(ifindex);
					swp.setDuplex(s[1].charAt(0));
					swp.setMedia(s[2]);
				} else {
					Log.w("PROCESS_3COM", "Unknown mauTypeOid: " + mauTypeOid + ", netboxid: " + netboxid + " ifindex: " + ifindex);
				}
			}
		}

	}

}
