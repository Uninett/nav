package no.ntnu.nav.getDeviceData.deviceplugins.CiscoSwIOSaddon;

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
 * DeviceHandler for collecting the extra Cisco IOS switch port OIDs.
 * </p>
 *
 * <p>
 * This plugin handles the following OID keys:
 * </p>
 *
 * <ul>
 *  <li>From Cisco IOS</li>
 *  <ul>
 *   <li>iosTrunk</li>
 *   <li>iosDuplex</li>
 *  </ul>
 * </ul>
 * </p>
 *
 */

public class CiscoSwIOSaddon implements DeviceHandler
{
	private static String[] canHandleOids = {
	    "iosTrunk", 
	    "iosDuplex", 
	};

	private SimpleSnmp sSnmp;

	public int canHandleDevice(Netbox nb) {
		int v = nb.isSupportedOids(canHandleOids) ? ALWAYS_HANDLE : NEVER_HANDLE;
		Log.d("IOSaddon_CANHANDLE", "CHECK_CAN_HANDLE", "Can handle device: " + v);
		return v;
	}

	public void handleDevice(Netbox nb, SimpleSnmp sSnmp, ConfigParser cp, DataContainers containers) throws TimeoutException
	{
		Log.setDefaultSubsystem("IOSaddon_DEVHANDLER");
		
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
		this.sSnmp = sSnmp;

		processIOSaddon(nb, netboxid, ip, cs_ro, sc);

	}

	private void processIOSaddon(Netbox nb, String netboxid, String ip, String cs_ro, SwportContainer sc) throws TimeoutException
	{
		// Map port to ifindex
		Map ifindexMap = sSnmp.getAllMap(nb.getOid("iosPortIfindex"), false);
		if (ifindexMap != null) {
			List l;
		
			l = sSnmp.getAll(nb.getOid("iosTrunk"));
			if (l != null) {
				for (Iterator it = l.iterator(); it.hasNext();) {
					String[] s = (String[])it.next();
					String ifindex = (String)ifindexMap.get(s[0]);
					if (ifindex == null) continue;

					boolean trunk = (s[1].equals("1") ? false : true);
					sc.swportFactory(ifindex).setTrunk(trunk);
				}
			}
			l = sSnmp.getAll(nb.getOid("iosDuplex"));
			if (l != null) {
				for (Iterator it = l.iterator(); it.hasNext();) {
					String[] s = (String[])it.next();
					String ifindex = (String)ifindexMap.get(s[0]);
					if (ifindex == null) continue;

					char duplex = (s[1].equals("1") ? 'f' : 'h');
					sc.swportFactory(ifindex).setDuplex(duplex);
					sc.swportFactory(ifindex).setPort(Integer.valueOf(s[0]));
				}
			}
		}
	}
}
