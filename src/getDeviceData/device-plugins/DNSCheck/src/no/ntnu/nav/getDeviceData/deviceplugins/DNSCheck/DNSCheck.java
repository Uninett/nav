package no.ntnu.nav.getDeviceData.deviceplugins.DNSCheck;

import java.io.*;
import java.net.*;
import java.util.*;
import java.util.regex.*;

import no.ntnu.nav.logger.*;
import no.ntnu.nav.SimpleSnmp.*;
import no.ntnu.nav.ConfigParser.*;
import no.ntnu.nav.Database.*;
import no.ntnu.nav.event.*;
import no.ntnu.nav.util.*;
import no.ntnu.nav.getDeviceData.Netbox;
import no.ntnu.nav.getDeviceData.deviceplugins.*;
import no.ntnu.nav.getDeviceData.dataplugins.*;
import no.ntnu.nav.getDeviceData.dataplugins.Netbox.*;

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

	private static String[] hostBinCandidates = {
		"/bin/host",
		"/sbin/host",
		"/usr/bin/host",
		"/usr/sbin/host",
		"/usr/local/bin/host",
		"/usr/local/sbin/host",
	};
	private static File hostBin;
		

	private SimpleSnmp sSnmp;

	public int canHandleDevice(Netbox nb) {
		// DNS should run second, after Typeoid
		int v = nb.isSupportedOids(canHandleOids) ? -90 : NEVER_HANDLE;
		Log.d("DNSCHECK_CANHANDLE", "CHECK_CAN_HANDLE", "Can handle device: " + v);
		return v;
	}

	public void handleDevice(Netbox nb, SimpleSnmp sSnmp, ConfigParser cp, DataContainers containers) throws TimeoutException
	{
		Log.setDefaultSubsystem("DNSCHECK_DEVHANDLER");

		NetboxContainer nc;
		{
			DataContainer dc = containers.getContainer("NetboxContainer");
			if (dc == null) {
				Log.w("NO_CONTAINER", "No NetboxContainer found, plugin may not be loaded");
				return;
			}
			if (!(dc instanceof NetboxContainer)) {
				Log.w("NO_CONTAINER", "Container is not a NetboxContainer! " + dc);
				return;
			}
			nc = (NetboxContainer)dc;
		}

		// Do DNS lookup
		InetAddress ia = null;
		try {
			ia = InetAddress.getByName(nb.getIp());
		} catch (UnknownHostException e) {
			// Cannot happen as we always supply an IP address
		}
		String dnsName = ia.getCanonicalHostName();
		if (dnsName.equals(nb.getIp())) {
			Log.d("HANDLE", "Java DNS lookup failed for " + nb);

			dnsName = doHostReverseDNS(nb.getIp());
			if (dnsName.equals(nb.getIp())) {
				// DNS lookup failed
				Log.i("HANDLE", "DNS lookup failed for " + nb);
			}
		}

		nc.netboxDataFactory(nb).setSysname(dnsName);
		nc.commit();

	}

	private String doHostReverseDNS(String ip) {
		try {
			if (hostBin == null) {
				for (int i=0; i < hostBinCandidates.length; i++) {
					File f = new File(hostBinCandidates[i]);
					if (f.exists() && f.isFile()) {
						hostBin = f;
						break;
					}
				}
			}

			String[] hostCmd = {
				hostBin.getAbsolutePath(),
				ip
			};

			Runtime rt = Runtime.getRuntime();
			Process p = rt.exec(hostCmd);
			BufferedInputStream in = new BufferedInputStream(p.getInputStream());
			try {
				p.waitFor();
			} catch (InterruptedException e) {
				System.err.println("InterruptedException: " + e);
				e.printStackTrace(System.err);
				return ip;
			}

			byte[] b = new byte[1024];
			in.read(b, 0, 1024);
			String s = new String(b).trim();

			// Check if found
			if (s.indexOf("not found") >= 0) return ip;

			// Extract DNS name
			String pat = "(?s)(.*domain name pointer|Name:) +(\\S{3,}).*";

			if (s.matches(pat)) {
				Matcher m = Pattern.compile(pat).matcher(s);
				m.matches();
				String host = m.group(2);
				if (host.endsWith(".")) host = host.substring(0, host.length()-1);
				return host;
			}

		} catch (IOException e) {
			System.err.println("IOException: " + e);
			e.printStackTrace(System.err);
		}
		return ip;
	}

}
