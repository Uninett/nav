package no.ntnu.nav.getDeviceData.deviceplugins.CiscoSwIOS;

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
 * DeviceHandler for collecting the standard Cisco IOS switch port OIDs.
 * </p>
 *
 * <p>
 * This plugin handles the following OID keys:
 * </p>
 *
 * <ul>
 *	<li>From Cisco IOS</li>
 *	<ul>
 *	 <li>ifDescr</li>
 *	 <li>ifName</li>
 *	 <li>ifVlan</li>
 *	 <li>ifVlansAllowed</li>
 *	 <li>portPortName</li>
 *	</ul>
 * </ul>
 * </p>
 *
 */

public class CiscoSwIOS implements DeviceHandler
{
	private static String[] canHandleOids = {
			"ifDescr", 
			"ifVlan", 
			"ifVlansAllowed", 
			"ifPortName",
	};

	private SimpleSnmp sSnmp;

	public int canHandleDevice(Netbox nb) {
		int v = nb.isSupportedOids(canHandleOids) ? ALWAYS_HANDLE : NEVER_HANDLE;

		Log.d("IOS_CANHANDLE", "CHECK_CAN_HANDLE", "Can handle device: " + v);
		return v;
	}

	public void handleDevice(Netbox nb, SimpleSnmp sSnmp, ConfigParser cp, DataContainers containers) throws TimeoutException
	{
		Log.setDefaultSubsystem("IOS_DEVHANDLER");
		
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
		//String sysName = nb.getSysname();
		//String cat = nb.getCat();
		this.sSnmp = sSnmp;

		processIOS(nb, netboxid, ip, cs_ro, type, sc);

		// Commit data
		sc.commit();
	}

	private void processIOS(Netbox nb, String netboxid, String ip, String cs_ro, String typeid, SwportContainer sc) throws TimeoutException
	{
		typeid = typeid.toLowerCase();

		List l;

		//String stackOid = "1.3.6.1.4.1.11.2.14.11.5.1.10.4.1.1";//?

		String ifIndexOid = ".1.3.6.1.2.1.2.2.1.1";
		String ifSpeedOid = ".1.3.6.1.2.1.2.2.1.5";
		String ifAdmStatusOid = ".1.3.6.1.2.1.2.2.1.7";
		String ifOperStatusOid = ".1.3.6.1.2.1.2.2.1.8";
		//String ifPortOid = ".1.3.6.1.2.1.31.1.1.1.1";

		//String serialOid = ".1.3.6.1.4.1.9.5.1.3.1.1.26";
		//String hwOid = ".1.3.6.1.4.1.9.5.1.3.1.1.18";
		//String swOid = ".1.3.6.1.4.1.9.5.1.3.1.1.20";

		//String portIfOid = ".1.3.6.1.4.1.9.5.1.4.1.1.11";
		String ifPortOid = ".1.3.6.1.2.1.2.2.1.2";
		String ifDuplexOid = ".1.3.6.1.4.1.9.9.87.1.4.1.1.32.0";
		//String portTypeOid = ".1.3.6.1.4.1.11.2.14.11.5.1.7.1.3.1.1.2";
		String portNameOid = ".1.3.6.1.4.1.9.2.2.1.1.28";
		String ifTrunkOid = ".1.3.6.1.4.1.9.9.87.1.4.1.1.6.0";
		String vlanHexOid = ".1.3.6.1.4.1.9.9.46.1.6.1.1.4";
		String vlanOid = ".1.3.6.1.4.1.9.9.68.1.2.2.1.2";

		l = sSnmp.getAll(nb.getOid("ifDescr"));

		for (Iterator it = l.iterator(); it.hasNext();) {
			String[] s = (String[])it.next();
			
			String ifindex = s[0];
			String portif = s[1];

			// Determine and create the module
			int module = 0;
			String modulePattern = ".*?(\\d+)/.*";
			if (portif.matches(modulePattern)) {
				Matcher m = Pattern.compile(modulePattern).matcher(portif);
				m.matches();
				module = Integer.parseInt(m.group(1));
			}
			SwModule swm = sc.swModuleFactory(module);
			Swport swp = swm.swportFactory(ifindex); // Create module <-> ifindex mapping

			String[] modulport = portif.split("/");
			if (modulport.length > 1) {
				Integer port = Integer.valueOf(modulport[1]);
				swp.setPort(port);
			}
		}

		/*		l = sSnmp.getAll(nb.getOid("ifDuplex"));
					if (l != null) {
					for (Iterator it = l.iterator(); it.hasNext();) {
					String[] s = (String[])it.next();
					String ifindex = s[0];
					char duplex = (s[1].equals("1") ? 'f' : 'h');
					sc.swportFactory(ifindex).setDuplex(duplex);
					}
					}*/
		l = sSnmp.getAll(nb.getOid("ifVlan"));
		if (l != null) {
			for (Iterator it = l.iterator(); it.hasNext();) {
				String[] s = (String[])it.next();
				String ifindex = s[0];
				int vlan = 0;
				try{
					vlan = Integer.parseInt(s[1]);
				} catch	 (NumberFormatException e) {
					Log.w("PROCESS_CAT", "netboxid: " + netboxid + " ifindex: " + s[0] + " NumberFormatException on vlan: " + s[1]);
				}
				sc.swportFactory(ifindex).setVlan(vlan);
			}
		}

		/*	l = sSnmp.getAll(nb.getOid("ifTrunk"));
				if (l != null) {
				for (Iterator it = l.iterator(); it.hasNext();) {
				String[] s = (String[])it.next();
				boolean trunk = (s[1].equals("1") ? true : false);
				String[] s2 = s[0].split("\\.");
				String module = s2[0];
				String ifindex = (String) modPortIfindex.get(s[0]);
				String mo = (String) ifModule.get(module);
				module = (mo != null ? mo : module);
				SwModule m = sc.swModuleFactory(module);
				m.swportFactory(ifindex).setTrunk(trunk);
				}
				}*/

		l = sSnmp.getAll(nb.getOid("ifVlansAllowed"));
		if (l != null) {
			for (Iterator it = l.iterator(); it.hasNext();) {
				String[] s = (String[])it.next();
				sc.swportFactory(s[0]).setHexstring(s[1]);
			}
		}
		
		l = sSnmp.getAll(nb.getOid("ifPortName"), true);
		if (l != null) {
			for (Iterator it = l.iterator(); it.hasNext();) {
				String[] s = (String[])it.next();
				sc.swportFactory(s[0]).setPortname(s[1]);
			}
		}

	}
}
