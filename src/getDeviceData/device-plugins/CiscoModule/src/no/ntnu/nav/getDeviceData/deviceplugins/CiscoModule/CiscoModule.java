package no.ntnu.nav.getDeviceData.deviceplugins.CiscoModule;

import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import no.ntnu.nav.ConfigParser.ConfigParser;
import no.ntnu.nav.SimpleSnmp.SimpleSnmp;
import no.ntnu.nav.SimpleSnmp.TimeoutException;
import no.ntnu.nav.getDeviceData.Netbox;
import no.ntnu.nav.getDeviceData.dataplugins.DataContainer;
import no.ntnu.nav.getDeviceData.dataplugins.DataContainers;
import no.ntnu.nav.getDeviceData.dataplugins.Module.Module;
import no.ntnu.nav.getDeviceData.dataplugins.Module.ModuleContainer;
import no.ntnu.nav.getDeviceData.dataplugins.ModuleMon.ModuleMonContainer;
import no.ntnu.nav.getDeviceData.dataplugins.Netbox.NetboxContainer;
import no.ntnu.nav.getDeviceData.dataplugins.Netbox.NetboxData;
import no.ntnu.nav.getDeviceData.deviceplugins.DeviceHandler;
import no.ntnu.nav.logger.Log;
import no.ntnu.nav.util.MultiMap;
import no.ntnu.nav.util.util;

/**
 * <p>
 * DeviceHandler for collecting Cisco module info.
 * </p>
 *
 * <p>
 * This plugin handles the following OID keys:
 * </p>
 *
 * <p>
 * <ui>
 *  <li>cCard*</li>
 *  <li>cL3*</li>
 *  <li>catModule*</li>
 * </ul>
 * </p>
 */

public class CiscoModule implements DeviceHandler
{
	public static final boolean DEBUG = false;

	public static final int HANDLE_PRI_MODULE = -20;

	private static String[] canHandleOids = {
		"cChassisId",
		"cCardSlotNumber",
		"cL3Serial",
		"cL3Model",
		"cL3HwVer",
		"cL3FwVer",
		"cL3SwVer",
		"catModuleModel",
		"catModuleHwVer",
		"catModuleFwVer",
		"catModuleSwVer",
		"catModuleSerial",
		"physClass",
		"physSwVer",
		"physDescr",
		"physSerial",
		"physHwVer",
		"physFwVer",
		"physModelName",
	};

	private SimpleSnmp sSnmp;

	public int canHandleDevice(Netbox nb) {
		int v = nb.isSupportedOids(canHandleOids) ? HANDLE_PRI_MODULE : NEVER_HANDLE;
		Log.d("CMOD_CANHANDLE", "CHECK_CAN_HANDLE", "Can handle device: " + v);
		return v;
	}

	public void handleDevice(Netbox nb, SimpleSnmp sSnmp, ConfigParser cp, DataContainers containers) throws TimeoutException
	{
		Log.setDefaultSubsystem("CMOD_DEVHANDLER");
		
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

		ModuleMonContainer mmc;
		{
			DataContainer dc = containers.getContainer("ModuleMonContainer");
			if (dc == null) {
				Log.w("NO_CONTAINER", "No ModuleMonContainer found, plugin may not be loaded");
				return;
			}
			if (!(dc instanceof ModuleMonContainer)) {
				Log.w("NO_CONTAINER", "Container is not a ModuleMonContainer! " + dc);
				return;
			}
			mmc = (ModuleMonContainer)dc;
		}


		String netboxid = nb.getNetboxidS();
		String ip = nb.getIp();
		String cs_ro = nb.getCommunityRo();
		String type = nb.getType();
		String sysName = nb.getSysname();
		String cat = nb.getCat();
		this.sSnmp = sSnmp;

		boolean fetch = processCiscoModule(nb, netboxid, ip, cs_ro, type, nc, mc, mmc);
			
		// Commit data
		if (fetch) {
			mc.commit();
		}
	}

	/*
	 * Cisco modules
	 *
	 */
	private boolean processCiscoModule(Netbox nb, String netboxid, String ip, String cs_ro, String type, NetboxContainer nc, ModuleContainer mc, ModuleMonContainer mmc) throws TimeoutException {

		/*
		  "catModuleModel",
		  "catModuleHwVer",
		  "catModuleFwVer",
		  "catModuleSwVer",
		  "catModuleSerial",
		*/

		/*
		  "cCardIndex",
		  "cCardDescr",
		  "cCardSerial",
		  "cCardSlotNumber",
		  "cCardContainedByIndex",
		*/

		/*
		  "cL3Serial",
		  "cL3Model",
		  "cl3HwVer",
		  "cl3SwVer",
		*/

		/* Highest pri

		  "physClass",
		  "physSwVer",
		  "physDescr",
		  "physName",
		  "physSerial",
		  "physHwVer",
		  "physFwVer",
		  "physModelName",
		  "physParentRelPos",
		*/


		// Try to fetch the serial for the chassis
		if (nc.netboxDataFactory(nb).getSerial() == null) {
			List chassisIdList = sSnmp.getAll(nb.getOid("cChassisId"), true);
			if (chassisIdList != null && !chassisIdList.isEmpty()) {
				String[] s = (String[])chassisIdList.get(0);
				nc.netboxDataFactory(nb).setSerial(s[1]);
			}
		}

		// HwVer for the chassis
		if (nc.netboxDataFactory(nb).getHwVer() == null) {
			List chassisVerList = sSnmp.getAll(nb.getOid("cChassisVersion"), true);
			if (chassisVerList != null && !chassisVerList.isEmpty()) {
				String[] s = (String[])chassisVerList.get(0);
				nc.netboxDataFactory(nb).setHwVer(s[1]);
			}
		}

		// The card OIDs
		Map cardSlotNum = sSnmp.getAllMap(nb.getOid("cCardSlotNumber"));

		// The cL3 OIDs
		Map cl3Serial = sSnmp.getAllMap(nb.getOid("cL3Serial"), true);
		Map cl3Model = sSnmp.getAllMap(nb.getOid("cL3Model"), true);
		Map cl3HwVer = sSnmp.getAllMap(nb.getOid("cL3HwVer"), true);
		Map cl3FwVer = sSnmp.getAllMap(nb.getOid("cL3FwVer"), true);
		Map cl3SwVer = sSnmp.getAllMap(nb.getOid("cL3SwVer"), true);

		// The catModule OIDs
		Map catModModel = sSnmp.getAllMap(nb.getOid("catModuleModel"), true);
		Map catModHwVer = sSnmp.getAllMap(nb.getOid("catModuleHwVer"), true);
		Map catModFwVer = sSnmp.getAllMap(nb.getOid("catModuleFwVer"), true);
		Map catModSwVer = sSnmp.getAllMap(nb.getOid("catModuleSwVer"), true);
		Map catModSerial = sSnmp.getAllMap(nb.getOid("catModuleSerial"), true);

		// catModule*
		if (catModModel != null) {
			for (Iterator it = catModModel.entrySet().iterator(); it.hasNext();) {
				Map.Entry me = (Map.Entry)it.next();
				String module = (String)me.getKey();
				Log.d("CATMOD_OID", "Created module " + module + " from catModModel");
				mc.moduleFactory(module).setModel((String)me.getValue());
			}
		}

		if (catModHwVer != null) {
			for (Iterator it = catModHwVer.entrySet().iterator(); it.hasNext();) {
				Map.Entry me = (Map.Entry)it.next();
				String module = (String)me.getKey();
				mc.moduleFactory(module).setHwVer((String)me.getValue());
			}
		}

		if (catModFwVer != null) {
			for (Iterator it = catModFwVer.entrySet().iterator(); it.hasNext();) {
				Map.Entry me = (Map.Entry)it.next();
				String module = (String)me.getKey();
				mc.moduleFactory(module).setFwVer((String)me.getValue());
			}
		}

		if (catModSwVer != null) {
			for (Iterator it = catModSwVer.entrySet().iterator(); it.hasNext();) {
				Map.Entry me = (Map.Entry)it.next();
				String module = (String)me.getKey();
				mc.moduleFactory(module).setSwVer((String)me.getValue());
			}
		}

		if (catModSerial != null) {
			for (Iterator it = catModSerial.entrySet().iterator(); it.hasNext();) {
				Map.Entry me = (Map.Entry)it.next();
				String module = (String)me.getKey();
				mc.moduleFactory(module).setSerial((String)me.getValue());
			}
		}

		// cCard*
		if (cardSlotNum != null) {
			Map cardDescr = sSnmp.getAllMap(nb.getOid("cCardDescr"), true);
			Map cardSerial = sSnmp.getAllMap(nb.getOid("cCardSerial"), true);
			Map cardHwVer = sSnmp.getAllMap(nb.getOid("cCardHwVersion"), true);
			Map cardSwVer = sSnmp.getAllMap(nb.getOid("cCardSwVersion"), true);
			Map cardContainedByIndex = sSnmp.getAllMap(nb.getOid("cCardContainedByIndex"));

			for (Iterator it = cardSlotNum.entrySet().iterator(); it.hasNext();) {
				Map.Entry me = (Map.Entry)it.next();
				String cardIndex = (String)me.getKey();
				String module = (String)me.getValue();

				// We only include modules directly in the chassis, ie. containedByIndex=0
				if (cardContainedByIndex != null) {
					String containedBy = (String)cardContainedByIndex.get(cardIndex);
					if (containedBy != null && !"0".equals(containedBy)) continue;
				}

				try {
					if (Integer.parseInt(module) < 0) module = "0";
				} catch (NumberFormatException e) {
					System.err.println("Error, module is not a number: " + module);
					e.printStackTrace(System.err);
				}
				Log.d("CCARD_OID", "Created module " + module + " from cCard");
				Module m = mc.moduleFactory(module);
				
				if (cardDescr != null && m.getDescr() == null) m.setDescr((String)cardDescr.get(cardIndex));
				if (cardSerial != null && m.getSerial() == null) m.setSerial((String)cardSerial.get(cardIndex));
				if (cardHwVer != null && m.getHwVer() == null) m.setHwVer((String)cardHwVer.get(cardIndex));
				if (cardSwVer != null && m.getSwVer() == null) m.setSwVer((String)cardSwVer.get(cardIndex));
			}
		}

		// Find module translation using phys OIDs
		Map modTrans = new HashMap();
		{
			Map physClass = sSnmp.getAllMap(nb.getOid("physClass"), false, 0, true); // Ask for oidToModuleMap
			if (physClass != null) {
				Map oidToModuleMapping = (Map)physClass.remove("OidToModuleMapping");
				MultiMap classMap = util.reverse(physClass);
				// modules
				for (Iterator it = classMap.get("9").iterator(); it.hasNext();) {
					String id = (String)it.next();
					int module;
					try {
						if (oidToModuleMapping != null && oidToModuleMapping.containsKey(id)) {
							module = Integer.parseInt((String)oidToModuleMapping.get(id));						
						} else {
							module = Integer.parseInt(id);
							if (module < 1000 || (module%1000) != 0) continue;
							// if physName is supported, try to get module number from this
							String physNameOid = nb.getOid("physName");
							if (physNameOid != null) {
								boolean foundMod = false;
								List physNameL = sSnmp.getNext(physNameOid+"."+(module+1), 1, true, false);
								if (!physNameL.isEmpty()) {
									String portif = ((String[])physNameL.get(0))[1];
									String modulePattern = "((.*?)(\\d+))/(\\d+)(/(\\d+))?";
									if (portif.matches(modulePattern)) {
										Matcher m = Pattern.compile(modulePattern).matcher(portif);
										m.matches();
										int newModule = Integer.parseInt(m.group(3));
										modTrans.put(""+(module/1000), ""+newModule);
										foundMod = true;
									}
								}
								if (!foundMod) {
									physNameL = sSnmp.getNext(physNameOid+"."+(module), 1, true, false);
									if (!physNameL.isEmpty()) {
										String portif = ((String[])physNameL.get(0))[1];
										try {
											int newModule = Integer.parseInt(portif);
											modTrans.put(""+(module/1000), ""+newModule);
										} catch (NumberFormatException exp) {
											Log.e("CMOD_PHYSOID", "The module number '" + portif + "' is not a valid integer (" + nb.getSysname() + ")");
										}
									}
								}
							}
						}
					} catch (NumberFormatException e) {
					}
				}
			}
		}

		Log.d("MODTRANS", "" + modTrans);

		// cL3*
		{
			Set valid;
			if (cl3Serial != null && !(valid = getValidCL3Modules(cl3Serial)).isEmpty()) {
				for (Iterator it = valid.iterator(); it.hasNext();) {
					String module = (String)it.next();
					String nModule = modTrans.containsKey(module) ? (String)modTrans.get(module) : module;
					Log.d("CL3_OID", "Created module " + nModule + " from cL3: " + cl3Serial.get(module+"000"));				
					mc.moduleFactory(nModule).setSerial((String)cl3Serial.get(module+"000"));
				}
			}

			if (cl3Model != null && !(valid = getValidCL3Modules(cl3Model)).isEmpty()) {
				for (Iterator it = valid.iterator(); it.hasNext();) {
					String module = (String)it.next();
					String nModule = modTrans.containsKey(module) ? (String)modTrans.get(module) : module;
					mc.moduleFactory(nModule).setDescr((String)cl3Model.get(module+"000"));
				}
			}

			if (cl3HwVer != null && !(valid = getValidCL3Modules(cl3HwVer)).isEmpty()) {
				for (Iterator it = valid.iterator(); it.hasNext();) {
					String module = (String)it.next();
					String nModule = modTrans.containsKey(module) ? (String)modTrans.get(module) : module;
					mc.moduleFactory(nModule).setHwVer((String)cl3HwVer.get(module+"000"));
				}
			}

			if (cl3FwVer != null && !(valid = getValidCL3Modules(cl3FwVer)).isEmpty()) {
				for (Iterator it = valid.iterator(); it.hasNext();) {
					String module = (String)it.next();
					String nModule = modTrans.containsKey(module) ? (String)modTrans.get(module) : module;
					mc.moduleFactory(nModule).setFwVer((String)cl3FwVer.get(module+"000"));
				}
			}

			if (cl3SwVer != null && !(valid = getValidCL3Modules(cl3SwVer)).isEmpty()) {
				for (Iterator it = valid.iterator(); it.hasNext();) {
					String module = (String)it.next();
					String nModule = modTrans.containsKey(module) ? (String)modTrans.get(module) : module;
					mc.moduleFactory(nModule).setSwVer((String)cl3SwVer.get(module+"000"));
				}
			}
		}

		// The phys OIDs
		Map physClass = sSnmp.getAllMap(nb.getOid("physClass"), false, 0, true); // Ask for oidToModuleMap
		if (physClass != null) {
			Map physDescr = sSnmp.getAllMap(nb.getOid("physDescr"), true);
			Map physSerial = sSnmp.getAllMap(nb.getOid("physSerial"), true);
			Map physHwVer = sSnmp.getAllMap(nb.getOid("physHwVer"), true);
			Map physFwVer = sSnmp.getAllMap(nb.getOid("physFwVer"), true);
			Map physSwVer = sSnmp.getAllMap(nb.getOid("physSwVer"), true);
			Map physModelName = sSnmp.getAllMap(nb.getOid("physModelName"), true);
			//Map physParentPos = sSnmp.getAllMap(nb.getOid("physParentRelPos"), true);

			/*
			  PhysicalClass
			  1:other
			  2:unknown
			  3:chassis
			  4:backplane
			  5:container
			  6:powerSupply
			  7:fan
			  8:sensor
			  9:module
			  10:port
			  11:stack
			*/
			Map oidToModuleMapping = (Map)physClass.remove("OidToModuleMapping");
			MultiMap classMap = util.reverse(physClass);
			
			// chassis
			for (Iterator it = util.intSortedSetFactory(classMap.get("3")).iterator(); it.hasNext();) {
				String id = (String)it.next();
				NetboxData nd = nc.netboxDataFactory(nb);
				if (nd.getSerial() == null && physSerial != null && physSerial.containsKey(id)) nd.setSerial((String)physSerial.get(id));
				if (physHwVer != null && physHwVer.containsKey(id)) nd.setHwVer((String)physHwVer.get(id));
				if (physFwVer != null && physFwVer.containsKey(id)) nd.setFwVer((String)physFwVer.get(id));
				if (physSwVer != null && physSwVer.containsKey(id)) nd.setSwVer((String)physSwVer.get(id));
				break; // Only do first
			}

			// modules
			for (Iterator it = classMap.get("9").iterator(); it.hasNext();) {
				String id = (String)it.next();
				int module;
				try {
					if (oidToModuleMapping != null && oidToModuleMapping.containsKey(id)) {
						module = Integer.parseInt((String)oidToModuleMapping.get(id));						
					} else {
						module = Integer.parseInt(id);
						if (module < 1000 || (module%1000) != 0) continue;
						module /= 1000;
					}
				} catch (NumberFormatException e) {
					System.err.println("Working with " + nb + ", NumberFormatException: " + e);
					e.printStackTrace(System.err);
					continue;
				}
				if (module < 0) module = 0;
				if (modTrans.containsKey(""+module)) module = Integer.parseInt((String)modTrans.get(""+module));
				if (mc.getModule(module) == null && !modTrans.containsKey(""+module)) {
					// Not allowed to create module
					Log.w("CMOD_PHYSOID", "Module " + module + " does not exist on netbox " + nb.getSysname() + ", skipping");
					continue;
				}
				Log.d("CMOD_PHYSOID", "Created module " + module + " from Phys: " + physSerial.get(id));
				Module m = mc.moduleFactory(module);

				if (physSerial != null && physSerial.containsKey(id) && m.getSerial() == null) m.setSerial((String)physSerial.get(id));
				if (physHwVer != null && physHwVer.containsKey(id) && m.getHwVer() == null) m.setHwVer((String)physHwVer.get(id));
				if (physFwVer != null && physFwVer.containsKey(id) && m.getFwVer() == null) m.setFwVer((String)physFwVer.get(id));
				if (physSwVer != null && physSwVer.containsKey(id) && m.getSwVer() == null) m.setSwVer((String)physSwVer.get(id));

				if (physModelName != null && physModelName.containsKey(id) && m.getModel() == null) m.setModel((String)physModelName.get(id));
				if (physDescr != null && physDescr.containsKey(id) && m.getDescr() == null) m.setDescr((String)physDescr.get(id));
			}				
		}

		Set moduleSet = mc.getModuleSet();
		if (!moduleSet.isEmpty()) {
			for (Iterator it = moduleSet.iterator(); it.hasNext();) {
				String module = (String)it.next();
				mmc.moduleUp(nb, module);
			}
			//System.err.println("modulesUp: " + moduleSet);
			mmc.commit();
			return true;
		}
		return false;
	}

	private Set getValidCL3Modules(Map m) {
		Set valid = new HashSet();
		for (Iterator it = m.entrySet().iterator(); it.hasNext();) {
			Map.Entry me = (Map.Entry)it.next();
			String module = (String)me.getKey();
			String val = (String)me.getValue();
			if (val == null || val.length() == 0 || "unknown".equalsIgnoreCase(val)) continue;
			try {
				int i = Integer.parseInt(module);
				if ((i % 1000) == 0) valid.add(Integer.toString(i / 1000));
			} catch (NumberFormatException e) {
			}
		}
		return valid;
	}

	private static boolean isNumber(String s) {
		try {
			Integer.parseInt(s);
		} catch (NumberFormatException e) {
			return false;
		}
		return true;
	}

}
