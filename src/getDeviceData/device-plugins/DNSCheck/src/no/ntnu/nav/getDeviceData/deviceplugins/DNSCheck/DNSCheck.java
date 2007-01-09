/*
 * $Id$ 
 *
 * Copyright 2004 Norwegian University of Science and Technology
 * Copyright 2007 UNINETT AS
 * 
 * This file is part of Network Administration Visualized (NAV)
 * 
 * NAV is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 * 
 * NAV is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with NAV; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 *
 */
package no.ntnu.nav.getDeviceData.deviceplugins.DNSCheck;

import no.ntnu.nav.ConfigParser.ConfigParser;
import no.ntnu.nav.SimpleSnmp.SimpleSnmp;
import no.ntnu.nav.SimpleSnmp.TimeoutException;
import no.ntnu.nav.getDeviceData.Netbox;
import no.ntnu.nav.getDeviceData.dataplugins.DataContainer;
import no.ntnu.nav.getDeviceData.dataplugins.DataContainers;
import no.ntnu.nav.getDeviceData.dataplugins.Netbox.NetboxContainer;
import no.ntnu.nav.getDeviceData.deviceplugins.DeviceHandler;
import no.ntnu.nav.logger.Log;

/**
 * <p>
 * DeviceHandler for checking that the sysname and DNS record of a netbox correspond.
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
 * @version $Id$
 * @author Kristian Eide &lt;kreide@gmail.com&gt;,
 *         Morten Brekkevold &lt;morten.brekkevold@uninett.no&gt;
 */

public class DNSCheck implements DeviceHandler
{
	private static String[] canHandleOids = {
		"dnscheck",
	};

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

		// Do reverse DNS lookup
		String name = DNSResolver.reverseLookup(nb.getIp());
		if (name.equals(nb.getIp())) {
			Log.e("HANDLE", "Reverse DNS lookup failed for " + nb.getIp());
		}
		
		nc.netboxDataFactory(nb).setSysname(name);
		nc.commit();
	}

}
