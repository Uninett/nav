package no.ntnu.nav.getDeviceData.deviceplugins.CiscoSwCL3addon;

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
 * DeviceHandler for collecting the extra Cisco CL3 switch port OIDs.
 * </p>
 *
 * <p>
 * This plugin handles the following OID keys:
 * </p>
 *
 * <ul>
 *  <li>From Cisco CL3</li>
 *  <ul>
 *   <li>cL3Trunk</li>
 *  </ul>
 * </ul>
 * </p>
 *
 */


public class CiscoSwCL3addon implements DeviceHandler
{
	private static String[] canHandleOids = {
	    "cL3Trunk", 
	};
	private static boolean VERBOSE_OUT = true;
	private static boolean DEBUG_OUT = true;

	private SimpleSnmp sSnmp;

	public int canHandleDevice(Netbox nb) {
		int v = nb.isSupportedOids(canHandleOids) ? ALWAYS_HANDLE : NEVER_HANDLE;
		Log.d("CL3addon_CANHANDLE", "CHECK_CAN_HANDLE", "Can handle device: " + v);
		return v;
	}

	public void handleDevice(Netbox nb, SimpleSnmp sSnmp, ConfigParser cp, DataContainers containers) throws TimeoutException
	{
		Log.setDefaultSubsystem("CL3addon_DEVHANDLER");
		
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
		this.sSnmp = sSnmp;

		processCL3addon(nb, netboxid, ip, cs_ro, type, sc);

	}

	private void processCL3addon(Netbox nb, String netboxid, String ip, String cs_ro, String typeid, SwportContainer sc) throws TimeoutException
	{
		typeid = typeid.toLowerCase();

		List l;

		l = sSnmp.getAll(nb.getOid("cL3Trunk"));
		if (l != null) {
			for (Iterator it = l.iterator(); it.hasNext();) {
				String[] s = (String[])it.next();
				boolean trunk = (s[1].equals("1") ? true : false);
				sc.swportFactory(s[0]).setTrunk(trunk);
			}
		}
	}
}
