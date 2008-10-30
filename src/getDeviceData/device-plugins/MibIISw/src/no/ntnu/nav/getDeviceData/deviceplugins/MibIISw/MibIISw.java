package no.ntnu.nav.getDeviceData.deviceplugins.MibIISw;

import java.util.ArrayList;
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
import no.ntnu.nav.event.Event;
import no.ntnu.nav.event.EventQ;
import no.ntnu.nav.getDeviceData.Netbox;
import no.ntnu.nav.getDeviceData.dataplugins.DataContainer;
import no.ntnu.nav.getDeviceData.dataplugins.DataContainers;
import no.ntnu.nav.getDeviceData.dataplugins.Module.ModuleContainer;
import no.ntnu.nav.getDeviceData.dataplugins.ModuleMon.ModuleMonContainer;
import no.ntnu.nav.getDeviceData.dataplugins.Netbox.NetboxContainer;
import no.ntnu.nav.getDeviceData.dataplugins.Netbox.NetboxData;
import no.ntnu.nav.getDeviceData.dataplugins.Swport.Swport;
import no.ntnu.nav.getDeviceData.dataplugins.Swport.SwportContainer;
import no.ntnu.nav.getDeviceData.deviceplugins.DeviceHandler;
import no.ntnu.nav.logger.Log;
import no.ntnu.nav.netboxinfo.NetboxInfo;

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
 *   <li>ifHighSpeed</li>
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
		"ifHighSpeed",
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
		ModuleContainer mc;
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

			dc = containers.getContainer("ModuleContainer");
			if (dc == null) {
				Log.w("NO_CONTAINER", "No ModuleContainer found, plugin may not be loaded");
				return;
			}
			if (!(dc instanceof ModuleContainer)) {
				Log.w("NO_CONTAINER", "Container is not a ModuleContainer! " + dc);
				return;
			}
			mc = (ModuleContainer)dc;

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

		processMibII(nb, netboxid, ip, cs_ro, type, nc, mc, sc, mmc);

		// Commit data
		sc.commit();
	}

	private void processMibII(Netbox nb, String netboxid, String ip, String cs_ro, String typeid, NetboxContainer nc, ModuleContainer mc, SwportContainer sc, ModuleMonContainer mmc) throws TimeoutException
	{
		if (nb.getNumInStack() > 1) {
			// Do moduleMon
			// PS40 must use a special OID
			Map ifindexMap = null;
			String baseOidAlt = null;
			if (nb.getOid("3cPS40PortState") != null) {
				baseOidAlt = nb.getOid("3cPS40PortState");
				ifindexMap = new HashMap();
				for (Iterator it = mmc.getQueryIfindices(netboxid); it.hasNext();) {
					Map.Entry me = (Map.Entry)it.next();
					String module = (String)me.getKey();
					List ifindexList = (List)me.getValue();
					for (Iterator ifIt = ifindexList.iterator(); ifIt.hasNext();) {
						String ifindex = (String)ifIt.next();
						if (ifindex.length() < 3) continue;
						String m = ifindex.substring(0, ifindex.length()-2);
						String p = ifindex.substring(ifindex.length()-2, ifindex.length());
						ifindexMap.put(ifindex, Integer.parseInt(m)+"."+Integer.parseInt(p));
					}
				}
			}
			String baseOid = nb.getOid("moduleMon");
			if (baseOid != null) {
				for (Iterator it = mmc.getQueryIfindices(netboxid); it.hasNext();) {
					Map.Entry me = (Map.Entry)it.next();
					String module = (String)me.getKey();
					List ifindexList = (List)me.getValue();
					boolean down = true;
					int cnt = 0;
					for (Iterator ifIt = ifindexList.iterator(); ifIt.hasNext() && down && cnt++ < 5;) {
						String ifindex = (String)ifIt.next();
						try {
							String askOid = (ifindexMap != null && ifindexMap.containsKey(ifindex) ? baseOidAlt + "." + ifindexMap.get(ifindex) + ".1" : baseOid + "." + ifindex);
							List l = sSnmp.getNext(askOid, 1, false, false);
							if (l != null && !l.isEmpty()) {
								// We got a response
								mmc.moduleUp(nb, module);
								down = false;
							} else {
								Log.d("MODULE_MON", "No response on askOid " + askOid + ", trying next (cnt: " + cnt + ")");
							}
						} catch (TimeoutException te) {
							// Assume the module is down
							mmc.moduleDown(nb, module);
							Log.i("MODULE_MON", "Module " + module + ", ifindex " + ifindex + " on " + nb.getSysname() + " is not responding");
							break;
						}
					}
					if (down) {
						// Assume down
						mmc.moduleDown(nb, module);
						Log.d("MODULE_MON", "Module " + module + " on " + nb.getSysname() + " returned no values");						
						List oidL = new ArrayList();
						oidL.add("moduleMon");
						if (baseOidAlt != null) oidL.add("3cPS40PortState");
						mmc.rescheduleNetbox(nb, module, oidL);
					}
				}
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
			if (!nb.getSysname().trim().toLowerCase().startsWith(netboxSysname.trim().toLowerCase())) {
				// Log
				Log.i("HANDLE", "Sysname (DNS) ("+nb.getSysname()+") does not start with the collected sysname ("+netboxSysname+")");

				Map varMap = new HashMap();
				varMap.put("alerttype", "dnsMismatch");
				varMap.put("dnsname", String.valueOf(nb.getSysname()));
				varMap.put("snmpsysname", String.valueOf(s[1]));
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
		Map highSpeedMap = sSnmp.getAllMap(nb.getOid("ifHighSpeed"));
		if (speedList != null) {
			for (Iterator it = speedList.iterator(); it.hasNext();) {
				String[] s = (String[])it.next();

				// Ugly hack for GWs, waiting for new table port
				if ("GW".equals(nb.getCat())) {
					skipIfindexSet.add(s[0]);
					sc.ignoreSwport(s[0]);
					continue;
				}
				
				double speedNum = 0.0;
				try {
					// If the ifSpeed value is maxed out (a 32 bit unsigned value), get the speed value from ifHighSpeed (if available)
					if (Long.parseLong(s[1]) == 4294967295L && highSpeedMap != null && highSpeedMap.containsKey(s[0])) {
						speedNum = Long.parseLong((String)highSpeedMap.get(s[0]));
						Log.d("PROCESS_MIB_II_SW", "Set gwport speed from ifHighSpeed for ifindex " + s[0]);
					} else {
						speedNum = Long.parseLong(s[1]) / 1000000;
					}
					// XXX: Ports with ifSpeed=0 do not have any concept of bandwidth, and will most likely not be a physical port or be able to carry any traffic (according to RFC 2233).  We ignore them here. 
					if (speedNum <= 0) {
						skipIfindexSet.add(s[0]);
						sc.ignoreSwport(s[0]);
					} else {
						Swport swp = sc.swportFactory(s[0]);
						swp.setSpeed(String.valueOf( speedNum ));
					}
				} catch (NumberFormatException e) {
					Log.w("PROCESS_MIB_II_SW", "netboxid: " + netboxid + " ifindex: " + s[0] + " NumberFormatException on speed: " + s[1]);
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

				// Some heuristics for choosing either ifdescr or ifname as interface string
				// We prefer ifname if it exists, unless ifdescr contains the substring "Ethernet" followed by at least 1 digit
				String interf;
				if (ifdescr.matches(".*[a-zA-Z]Ethernet.*[0-9]")) {
					interf = ifdescr;
				} else {
					interf = (ifname != null && ifname.length() > 0 ? ifname : ifdescr);
				}

				swp.setInterface(interf);

				// Some interfaces on Cisco devices are not physical ports, or are not eligible as switchports.  We ignore them.
				String vlanPattern = "VLAN\\s?(\\d+)";				
				if (ifdescr.toUpperCase().matches(vlanPattern) ||
						interf.toUpperCase().matches(vlanPattern) ||
						interf.startsWith("EO") ||
						interf.startsWith("Nu")) {
					sc.ignoreSwport(ifindex);
				}
			}
		}

		// Collect sysDescr
		List sysDescrList = sSnmp.getAll(nb.getOid("sysDescr"), true, false);
		if (sysDescrList != null) {
			for (Iterator it = sysDescrList.iterator(); it.hasNext();) {
				String[] s = (String[])it.next();
				String sysDescr = s[1];
				NetboxInfo.put(nb.getNetboxidS(), null, "sysDescr", sysDescr);

				String version = null;
				// Extract version
				int k=0;
				if ( (k=sysDescr.indexOf("Version")) >= 0) {
					k += "Version".length();
					int e = sysDescr.indexOf(",", k);
					int e2 = sysDescr.indexOf("\n", k);
					if (e <= k) e = sysDescr.length();
					if (e2 <= k) e2 = sysDescr.length();
					version =  sysDescr.substring(k, Math.min(e,e2));
				} else {
					Matcher m = Pattern.compile("V([0-9]+[a-zA-Z0-9.&&[^ ]]*)").matcher(sysDescr);
					if (m.find()) {	
						version = m.group(1);
					} else {
						m = Pattern.compile(" ([0-9]+\\.[a-zA-Z0-9.&&[^ ]]+)").matcher(sysDescr);
						if (m.find()) {	
							version = m.group(1);							
						}
					}
				}
				if (version != null) {
					version = version.trim();
					nc.netboxDataFactory(nb).setSwVer(version);
				}

				break;
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
