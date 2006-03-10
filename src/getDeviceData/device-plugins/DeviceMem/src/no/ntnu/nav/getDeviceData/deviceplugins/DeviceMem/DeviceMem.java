package no.ntnu.nav.getDeviceData.deviceplugins.DeviceMem;

import java.util.*;
import java.sql.ResultSet;
import java.sql.SQLException;

import no.ntnu.nav.logger.*;
import no.ntnu.nav.SimpleSnmp.*;
import no.ntnu.nav.ConfigParser.*;
import no.ntnu.nav.Database.*;
import no.ntnu.nav.event.*;
import no.ntnu.nav.util.*;
import no.ntnu.nav.getDeviceData.Netbox;
import no.ntnu.nav.getDeviceData.deviceplugins.*;
import no.ntnu.nav.getDeviceData.dataplugins.*;
import no.ntnu.nav.getDeviceData.dataplugins.Mem.*;

/**
 * <p>
 * DeviceHandler plugin for collecting memory info from netboxes.
 * </p>
 *
 * <p>
 * This plugin handles the following OID keys:
 * </p>
 *
 * <ul>
 *  <li>mem*</li>
 *  <li>flash*</li>
 * </ul>
 * </p>
 *
 */

public class DeviceMem implements DeviceHandler
{
	private static String[] canHandleOids = {
		"memName",
		"memUsed",
		"memFree",
		"flashName",
		"flashSize",
		"flashFree",
	};

	private SimpleSnmp sSnmp;

	public int canHandleDevice(Netbox nb) {
		int v = nb.isSupportedOids(canHandleOids) ? ALWAYS_HANDLE : NEVER_HANDLE;
		Log.d("MEM_CANHANDLE", "CHECK_CAN_HANDLE", "Can handle device: " + v);
		return v;
	}

	public void handleDevice(Netbox nb, SimpleSnmp sSnmp, ConfigParser cp, DataContainers containers) throws TimeoutException
	{
		Log.setDefaultSubsystem("MEM_DEVHANDLER");

		MemContainer mc;
		{
			DataContainer dc = containers.getContainer("MemContainer");
			if (dc == null) {
				Log.w("NO_CONTAINER", "No MemContainer found, plugin may not be loaded");
				return;
			}
			if (!(dc instanceof MemContainer)) {
				Log.w("NO_CONTAINER", "Container is not a MemContainer! " + dc);
				return;
			}
			mc = (MemContainer)dc;
		}
		
		List memName = sSnmp.getAll(nb.getOid("memName"), true);
		if (memName != null) {
			Map memUsed = sSnmp.getAllMap(nb.getOid("memUsed"));
			Map memFree = sSnmp.getAllMap(nb.getOid("memFree"));
			for (Iterator it = memName.iterator(); it.hasNext();) {
				String[] s = (String[])it.next();
				String idx = s[0];
				String name = s[1];
				long size=0, used=0;
				if (memUsed != null && memUsed.containsKey(idx) && memFree != null && memFree.containsKey(idx)) {
					used = Long.parseLong((String)memUsed.get(idx));
					size = used + Long.parseLong((String)memFree.get(idx));
					if (size < 0) Log.e("MEM_SIZE", "Invalid mem size: " + size);
					if (used < 0) Log.e("MEM_USED", "Invalid mem used: " + used);
				}
				mc.addMem(MemContainer.TYPE_MEMORY, name, size, used);
				mc.commit();
			}
		}

		List flashName = sSnmp.getAll(nb.getOid("flashName"), true);
		if (flashName != null) {
			Map flashSize = sSnmp.getAllMap(nb.getOid("flashSize"));
			Map flashFree = sSnmp.getAllMap(nb.getOid("flashFree"));
			for (Iterator it = flashName.iterator(); it.hasNext();) {
				String[] s = (String[])it.next();
				String idx = s[0];
				String name = s[1];
				long size=0, used=0;
				if (flashSize != null && flashSize.containsKey(idx)) {
					size = Long.parseLong((String)flashSize.get(idx));
					if (size < 0) Log.e("FLASH_SIZE", "Invalid flash size: " + size);
					if (flashFree != null && flashFree.containsKey(idx)) {
						used = size - Long.parseLong((String)flashFree.get(idx));
						if (used < 0) Log.e("FLASH_USED", "Invalid flash used: " + used + " (size: " + flashSize.get(idx) + " free: " + flashFree.get(idx) + ")");
					}
				}
				mc.addMem(MemContainer.TYPE_FLASH, name, size, used);
				mc.commit();
			}
		}

		

		/*
		*/


	}

}
