package no.ntnu.nav.getDeviceData.deviceplugins.MibIISw;

import java.util.*;

import no.ntnu.nav.logger.*;
import no.ntnu.nav.SimpleSnmp.*;
import no.ntnu.nav.ConfigParser.*;
import no.ntnu.nav.util.*;
import no.ntnu.nav.event.*;
import no.ntnu.nav.netboxinfo.*;
import no.ntnu.nav.getDeviceData.Netbox;
import no.ntnu.nav.getDeviceData.deviceplugins.*;
import no.ntnu.nav.getDeviceData.dataplugins.*;
import no.ntnu.nav.getDeviceData.dataplugins.Netbox.*;
import no.ntnu.nav.getDeviceData.dataplugins.Module.*;
import no.ntnu.nav.getDeviceData.dataplugins.Swport.*;
import no.ntnu.nav.getDeviceData.dataplugins.ModuleMon.*;

/**
 * <p>
 * DeviceHandler for collecting the standard MIB-II switch port OIDs.
 * </p>
 *
 * <p>
 * This plugin handles the following OID keys:
 * </p>
 *
 * <ul>
 *  <li>From MIB-II</li>
 *  <ul>
 *   <li>sysname</li>
 *   <li>sysUpTime</li>
 *   <li>ifIndex (not used)</li>
 *   <li>ifSpeed</li>
 *   <li>ifAdminStatus</li>
 *   <li>ifOperStatus</li>
 *   <li>ifDescr</li>
 *   <li>moduleMon</li>
 *  </ul>
 * </ul>
 * </p>
 *
 */

public class MibIISw implements DeviceHandler
{
	public static final int HANDLE_PRI_MIB_II_SW = -30;

	private static String[] canHandleOids = {
		"sysname",
		"sysUpTime",
		"ifSpeed",
		"ifAdminStatus",
		"ifOperStatus",
		"ifDescr",
		"moduleMon",
		"vtpVlanState",
	};

	private SimpleSnmp sSnmp;

	public int canHandleDevice(Netbox nb) {
		int v = nb.isSupportedOids(canHandleOids) ? HANDLE_PRI_MIB_II_SW : NEVER_HANDLE;
		Log.d("MIB_II_SW_CANHANDLE", "CHECK_CAN_HANDLE", "Can handle device: " + v);
		return v;
	}

	public void handleDevice(Netbox nb, SimpleSnmp sSnmp, ConfigParser cp, DataContainers containers) throws TimeoutException
	{
		Log.setDefaultSubsystem("MIB_II_SW_DEVHANDLER");
		
		NetboxContainer nc;
		SwportContainer sc;
		ModuleMonContainer mmc;
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

			dc = containers.getContainer("SwportContainer");
			if (dc == null) {
				Log.w("NO_CONTAINER", "No SwportContainer found, plugin may not be loaded");
				return;
			}
			if (!(dc instanceof SwportContainer)) {
				Log.w("NO_CONTAINER", "Container is not an SwportContainer! " + dc);
				return;
			}
			sc = (SwportContainer)dc;

			dc = containers.getContainer("ModuleMonContainer");
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

		processMibII(nb, netboxid, ip, cs_ro, type, nc, sc, mmc);

		// Commit data
		sc.commit();
	}

	private void processMibII(Netbox nb, String netboxid, String ip, String cs_ro, String typeid, NetboxContainer nc, SwportContainer sc, ModuleMonContainer mmc) throws TimeoutException
	{
		if (nb.getNumInStack() > 1) {
			// Do moduleMon
			// PS40 must use a special OID
			Map ifindexMap = null;
			String baseOidAlt = null;
			if (nb.getOid("3cPS40PortState") != null) {
				List portList = sSnmp.getAll(nb.getOid("3cPS40PortState"));
				if (portList != null) {
					ifindexMap = new HashMap();
					baseOidAlt = nb.getOid("3cPS40PortState");
					for (Iterator it = portList.iterator(); it.hasNext();) {
						String[] s = (String[])it.next();
						String[] mp = s[0].split("\\.");
						String ifindex = mp[0] + (Integer.parseInt(mp[1])<10?"0":"") + mp[1];
						ifindexMap.put(ifindex, s[0]);
					}
				}
			}
			String baseOid = nb.getOid("moduleMon");
			String hpMemberStatusOid = nb.getOid("hpStackStatsMemberOperStatus");
			if (hpMemberStatusOid != null) {
				Set modulesUp = new HashSet();
				Map moduleStatus = new HashMap();
				List statusList = sSnmp.getAll(hpMemberStatusOid);
				for (Iterator it = statusList.iterator(); it.hasNext();) {
					String[] s = (String[])it.next();
					String module;
					if (s.length < 4) {
						System.err.println("Error in ModuleMon, module not found!");
						module = s[0];
					} else {
						module = s[3];
					}
					int status = Integer.parseInt(s[1]);
					moduleStatus.put(module, ""+status);
					if (status == 10 || status == 12) {
						// Up
						modulesUp.add(module);
					}
				}
				for (Iterator it = mmc.getQueryIfindices(netboxid); it.hasNext();) {
					String[] s = (String[])it.next();
					String ifindex = s[0];
					String module = s[1];
					if (modulesUp.contains(module)) {
						mmc.moduleUp(nb, module);
					} else {
						Log.d("MODULE_MON", "HP Module " + module + ", ifindex " + ifindex + " on " + nb.getSysname() + " is down ("+moduleStatus.get(module)+")");
						System.err.println("HP module down, " + nb + ", " + module + ", " + ifindex + ", " + modulesUp + ", " + moduleStatus);
						sSnmp.ignoreModule(module);
						mmc.rescheduleNetbox(nb, module, "hpStackStatsMemberOperStatus");
					}
				}
				mmc.commit();
			} else
			if (baseOid != null) {
				for (Iterator it = mmc.getQueryIfindices(netboxid); it.hasNext();) {
					String[] s = (String[])it.next();
					String ifindex = s[0];
					String ifindexOid = sSnmp.extractIfIndexOID(ifindex);
					String module = s[1];
					try {
						sSnmp.onlyAskModule(module);
						String askOid = (ifindexMap != null && ifindexMap.containsKey(ifindexOid) ? baseOidAlt + "." + ifindexMap.get(ifindexOid) : baseOid + "." + ifindexOid);
						List l = sSnmp.getNext(askOid, 1, false, false);
						if (l != null && !l.isEmpty()) {
							// We got a response
							if (nb.getNumInStack() == 2) {
								String moduleWithIP = NetboxInfo.getSingleton(nb.getNetboxidS(), null, "ModuleWithIP");
								if (moduleWithIP != null) {
									String ifind = mmc.ifindexForModule(nb.getNetboxidS(), moduleWithIP);
									// Since there are only two modules we are surely talking to the one with the IP
									if (ifind != null) ifindex = ifind;
									else System.err.println("Wops, ifind is null for " + nb.getSysname() + " moduleWithIP: " + moduleWithIP);
								}
							}
							mmc.moduleUp(nb, module);
						} else {
							// Assume down
							Log.d("MODULE_MON", "Module " + module + ", ifindex " + ifindex + " on " + nb.getSysname() + " returned no values");						
							System.err.println("Module down, " + nb + ", " + module + ", " + ifindex + ", " + askOid + ", " + ifindexMap + ", " + l);
							sSnmp.ignoreModule(module);
							mmc.rescheduleNetbox(nb, module, "moduleMon");
						}
					} catch (TimeoutException te) {
						// Assume the module is down
						Log.i("MODULE_MON", "Module " + module + ", ifindex " + ifindex + " on " + nb.getSysname() + " is not responding");
						sSnmp.ignoreModule(module);
					}
				}
				sSnmp.onlyAskModule(null);
				mmc.commit();
			} else {
				Log.w("MODULE_MON", "Netbox " + nb.getSysname() + ", type " + nb.getType() + " does not support the moduleMon OID, skipping");
			}
		}

		List l;
		// If vtpVlanState is supported, collect VLANs
		if (nb.getOid("vtpVlanState") != null) {
			l = sSnmp.getAll(nb.getOid("vtpVlanState")+".1");
			if (l != null) {
				NetboxData nd = nc.netboxDataFactory(nb);
				for (Iterator it = l.iterator(); it.hasNext();) {
					String[] s = (String[])it.next();
					try {
						nd.addVtpVlan(Integer.parseInt(s[0]));
					} catch (NumberFormatException e) {
						e.printStackTrace(System.err);
					}
				}
				nc.commit();
			}
		}

		// Collect serial for chassis
		l = sSnmp.getNext(nb.getOid("ifSerial"), 1, true, false);
		if (l != null && !l.isEmpty()) {
			String[] s = (String[])l.get(0);
			Log.d("HANDLE", "Setting serial for netbox ("+nb.getSysname()+"): " + s[1]);
			nc.netboxDataFactory(nb).setSerial(s[1]);
			nc.commit();
		}

		// Collect sysname and uptime
		l = sSnmp.getNext(nb.getOid("sysname"), 1, true, false);
		if (l != null && !l.isEmpty()) {
			// sysname (dnsname) should start with the collected sysname
			String[] s = (String[])l.get(0);
			String netboxSysname = s[1];
			if (!nb.getSysname().startsWith(netboxSysname)) {
				// Log
				Log.i("HANDLE", "Sysname (DNS) ("+nb.getSysname()+") does not start with the collected sysname ("+netboxSysname+")");

				Map varMap = new HashMap();
				varMap.put("alerttype", "dnsMismatch");
				varMap.put("dnsname", String.valueOf(nb.getSysname()));
				varMap.put("sysname", String.valueOf(s[1]));
				EventQ.createAndPostEvent("getDeviceData", "eventEngine", nb.getDeviceid(), nb.getNetboxid(), 0, "info", Event.STATE_NONE, 0, 0, varMap);
			} else {
				Log.d("HANDLE", "Correct: Sysname (DNS) ("+nb.getSysname()+") starts with the collected sysname ("+s[1]+")");
			}

			// Put sysname in netboxinfo
			NetboxInfo.put(nb.getNetboxidS(), null, "sysname", netboxSysname);
		}

		l = sSnmp.getNext(nb.getOid("sysUpTime"), 1, false, false);
		if (l != null && !l.isEmpty()) {
			String[] s = (String[])l.get(0);
			long ticks = Long.parseLong(s[1]);
			//if (ticks > 0 && ticks != 4294967295l) {
			// Ticks must be > 0 and < 30 years
			if (ticks > 0 && ticks != 4294967295l && ticks < 94608000000l) {
				nc.netboxDataFactory(nb).setUptimeTicks(ticks);
				nc.commit();
			}
		}

		Set skipIfindexSet = new HashSet();

		// Set speed
		List speedList = sSnmp.getAll(nb.getOid("ifSpeed"));
		if (speedList != null) {
			for (Iterator it = speedList.iterator(); it.hasNext();) {
				String[] s = (String[])it.next();

				// Ugly hack for GWs, waiting for new table port
				if ("GW".equals(nb.getCat())) {
					skipIfindexSet.add(s[0]);
					sc.ignoreSwport(s[0]);
					continue;
				}
				
				long speedNum;
				try {
					speedNum = Long.parseLong(s[1]) / 1000000;
					if (speedNum <= 0) {
						skipIfindexSet.add(s[0]);
						sc.ignoreSwport(s[0]);
					} else {
						Swport swp = sc.swportFactory(s[0]);
						swp.setSpeed(String.valueOf( speedNum ));
					}
				} catch (NumberFormatException e) {
					Log.w("PROCESS_HP", "netboxid: " + netboxid + " ifindex: " + s[0] + " NumberFormatException on speed: " + s[1]);
				}
			}
		}

		// Set interface, first we try IfName
		Map ifdescrMap = sSnmp.getAllMap(nb.getOid("ifDescr"), true);
		Map ifNameMap = sSnmp.getAllMap(nb.getOid("ifName"), true);

		if (ifdescrMap != null) {
			for (Iterator it = ifdescrMap.entrySet().iterator(); it.hasNext();) {
				Map.Entry me = (Map.Entry)it.next();
				String ifindex = (String)me.getKey();
				if (skipIfindexSet.contains(ifindex)) continue;
				String ifdescr = (String)me.getValue();
				String ifname = (ifNameMap != null ? (String)ifNameMap.get(ifindex) : null);
				Swport swp = sc.swportFactory(ifindex);

				// Some heuristics for choosing either ifdescr or ifname
				// We prefer ifname if it exists, unless ifdescr contains the string "Ethernet"
				String interf;
				if (ifdescr.indexOf("Ethernet") >= 0) {
					interf = ifdescr;
				} else {
					interf = (ifname != null && ifname.length() > 0 ? ifname : ifdescr);
				}

				swp.setInterface(interf);

				String vlanPattern = "VLAN (\\d+)";				
				if (ifdescr.matches(vlanPattern) ||
						interf.matches(vlanPattern) ||
						interf.startsWith("EO") ||
						interf.startsWith("Nu")) {
					sc.ignoreSwport(ifindex);
				}
			}
		}
		
		if ("GW".equals(nb.getCat())) return;
			
		Map operStatusMap = sSnmp.getAllMap(nb.getOid("ifOperStatus"));
		Map admStatusMap = sSnmp.getAllMap(nb.getOid("ifAdminStatus"));
		if (operStatusMap != null && admStatusMap != null) {
			for (Iterator it = operStatusMap.keySet().iterator(); it.hasNext();) {
				String ifindex = (String)it.next();
				if (skipIfindexSet.contains(ifindex)) continue;
				// Some 3Com units doesn't give all us all every time
				if (!admStatusMap.containsKey(ifindex) || !operStatusMap.containsKey(ifindex)) continue;
				Swport swp = sc.swportFactory(ifindex);

				try {
					int n = Integer.parseInt((String)admStatusMap.get(ifindex));
					char link = 'd'; // adm down
					if (n == 1) {
						// adm up
						n = Integer.parseInt((String)operStatusMap.get(ifindex));
						if (n == 1) link ='y'; // link up
						else link = 'n'; // link oper down
					}
					else if (n != 2 && n != 0) {
						Log.w("PROCESS_MIB_II_SW", "netboxid: " + netboxid + " ifindex: " + ifindex + " Unknown status code: " + n);
					}
					swp.setLink(link);
				} catch (NumberFormatException e) {
					Log.w("PROCESS_MIB_II_SW", "netboxid: " + netboxid + " ifindex: " + ifindex + " NumberFormatException for status code: " + admStatusMap.get(ifindex) + " / " + operStatusMap.get(ifindex));
				}
			}
		}

		// Fetch portname (ifAlias)
		List ifAliasList = sSnmp.getAll(nb.getOid("ifAlias"), true);
		if (ifAliasList != null) {
			for (Iterator it = ifAliasList.iterator(); it.hasNext();) {
				String[] s = (String[])it.next();
				String ifindex = s[0];
				String alias = s[1];

				Swport swp = sc.swportFactory(ifindex);
				swp.setPortname(alias);
			}
		}



		/*
		// Set interface, first we try IfName
		Map ifNameMap = sSnmp.getAllMap(nb.getOid("ifName"), true);
		if (ifNameMap != null) {
			for (Iterator it = ifNameMap.entrySet().iterator(); it.hasNext();) {
				Map.Entry me = (Map.Entry)it.next();
				String ifindex = (String)me.getKey();
				if (skipIfindexSet.contains(ifindex)) continue;
				String ifname = (String)me.getValue();
				
				Swport swp = sc.swportFactory(ifindex);
				swp.setInterface(ifname);
			}
		} else {
			// Type does not support ifName; instead use ifDescr
			Map ifdescrMap = sSnmp.getAllMap(nb.getOid("ifDescr"), true);
			if (ifdescrMap != null) {
				for (Iterator it = ifdescrMap.entrySet().iterator(); it.hasNext();) {
					Map.Entry me = (Map.Entry)it.next();
					String ifindex = (String)me.getKey();
					if (skipIfindexSet.contains(ifindex)) continue;
					String ifdescr = (String)me.getValue();
					
					Swport swp = sc.swportFactory(ifindex);
					swp.setInterface(ifdescr);
				}
			}
		}
		*/

		/*
		// If type supports portIfindex
		MultiMap portIfindexMap = util.reverse(sSnmp.getAllMap(nb.getOid("portIfIndex")));
		if (portIfindexMap != null) {
		for (Iterator it = portIfindexMap.keySet().iterator(); it.hasNext();) {
				String ifindex = (String)it.next();
				if (skipIfindexSet.contains(ifindex)) continue;

				String[] mp = ((String)portIfindexMap.get(ifindex).iterator().next()).split("\\.");
				
				Swport swp = sc.swportFactory(ifindex);
				swp.setInterface(mp[0] + "/" + mp[1]);
			}
		*/

	}

}
