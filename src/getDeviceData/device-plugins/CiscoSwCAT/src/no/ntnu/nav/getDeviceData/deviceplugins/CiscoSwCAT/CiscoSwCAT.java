package no.ntnu.nav.getDeviceData.deviceplugins.CiscoSwCAT;

import java.util.HashMap;
import java.util.Iterator;
import java.util.List;

import no.ntnu.nav.ConfigParser.ConfigParser;
import no.ntnu.nav.SimpleSnmp.SimpleSnmp;
import no.ntnu.nav.SimpleSnmp.TimeoutException;
import no.ntnu.nav.getDeviceData.Netbox;
import no.ntnu.nav.getDeviceData.dataplugins.DataContainer;
import no.ntnu.nav.getDeviceData.dataplugins.DataContainers;
import no.ntnu.nav.getDeviceData.dataplugins.Module.ModuleContainer;
import no.ntnu.nav.getDeviceData.dataplugins.Swport.SwModule;
import no.ntnu.nav.getDeviceData.dataplugins.Swport.SwportContainer;
import no.ntnu.nav.getDeviceData.deviceplugins.DeviceHandler;
import no.ntnu.nav.logger.Log;

/**
 * <p>
 * DeviceHandler for collecting the standard Cisco CAT switch port OIDs.
 * </p>
 *
 * <p>
 * This plugin handles the following OID keys:
 * </p>
 *
 * <ul>
 *	<li>From Cisco CAT</li>
 *	<ul>
 *	 <li>portIfIndex</li>
 *	 <li>portDuplex</li>
 *	 <li>portVlan</li>
 *	 <li>portVlansAllowed</li>
 *	 <li>portTrunk</li>
 *	 <li>portPortName</li>
 *	</ul>
 * </ul>
 * </p>
 *
 */

public class CiscoSwCAT implements DeviceHandler
{
	private static String[] canHandleOids = {
			"portDuplex", 
			"portIfIndex", 
			"portVlan", 
			"portTrunk", 
			"portVlansAllowed", 
			"portPortName",
	};

	private SimpleSnmp sSnmp;

	public int canHandleDevice(Netbox nb) {
		int v = nb.isSupportedOids(canHandleOids) ? ALWAYS_HANDLE : NEVER_HANDLE;

		Log.d("CAT_CANHANDLE", "CHECK_CAN_HANDLE", "Can handle device: " + v);
		return v;
	}

	public void handleDevice(Netbox nb, SimpleSnmp sSnmp, ConfigParser cp, DataContainers containers) throws TimeoutException
	{
		Log.setDefaultSubsystem("CAT_DEVHANDLER");

		ModuleContainer mc;
		{
			DataContainer dc = containers.getContainer("ModuleContainer");
			if (dc == null) {
				Log.w("NO_CONTAINER", "No ModuleContainer found, plugin may not be loaded");
				return;
			}
			if (!(dc instanceof ModuleContainer)) {
				Log.w("NO_CONTAINER", "Container is not a ModuleContainer! " + dc);
				return;
			}
			mc = (ModuleContainer)dc;
		}

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

		this.sSnmp = sSnmp;

		processCAT(nb, mc, sc);

		// Commit data
		if (mc.isCommited()) sc.setEqual(mc);
		sc.commit();
	}

	/**
	 * <p>Collects and processes data from a Cisco Switch running CatOS (or otherwise OID compatible box).</p>
	 * 
	 * <p>As opposed to the CiscoSwCAT plugin, this one requires the portIfIndex OID to be supported, or
	 * no interfaces will be collected.</p>
	 * 
	 */
	private void processCAT(Netbox nb, ModuleContainer mc, SwportContainer sc) throws TimeoutException
	{
		HashMap modPortIfindex = new HashMap();
		List portIfIndexes = sSnmp.getAll(nb.getOid("portIfIndex"));

		if (portIfIndexes != null) {
			// Iterate the portIfIndex response to enumerate modules/ports
			for (Iterator it = portIfIndexes.iterator(); it.hasNext();) {
				String[] s = (String[])it.next();
				String moduleDotPort = s[0];
				String ifindex = s[1];
				
				String[] s2 = moduleDotPort.split("\\.");
				Integer module = Integer.valueOf(s2[0]);
				Integer port = Integer.valueOf(s2[1]);
				modPortIfindex.put(moduleDotPort, ifindex);
				Log.d("PROCESS_CAT", "ifIndex " + ifindex+ " maps to " + moduleDotPort);
				
				SwModule swm = sc.swModuleFactory(module.intValue());
				swm.swportFactory(ifindex).setPort(port); // Create module <-> ifindex mapping
			}
			
			List response = sSnmp.getAll(nb.getOid("portDuplex"));
			if (response != null) {
				for (Iterator it = response.iterator(); it.hasNext();) {
					String[] s = (String[])it.next();
					String modport = s[0];
					String ifindex = (String)modPortIfindex.get(modport);
					char duplex = (s[1].equals("1") ? 'h' : 'f');
					sc.swportFactory(ifindex).setDuplex(duplex);
				}
			}

			response = sSnmp.getAll(nb.getOid("portPortName"), true);
			if (response != null) {
				for (Iterator it = response.iterator(); it.hasNext();) {
					String[] s = (String[])it.next();
					String ifindex = (String) modPortIfindex.get(s[0]);
					sc.swportFactory(ifindex).setPortname(s[1]);
				}
			}
				
			response = sSnmp.getAll(nb.getOid("portVlan"));
			if (response != null) {
				for (Iterator it = response.iterator(); it.hasNext();) {
					String[] s = (String[])it.next();
					int vlan = 0;
					try{
						vlan = Integer.parseInt(s[1]);
					} catch	 (NumberFormatException e) {
						Log.w("PROCESS_CAT", "netboxid: " + nb.getNetboxid() + " ifindex: " + s[0] + " NumberFormatException on vlan: " + s[1]);
					}
					String ifindex = (String) modPortIfindex.get(s[0]);
					sc.swportFactory(ifindex).setVlan(vlan);
				}
			}

			response = sSnmp.getAll(nb.getOid("portTrunk"));
			if (response != null) {
				for (Iterator it = response.iterator(); it.hasNext();) {
					String[] s = (String[])it.next();
					boolean trunk = (s[1].equals("1") ? true : false);
					String ifindex = (String) modPortIfindex.get(s[0]);
					sc.swportFactory(ifindex).setTrunk(trunk);
				}
			}

			response = sSnmp.getAll(nb.getOid("portVlansAllowed"));
			if (response != null) {
				for (Iterator it = response.iterator(); it.hasNext();) {
					String[] s = (String[])it.next();
					String ifindex = (String) modPortIfindex.get(s[0]);
					sc.swportFactory(ifindex).setHexstring(s[1]);
				}
			}
				
		}

	}
}
