package no.ntnu.nav.getDeviceData.deviceplugins.CiscoSwCAT;

import java.util.*;
import java.util.regex.*;

import no.ntnu.nav.logger.*;
import no.ntnu.nav.util.*;
import no.ntnu.nav.SimpleSnmp.*;
import no.ntnu.nav.ConfigParser.*;
import no.ntnu.nav.getDeviceData.Netbox;
import no.ntnu.nav.getDeviceData.deviceplugins.*;
import no.ntnu.nav.getDeviceData.dataplugins.*;
import no.ntnu.nav.getDeviceData.dataplugins.Module.*;
import no.ntnu.nav.getDeviceData.dataplugins.Swport.*;

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
 *	 <li>ifName</li>
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

		String netboxid = nb.getNetboxidS();
		String ip = nb.getIp();
		String cs_ro = nb.getCommunityRo();
		String type = nb.getType();
		this.sSnmp = sSnmp;

		processCAT(nb, netboxid, ip, cs_ro, type, mc, sc);

		// Commit data
		sc.commit();
	}
	
	private void processCAT(Netbox nb, String netboxid, String ip, String cs_ro, String typeid, ModuleContainer mc, SwportContainer sc) throws TimeoutException
	{
		typeid = typeid.toLowerCase();

		List l;

		HashMap modPortIfindex = new HashMap();
		List o = sSnmp.getAll(nb.getOid("portIfIndex"));

		if (o != null) {
			HashMap ifModule = new HashMap();
			l = sSnmp.getAll(nb.getOid("ifName"), true);
			if (l != null) {
				// Count number of modules
				Set moduleCntSet = new HashSet();
				for (Iterator it = l.iterator(); it.hasNext();) {
					String[] s = (String[])it.next();
					String portif = s[1];
					String modulePattern = "((.*)(\\d+))/(\\d+)";
					if (portif.matches(modulePattern)) {
						Matcher m = Pattern.compile(modulePattern).matcher(portif);
						m.matches();
						moduleCntSet.add(m.group(3));
					}
				}

				for (Iterator it = l.iterator(); it.hasNext();) {
					String[] s = (String[])it.next();

					String ifindex = s[0];
					String portif = s[1];

					// Determine and create the module
					// Use *? because otherwise two digit numbers won't work!
					//String modulePattern = ".*?(\\d+)/(\\d+)";
					String modulePattern = "((.*?)(\\d+))/(\\d+)(/(\\d+))?";
					if (portif.matches(modulePattern)) {
						Matcher m = Pattern.compile(modulePattern).matcher(portif);
						m.matches();
						int module = Integer.parseInt(m.group(3));

						// If submodule then we add the submodule number to module as a string
						if (util.groupCountNotNull(m) >= 6) {
							String submod = m.group(4);
							module = Integer.parseInt(module + submod);
							mc.moduleFactory(module);
						}

						if (mc.getModule(module) == null) {
							if (module == 0 && moduleCntSet.size() == 1) {
								module = 1;
								mc.moduleFactory(1);
							} else {
								// Not allowed to create module
								Log.w("PROCESS_CAT", "Module " + module + " does not exist on netbox " + nb.getSysname() + ", skipping");
								continue;
							}
						}

						SwModule swm = sc.swModuleFactory(module);
						swm.swportFactory(ifindex); // Create module <-> ifindex mapping
						//swm.setDescr(portif.split("/")[0]);
					}
				}
			}
			for (Iterator it = o.iterator(); it.hasNext();) {
				String[] s = (String[])it.next();

				String modport = s[0];
				String ifindex = s[1];
				String[] s2 = s[0].split("\\.");
				modPortIfindex.put(s[0],s[1]);
			
				Integer port = Integer.valueOf(s2[1]);
				sc.swportFactory(ifindex).setPort(port);
			}
			
			l = sSnmp.getAll(nb.getOid("portDuplex"));
			if (l != null) {
				for (Iterator it = l.iterator(); it.hasNext();) {
					String[] s = (String[])it.next();
					String modport = s[0];
					String ifindex = (String)modPortIfindex.get(modport);
					char duplex = (s[1].equals("1") ? 'h' : 'f');
					sc.swportFactory(ifindex).setDuplex(duplex);
				}
			}

			l = sSnmp.getAll(nb.getOid("portPortName"), true);
			if (l != null) {
				for (Iterator it = l.iterator(); it.hasNext();) {
					String[] s = (String[])it.next();
					String ifindex = (String) modPortIfindex.get(s[0]);
					sc.swportFactory(ifindex).setPortname(s[1]);
				}
			}
				
			l = sSnmp.getAll(nb.getOid("portVlan"));
			if (l != null) {
				for (Iterator it = l.iterator(); it.hasNext();) {
					String[] s = (String[])it.next();
					String[] s2 = s[0].split("\\.");
					int vlan = 0;
					try{
						vlan = Integer.parseInt(s[1]);
					} catch	 (NumberFormatException e) {
						Log.w("PROCESS_CAT", "netboxid: " + netboxid + " ifindex: " + s[0] + " NumberFormatException on vlan: " + s[1]);
					}
					String ifindex = (String) modPortIfindex.get(s[0]);
					sc.swportFactory(ifindex).setVlan(vlan);
				}
			}
				
			l = sSnmp.getAll(nb.getOid("portTrunk"));
			if (l != null) {
				for (Iterator it = l.iterator(); it.hasNext();) {
					String[] s = (String[])it.next();
					boolean trunk = (s[1].equals("1") ? true : false);
					String ifindex = (String) modPortIfindex.get(s[0]);
					sc.swportFactory(ifindex).setTrunk(trunk);
				}
			}
				
			l = sSnmp.getAll(nb.getOid("portVlansAllowed"));
			if (l != null) {
				for (Iterator it = l.iterator(); it.hasNext();) {
					String[] s = (String[])it.next();
					String ifindex = (String) modPortIfindex.get(s[0]);
					sc.swportFactory(ifindex).setHexstring(s[1]);
				}
			}
				
		}

	}
}
