package no.ntnu.nav.getDeviceData.deviceplugins.CiscoSwBasic;

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
 * DeviceHandler for collecting switch port data from C3xxx and C19xx switches.
 */

public class CiscoSwBasic implements DeviceHandler
{
	private static boolean VERBOSE_OUT = true;
	private static boolean DEBUG_OUT = true;

	private SimpleSnmp sSnmp;

	public int canHandleDevice(Netbox nb) {
		int v = nb.getTypegroup() != null && (nb.getTypegroup().equals("cat1900-sw") || nb.getTypegroup().equals("catmeny-sw"))
			? ALWAYS_HANDLE : NEVER_HANDLE;
		Log.d("CSWBASIC_CANHANDLE", "CHECK_CAN_HANDLE", "Can handle device: " + v);
		return v;
	}

	public void handleDevice(Netbox nb, SimpleSnmp sSnmp, ConfigParser cp, DataContainers containers) throws TimeoutException
	{
		Log.setDefaultSubsystem("CSWBASIC_DEVHANDLER");
		
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

		// Vi trenger ifindexMp kobling
		HashMap ifindexMp = fetchIfindexMpMap(ip, cs_ro, typegroup);

		if (typegroup.equals("cat1900-sw")) {
			processCisco1900(netboxid, ip, cs_ro, typegroup, type, sc);
		} else
		if (typegroup.equals("catmeny-sw")) {
			processCisco1Q(netboxid, ip, cs_ro, typegroup, type, sc);
		}

		// Commit data
		sc.commit();
	}

	/*
	 * Cisco 1900
	 *
	 */
	private void processCisco1900(String netboxid, String ip, String cs_ro, String typegroup, String typeid, SwportContainer sc) throws TimeoutException
	{
		// Modul er alltid 1 på denne typen enhet
		String serial = "";
		String hw_ver = "";
		String sw_ver = "";
		String module = "1";

		SwModule m = sc.swModuleFactory(serial, hw_ver, sw_ver, module);

		/*
		Alle C1900*

	ifindex:
		1.3.6.1.2.1.2.2.1.1 = ifindex
		port = ifindex

	Status:
		1.3.6.1.2.1.2.2.1.8 = status

		1 = up
		2/other = down

	Speed:
		1.3.6.1.2.1.2.2.1.5 = speed

		speed is in bits/sec

	Duplex:
		1.3.6.1.4.1.437.1.1.3.3.1.1.8 = duplex

		1 = full
		2 = half

	Portnavn:
		1.3.6.1.4.1.437.1.1.3.3.1.1.3 = portnavn

		FIXME: Mangler info om media. Bruker vlan=1 på alle porter

		*/

		String ifindexOid = "1.3.6.1.2.1.2.2.1.1";
		String statusOid = "1.3.6.1.2.1.2.2.1.8";
		String speedOid = "1.3.6.1.2.1.2.2.1.5";
		String duplexOid = "1.3.6.1.4.1.437.1.1.3.3.1.1.8";
		String portnavnOid = "1.3.6.1.4.1.437.1.1.3.3.1.1.3";

		// Start med å hente alle ifindex/porter
		sSnmp.setParams(ip, cs_ro, ifindexOid);
		ArrayList portList = sSnmp.getAll();

		HashMap portMap = new HashMap();
		for (int i=0; i < portList.size(); i++) {
			String[] s = (String[])portList.get(i);

			String ifindex = getLastToken(s[0]);
			Integer port = new Integer(s[1]);
			
			Swport sw = m.swportFactory(port, ifindex);
			portMap.put(ifindex, sw);
		}

		// Hent status
		sSnmp.setParams(ip, cs_ro, statusOid);
		portList = sSnmp.getAll();
		for (int i=0; i < portList.size(); i++) {
			String[] s = (String[])portList.get(i);
			String ifindex = getLastToken(s[0]);
			Swport sw = (Swport)portMap.get(ifindex);

			char link = (s[1].equals("1") ? 'y' : 'n');
			sw.setLink(link);
		}

		// Hent speed&media
		sSnmp.setParams(ip, cs_ro, speedOid);
		portList = sSnmp.getAll();
		for (int i=0; i < portList.size(); i++) {
			String[] s = (String[])portList.get(i);
			String ifindex = getLastToken(s[0]);
			Swport sw = (Swport)portMap.get(ifindex);

			long speed = Long.parseLong(s[1]);
			speed /= 1000000; // Speed is in Mbit/sec

			sw.setSpeed(String.valueOf(speed));
		}

		// Hent duplex
		sSnmp.setParams(ip, cs_ro, duplexOid);
		portList = sSnmp.getAll();
		for (int i=0; i < portList.size(); i++) {
			String[] s = (String[])portList.get(i);
			String ifindex = getLastToken(s[0]);
			Swport sw = (Swport)portMap.get(ifindex);

			char duplex = (s[1].equals("1") ? 'f' : 'h');
			sw.setDuplex(duplex);
		}

		// Hent portnavn
		sSnmp.setParams(ip, cs_ro, portnavnOid);
		portList = sSnmp.getAll(true);
		for (int i=0; i < portList.size(); i++) {
			String[] s = (String[])portList.get(i);
			String ifindex = getLastToken(s[0]);
			Swport sw = (Swport)portMap.get(ifindex);

			sw.setPortname(s[1].trim());
		}

	}

	private void processCisco1Q(String netboxid, String ip, String cs_ro, String typegroup, String typeid, SwportContainer sc) throws TimeoutException
	{
		// Modul er alltid 1 på denne typen enhet
		String serial = "";
		String hw_ver = "";
		String sw_ver = "";
		String module = "1";

		SwModule m = sc.swModuleFactory(serial, hw_ver, sw_ver, module);

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
		String ifindexOid = "1.3.6.1.4.1.9.5.14.4.1.1.4";
		String statusOid = "1.3.6.1.4.1.9.5.14.4.1.1.29";
		String speedOid = "1.3.6.1.4.1.9.5.14.4.1.1.41";
		String duplexOid = "1.3.6.1.4.1.9.5.14.4.1.1.5";
		String trunkOid = "1.3.6.1.4.1.9.5.14.4.1.1.44";
		String vlanOid = "1.3.6.1.4.1.9.5.14.8.1.1.3";

		// Start med å hente alle ifindex/porter
		sSnmp.setParams(ip, cs_ro, ifindexOid);
		ArrayList portList = sSnmp.getAll();

		HashMap portMap = new HashMap();
		for (int i=0; i < portList.size(); i++) {
			String[] s = (String[])portList.get(i);

			String ifindex = getLastToken(s[0]);
			Integer port = new Integer(s[1]);
			
			Swport sw = m.swportFactory(port, ifindex);
			portMap.put(ifindex, sw);
		}

		// Hent status
		sSnmp.setParams(ip, cs_ro, statusOid);
		portList = sSnmp.getAll();
		for (int i=0; i < portList.size(); i++) {
			String[] s = (String[])portList.get(i);
			String ifindex = getLastToken(s[0]);
			Swport sw = (Swport)portMap.get(ifindex);

			char link = (s[1].equals("1") ? 'y' : 'n');
			sw.setLink(link);
		}

		// Hent speed&media
		sSnmp.setParams(ip, cs_ro, speedOid);
		portList = sSnmp.getAll();
		for (int i=0; i < portList.size(); i++) {
			String[] s = (String[])portList.get(i);
			String ifindex = getLastToken(s[0]);
			Swport sw = (Swport)portMap.get(ifindex);

			String speed = "-1";
			if (s[1].equals("1") || s[1].equals("5") || s[1].equals("6") || s[1].equals("7")) {
				speed = "10";
			} else
			if (s[1].equals("3") || s[1].equals("4") || s[1].equals("10") || s[1].equals("11") || s[1].equals("12") || s[1].equals("13")) {
				speed = "100";
			}

			String media = "Unknown";
			if (s[1].equals("1")) media = "10Base-T";
			if (s[1].equals("3")) media = "100Base-T";
			if (s[1].equals("4")) media = "100Base-FX";
			if (s[1].equals("7")) media = "10Base-FL";
			if (s[1].equals("12")) media = "ISL FX";
			if (s[1].equals("13")) media = "ISL TX";

			sw.setSpeed(speed);
			sw.setMedia(media);
		}

		// Hent duplex
		sSnmp.setParams(ip, cs_ro, duplexOid);
		portList = sSnmp.getAll();
		for (int i=0; i < portList.size(); i++) {
			String[] s = (String[])portList.get(i);
			String ifindex = getLastToken(s[0]);
			Swport sw = (Swport)portMap.get(ifindex);

			char duplex = (s[1].equals("1") ? 'f' : 'h');
			sw.setDuplex(duplex);

		}

		// Hent trunk
		sSnmp.setParams(ip, cs_ro, trunkOid);
		portList = sSnmp.getAll();
		for (int i=0; i < portList.size(); i++) {
			String[] s = (String[])portList.get(i);
			String ifindex = getLastToken(s[0]);
			Swport sw = (Swport)portMap.get(ifindex);

			boolean trunk = s[1].equals("1");
			sw.setTrunk(trunk);
		}

		// Hent vlan
		sSnmp.setParams(ip, cs_ro, vlanOid);
		portList = sSnmp.getAll();
		for (int i=0; i < portList.size(); i++) {
			String[] s = (String[])portList.get(i);
			String vlan = new StringTokenizer(s[0],".").nextToken();

			s[1] = removeString(s[1], ":");
			ArrayList portVlanList = getPortVlan(s[1]);
			for (int j=0; j < portVlanList.size(); j++) {
				String p = (String)portVlanList.get(j);
				Swport sw = (Swport)portMap.get(p);
				if (sw == null) {
					Log.w("PROCESS_CSWBASIC", "Port: " + p + " not found in portMap ("+typeid+"), netboxid: " + netboxid);
					continue;
				}

				if (sw.getTrunk()) {
					// Trunk, da skal vi lage oss en fin hexstring som går i swportallowedvlan
					sw.addTrunkVlan(vlan);
				} else {
					sw.setVlan(Integer.parseInt(vlan));
				}
			}
		}
	}

	private static ArrayList getPortVlan(String s)
	{
		ArrayList l = new ArrayList();

		// Vi får inn en hexstreng, f.eks: FF 0E 8A 00
		// Teller man fra venstre vil hver bit angi om vlanet kjører på porten
		// Funksjonen legger altså bare til posisjonen til alle bit'ene som er 1 til en liste
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
	private static String getLastToken(String s)
	{
		char sep = '.';
		int i;
		if ( (i=s.lastIndexOf(sep)) == -1) return s;

		return s.substring(i+1, s.length()).trim();
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

			//outl("  Found " + ifmpList.size() + " ifindex<->mp mappings.");
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

			//outl("  Found " + ifmpList.size() + " ifindex<->mp mappings.");
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
			Log.w("IFMP_CSWBASIC", "Unknown typegruppe: " + typegruppe);
			//return ifindexH;
		}
		return ifindexH;
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

}
