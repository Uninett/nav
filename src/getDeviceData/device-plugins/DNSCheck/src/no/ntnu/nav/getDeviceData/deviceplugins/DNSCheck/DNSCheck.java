package no.ntnu.nav.getDeviceData.deviceplugins.DNSCheck;

import java.util.*;
import java.net.*;

import no.ntnu.nav.logger.*;
import no.ntnu.nav.SimpleSnmp.*;
import no.ntnu.nav.ConfigParser.*;
import no.ntnu.nav.Database.*;
import no.ntnu.nav.event.*;
import no.ntnu.nav.util.*;
import no.ntnu.nav.getDeviceData.Netbox;
import no.ntnu.nav.getDeviceData.deviceplugins.*;
import no.ntnu.nav.getDeviceData.dataplugins.*;

/**
 * <p>
 * DeviceHandler for checking that the sysname and DNS record of a netbox corresponds.
 * </p>
 *
 * <p>
 * This plugin handles the following OID keys:
 * </p>
 *
 * <ul>
 *  <li>dnscheck</li>
 * </ul>
 * </p>
 *
 */

public class DNSCheck implements DeviceHandler
{
	private static String[] canHandleOids = {
		"dnscheck",
	};

	private SimpleSnmp sSnmp;

	public int canHandleDevice(Netbox nb) {
		int v = nb.isSupportedOids(canHandleOids) ? ALWAYS_HANDLE : NEVER_HANDLE;
		Log.d("DNSCHECK_CANHANDLE", "CHECK_CAN_HANDLE", "Can handle device: " + v);
		return v;
	}

	public void handleDevice(Netbox nb, SimpleSnmp sSnmp, ConfigParser cp, DataContainers containers) throws TimeoutException
	{
		Log.setDefaultSubsystem("DNSCHECK_DEVHANDLER");

		// Do DNS lookup
		InetAddress ia = null;
		try {
			ia = InetAddress.getByName(nb.getIp());
		} catch (UnknownHostException e) {
			// Cannot happen as we always supply an IP address
		}
		String dnsName = ia.getCanonicalHostName();
		if (dnsName.equals(nb.getIp())) {
			// DNS lookup failed
			Log.i("HANDLE", "DNS lookup failed for " + nb);
			return;
		}

		// dnsName and sysname should match - but for now we just check that dnsName starts with sysname
		if (!dnsName.startsWith(nb.getSysname())) {
			// Log
			Log.i("HANDLE", "Sysname ("+nb.getSysname()+") and DNS ("+dnsName+") does not match!");

			Map varMap = new HashMap();
			varMap.put("sysname", String.valueOf(nb.getSysname()));
			varMap.put("dnsname", dnsName);
			EventQ.createAndPostEvent("getDeviceData", "eventEngine", nb.getDeviceid(), nb.getNetboxid(), 0, "info", Event.STATE_NONE, 0, 0, varMap);
			
		}

	}

}
