package no.ntnu.nav.getDeviceData.deviceplugins.CiscoSwMenu;

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
 * <p>
 * DeviceHandler for collecting switch port data from C3xxx switches.
 * </p>
 *
 * <p>
 * This plugin handles the following OID keys:
 * </p>
 *
 * <p>
 * <ui>
 *  <li>cMenuIfIndex</li>
 *  <li>cMenuPortStatus</li>
 *  <li>cMenuPortType</li>
 *  <li>cMenuDuplex</li>
 *  <li>cMenuTrunk</li>
 *  <li>cMenuVlan</li>
 * </ul>
 * </p>
 *
 */

public class CiscoSwMenu implements DeviceHandler
{
	private static String[] canHandleOids = {
		"cMenuIfIndex",
		"cMenuPortStatus",
		"cMenuPortType",
		"cMenuDuplex",
		"cMenuTrunk",
		"cMenuVlan"
	};

	private SimpleSnmp sSnmp;

	public int canHandleDevice(Netbox nb) {
		int v = nb.isSupportedOids(canHandleOids) ? ALWAYS_HANDLE : NEVER_HANDLE;
		Log.d("C_MENU_CANHANDLE", "CHECK_CAN_HANDLE", "Can handle device: " + v);
		return v;
	}

	public void handleDevice(Netbox nb, SimpleSnmp sSnmp, ConfigParser cp, DataContainers containers) throws TimeoutException
	{
		Log.setDefaultSubsystem("C_MENU_DEVHANDLER");
		
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

		processCMenu(nb, netboxid, ip, cs_ro, type, sc);

		// Commit data
		sc.commit();
	}

	/*
	 * C30xx, C31xx
	 *
	 */
	private void processCMenu(Netbox nb, String netboxid, String ip, String cs_ro, String type, SwportContainer sc) throws TimeoutException {
		/*
		Støtter C3000/C3100

	ifindex:
		1.3.6.1.4.1.9.5.14.4.1.1.4 = ifindex
		port = ifindex

	Status:
		1.3.6.1.4.1.9.5.14.4.1.1.29 = status

		1 = up
		2/other = down

	Speed & Media:
		1.3.6.1.4.1.9.5.14.4.1.1.41 = value

		speed = 10 if value in [1,5,6,7]
		speed = 100 if value in [3,4,10,11,12,13]

		value=1  => media = 10BaseT
		value=3  => media = 100BaseT
		value=4  => media = 100BaseFX
		value=7  => media = 10BaseFL
		value=12 => media = ISL FX
		value=13 => media = ISL TX

	Duplex:
		1.3.6.1.4.1.9.5.14.4.1.1.5 = duplex

		1 = full
		2 = half

	Trunk:
		1.3.6.1.4.1.9.5.14.4.1.1.44 = value

		trunking if value = 1
		non-trunking if value = 2

		*/

		// Module is always 1 on this switch
		int module = 1;
		List l;

		// Switch port data
		l = sSnmp.getAll(nb.getOid("cMenuIfIndex"));
		if (l != null) {
			for (Iterator it = l.iterator(); it.hasNext();) {
				String[] s = (String[])it.next();
				String[] s2 = s[0].split("\\.");
				String ifindex = s2[s2.length-1];

				SwModule m = sc.swModuleFactory(module);
				m.swportFactory(ifindex).setPort(new Integer(s[1]));
			}
		}

		l = sSnmp.getAll(nb.getOid("cMenuPortStatus"));
		if (l != null) {
			for (Iterator it = l.iterator(); it.hasNext();) {
				String[] s = (String[])it.next();
				String[] s2 = s[0].split("\\.");
				String ifindex = s2[s2.length-1];
				char link = (s[1].equals("1") ? 'y' : 'n');

				SwModule m = sc.swModuleFactory(module);
				m.swportFactory(ifindex).setLink(link);
			}
		}

		l = sSnmp.getAll(nb.getOid("cMenuPortType"));
		if (l != null) {
			for (Iterator it = l.iterator(); it.hasNext();) {
				String[] s = (String[])it.next();
				String[] s2 = s[0].split("\\.");
				String ifindex = s2[s2.length-1];

				String speed = "-1";
				if (s[1].equals("1") || s[1].equals("5") || s[1].equals("6") || s[1].equals("7")) {
					speed = "10";
				}
				else if (s[1].equals("3") || s[1].equals("4") || s[1].equals("10") || s[1].equals("11") || s[1].equals("12") || s[1].equals("13")) {
					speed = "100";
				}
				
				String media = "Unknown";
				if (s[1].equals("1")) media = "10Base-T";
				if (s[1].equals("3")) media = "100Base-T";
				if (s[1].equals("4")) media = "100Base-FX";
				if (s[1].equals("7")) media = "10Base-FL";
				if (s[1].equals("12")) media = "ISL FX";
				if (s[1].equals("13")) media = "ISL TX";
				
				SwModule m = sc.swModuleFactory(module);
				Swport swp = m.swportFactory(ifindex);
				swp.setSpeed(speed);
				swp.setMedia(media);

			}
		}

		l = sSnmp.getAll(nb.getOid("cMenuDuplex"));
		if (l != null) {
			for (Iterator it = l.iterator(); it.hasNext();) {
				String[] s = (String[])it.next();
				String[] s2 = s[0].split("\\.");
				String ifindex = s2[s2.length-1];
				char duplex = (s[1].equals("1") ? 'f' : 'h');

				SwModule m = sc.swModuleFactory(module);
				m.swportFactory(ifindex).setDuplex(duplex);
			}
		}

		l = sSnmp.getAll(nb.getOid("cMenuTrunk"));
		if (l != null) {
			for (Iterator it = l.iterator(); it.hasNext();) {
				String[] s = (String[])it.next();
				String[] s2 = s[0].split("\\.");
				String ifindex = s2[s2.length-1];
				boolean trunk = s[1].equals("1");

				SwModule m = sc.swModuleFactory(module);
				m.swportFactory(ifindex).setTrunk(trunk);
			}
		}

		l = sSnmp.getAll(nb.getOid("cMenuVlan"));
		if (l != null) {
			for (Iterator it = l.iterator(); it.hasNext();) {
				String[] s = (String[])it.next();
				String vlan = new StringTokenizer(s[0],".").nextToken();

				s[1] = removeString(s[1], ":");
				List portVlanList = getPortVlan(s[1]);
				for (Iterator vlIt = portVlanList.iterator(); vlIt.hasNext();) {
					String ifindex = (String)vlIt.next();
					Swport swp = sc.swportFactory(ifindex);

					if (swp.getTrunk().booleanValue()) {
						swp.addTrunkVlan(vlan);
					} else {
						swp.setVlan(Integer.parseInt(vlan));
					}
				}
			}
		}
	}

	// Vi får inn en hexstreng, f.eks: FF 0E 8A 00 Teller man fra
	// venstre vil hver bit angi om vlanet kjører på porten Funksjonen
	// legger altså bare til posisjonen til alle bit'ene som er 1 til en
	// liste.
	private static List getPortVlan(String s) {
		List l = new ArrayList();

		for (int i=0; i < s.length(); i++) {
			int c = Integer.parseInt(String.valueOf(s.charAt(i)), 16);
			// En char er 4 bits, da det er hex det er snakk om
			for (int j=0;j<4;j++) if ( ((c>>(3-j))&1) != 0) l.add(String.valueOf(i*4+j+1));
		}

		return l;
	}

	private static String removeString(String s, String rem) {
		StringBuffer sb = new StringBuffer();
		StringTokenizer st = new StringTokenizer(s, rem);
		while (st.hasMoreTokens()) sb.append(st.nextToken());
		return sb.toString();
	}

}
