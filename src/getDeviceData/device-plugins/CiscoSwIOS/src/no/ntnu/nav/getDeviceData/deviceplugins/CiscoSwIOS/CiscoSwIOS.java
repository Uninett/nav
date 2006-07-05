package no.ntnu.nav.getDeviceData.deviceplugins.CiscoSwIOS;

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
		//String sysName = nb.getSysname();
		//String cat = nb.getCat();
		this.sSnmp = sSnmp;

		processIOS(nb, netboxid, ip, cs_ro, type, mc, sc);

		// Commit data
		if (mc.isCommited()) sc.setEqual(mc);
		sc.commit();
	}

	private void processIOS(Netbox nb, String netboxid, String ip, String cs_ro, String typeid, ModuleContainer mc, SwportContainer sc) throws TimeoutException
	{
		typeid = typeid.toLowerCase();

		List l;

		l = sSnmp.getAll(nb.getOid("ifDescr"), true);

		// Check which interfaces match our pattern
		Set matchIfindex = new HashSet();
		Set moduleCntSet = new HashSet();
		if (l != null) {
			Log.d("PROCESS_IOS", "ifDescr reported " + l.size() + " ports");
			for (Iterator it = l.iterator(); it.hasNext();) {
				String[] s = (String[])it.next();
			
				String portif = s[1];
				String modulePattern = "((.*)(\\d+))/(\\d+)";

				if (portif.matches(modulePattern)) {
					matchIfindex.add(s[0]);
					Matcher m = Pattern.compile(modulePattern).matcher(portif);
					m.matches();
					moduleCntSet.add(m.group(3));
				}
			}
			Log.d("PROCESS_IOS", "Port name matching suggests " + moduleCntSet.size() + " modules");
		}
		if (matchIfindex.isEmpty()) return;

		//int highModule = -1; // Highest module number seen so far
		//Map moduleNumMap = new HashMap();

		MultiMap modPortMM = new HashMultiMap();
		MultiMap modNames = new HashMultiMap();
		for (Iterator it = l.iterator(); it.hasNext();) {
			String[] s = (String[])it.next();
			
			String ifindex = s[0];
			if (!matchIfindex.contains(ifindex)) continue;
			String portif = s[1];

			// Determine and create the module
			// Use *? because otherwise two digit numbers won't work!
			int module = 0;
			int realModule = 0;
			String modulePattern = "((.*?)(\\d+))/(\\d+)(/(\\d+))?";
			String moduleNamePattern = "((.*)(\\d+))/(\\d+)";

			String moduleName = null;
			if (portif.matches(modulePattern)) {
				Matcher m = Pattern.compile(moduleNamePattern).matcher(portif);
				m.matches();
				moduleName = m.group(1);

				m = Pattern.compile(modulePattern).matcher(portif);
				m.matches();
				module = Integer.parseInt(m.group(3));
				realModule = module;
				/*
				if (!moduleNumMap.containsKey(moduleName)) {
					if (module > highModule) {
						highModule = module;
					} else {
						module = ++highModule;
					}
					moduleNumMap.put(moduleName, new Integer(module));
				} else {
					module = ((Integer)moduleNumMap.get(moduleName)).intValue();
				}
				*/
				// If submodule then we add the submodule number to module as a string
				if (util.groupCountNotNull(m) >= 6) {
					String submod = m.group(4);
					String newmodule = module + submod;
					mc.moduleTranslate(""+module, newmodule);
					sc.moduleTranslate(""+module, newmodule);
					module = Integer.parseInt(newmodule);
					realModule = module;
					mc.moduleFactory(module);
				}
			}

			Module md = mc.getModule(module);
			if (md == null) {
				if (module == 0 && moduleCntSet.size() == 1) {
					module = 1;
					md = mc.moduleFactory(1);
				} else {
					// Not allowed to create module
					Log.w("PROCESS_IOS", "Module " + module + " ("+moduleName+") does not exist on netbox " + nb.getSysname() + ", skipping");
					continue;
				}
			}
			SwModule swm = sc.swModuleFactory(module);
			Module mm = mc.moduleFactory(module);
			Swport swp = swm.swportFactory(ifindex); // Create module <-> ifindex mapping
			if (moduleName != null) {
				boolean composed = false;
				if (!modNames.put(new Integer(module), moduleName)) {
					String cModuleName = composeModuleName(realModule, modNames.get(new Integer(module)));
					if (!moduleName.equals(cModuleName)) {
						composed = true;
						moduleName = cModuleName;
					}
				}
				if ((mm.getDescr() == null && md.getDescr() == null) || composed) {
					md.setDescr(moduleName);
				}
			}

			String[] modulport = portif.split("/");
			if (modulport.length > 1) {
				try {
					// If we have a submodule the port is one index higher
					Integer port = modulport.length > 2 ? Integer.valueOf(modulport[2]) : Integer.valueOf(modulport[1]);
					if (!modPortMM.put(new Integer(module), port)) {
						port = new Integer(Integer.parseInt(ifindex));
					}
					swp.setPort(port);
				} catch (NumberFormatException e) { }
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
				if (!matchIfindex.contains(ifindex)) continue;
				int vlan = 0;
				try{
					vlan = Integer.parseInt(s[1]);
				} catch	 (NumberFormatException e) {
					Log.w("PROCESS_IOS", "netboxid: " + netboxid + " ifindex: " + s[0] + " NumberFormatException on vlan: " + s[1]);
				}
				sc.swportFactory(ifindex).setVlan(vlan);
			}
		}

		l = sSnmp.getAll(nb.getOid("ifTrunk"));
		if (l != null) {
			for (Iterator it = l.iterator(); it.hasNext();) {
				String[] s = (String[])it.next();
				String ifindex = s[0];
				if (!matchIfindex.contains(ifindex)) continue;

				boolean trunk = (s[1].equals("1") ? true : false);
				sc.swportFactory(ifindex).setTrunk(trunk);
			}
		}

		l = sSnmp.getAll(nb.getOid("ifVlansAllowed"));
		if (l != null) {
			for (Iterator it = l.iterator(); it.hasNext();) {
				String[] s = (String[])it.next();
				if (!matchIfindex.contains(s[0])) continue;
				sc.swportFactory(s[0]).setHexstring(s[1]);
			}
		}
		
		l = sSnmp.getAll(nb.getOid("ifPortName"), true);
		if (l != null) {
			for (Iterator it = l.iterator(); it.hasNext();) {
				String[] s = (String[])it.next();
				if (!matchIfindex.contains(s[0])) continue;
				sc.swportFactory(s[0]).setPortname(s[1]);
			}
		}

	}

	private String composeModuleName(int module, Set names) {
		Set ls = new HashSet(names);
		String n = "";
		String pat = "([a-zA-z]+)Ethernet(\\d+)";
		List nl = new ArrayList();
		boolean eth  = false;
		for (Iterator it = ls.iterator(); it.hasNext();) {
			String s = (String)it.next();
			Matcher m = Pattern.compile(pat).matcher(s);
			if (m.matches()) {
				it.remove();
				nl.add(m.group(1));
				eth = true;
			}
		}
		Collections.sort(nl);
		for (Iterator it = nl.iterator(); it.hasNext();) {
			n += it.next();
		}

		nl.clear();
		for (Iterator it = ls.iterator(); it.hasNext();) {
			nl.add(it.next());
		}
		Collections.sort(nl);
		for (Iterator it = nl.iterator(); it.hasNext();) {
			n += it.next();
		}

		if (eth) {
			n += "Ethernet" + module;
		}
		return n;
	}
}
