package no.ntnu.nav.getDeviceData.deviceplugins.CiscoSw1900;

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
 * DeviceHandler for collecting switch port data from C19xx switches.
 * </p>
 *
 * <p>
 * This plugin handles the following OID keys:
 * </p>
 *
 * <p>
 * <ui>
 *  <li>c1900Duplex</li>
 *  <li>c1900Portname</li>
 * </ul>
 * </p>
 *
 */

public class CiscoSw1900 implements DeviceHandler
{
	private static String[] canHandleOids = {
		"c1900Duplex",
		"c1900Portname"
	};

	private SimpleSnmp sSnmp;

	public int canHandleDevice(Netbox nb) {
		int v = nb.isSupportedOids(canHandleOids) ? ALWAYS_HANDLE : NEVER_HANDLE;
		Log.d("C1900_CANHANDLE", "CHECK_CAN_HANDLE", "Can handle device: " + v);
		return v;
	}

	public void handleDevice(Netbox nb, SimpleSnmp sSnmp, ConfigParser cp, DataContainers containers) throws TimeoutException
	{
		Log.setDefaultSubsystem("C1900_DEVHANDLER");
		
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

		processC1900(nb, netboxid, ip, cs_ro, type, sc);

		// Commit data
		sc.commit();
	}

	/*
	 * Cisco 1900
	 *
	 */
	private void processC1900(Netbox nb, String netboxid, String ip, String cs_ro, String type, SwportContainer sc) throws TimeoutException {
		/*
		Alle C1900*

	Duplex:
		1.3.6.1.4.1.437.1.1.3.3.1.1.8 = duplex

		1 = full
		2 = half

	Portnavn:
		1.3.6.1.4.1.437.1.1.3.3.1.1.3 = portnavn

		FIXME: Mangler info om media. Bruker vlan=1 på alle porter

		*/

		// Module is always 1 on this switch
		String module = "1";
		List l;

		// Switch port data
		l = sSnmp.getAll(nb.getOid("c1900Duplex"));
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

		l = sSnmp.getAll(nb.getOid("c1900Portname"));
		if (l != null) {
			for (Iterator it = l.iterator(); it.hasNext();) {
				String[] s = (String[])it.next();
				String[] s2 = s[0].split("\\.");
				String ifindex = s2[s2.length-1];
				String portname = s[1].trim();

				SwModule m = sc.swModuleFactory(module);
				m.swportFactory(ifindex).setPortname(portname);
			}
		}

	}
}
