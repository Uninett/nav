package no.ntnu.nav.getDeviceData.dataplugins.Gwport;

import java.util.*;
import java.sql.*;

import no.ntnu.nav.logger.*;
import no.ntnu.nav.Database.*;
import no.ntnu.nav.util.*;
import no.ntnu.nav.getDeviceData.Netbox;
import no.ntnu.nav.getDeviceData.dataplugins.*;
import no.ntnu.nav.getDeviceData.dataplugins.Module.ModuleHandler;

/**
 * DataHandler plugin for getDeviceData; provides an interface for storing
 * router data, which includes modules, gwports, prefixes and vlans.
 *
 * @see GwportContainer
 */

public class GwportHandler implements DataHandler {

	private static final boolean DEBUG_OUT = false;

	private static Map moduleMap;

	private static Map vlanMap;
	//private static Map prefixMap;
	

	/**
	 * Fetch initial data from module/gwport/prefix/vlan tables.
	 */
	public synchronized void init(Map persistentStorage) {
		if (persistentStorage.containsKey("initDone")) return;
		persistentStorage.put("initDone", null);

		vlanMap = Collections.synchronizedMap(new HashMap());

		/*
		Map m;
		ResultSet rs;
		long dumpBeginTime,dumpUsedTime;

		Log.setDefaultSubsystem("GwportHandler");

		try {
			// module, gwport, prefix, vlan
			dumpBeginTime = System.currentTimeMillis();
			m = Collections.synchronizedMap(new HashMap());
			rs = Database.query("SELECT serial,hw_ver,sw_ver,moduleid,module,descr,gwportid,ifindex,interface,masterindex,speed,ospf,prefixid,gwip,hsrp,host(netaddr) AS netaddr,masklen(netaddr) AS masklen,vlanid,vlan,nettype,orgid,usageid,netident,description FROM device JOIN module USING(deviceid) LEFT JOIN gwport USING(moduleid) LEFT JOIN gwportprefix USING(gwportid) LEFT JOIN prefix USING(prefixid) LEFT JOIN vlan USING(vlanid) ORDER BY moduleid,gwportid");
			while (rs.next()) {
				// Create module
				GwModule gwm = new GwModule(rs.getString("serial"), rs.getString("hw_ver"), rs.getString("sw_ver"), rs.getInt("module"));
				gwm.setDeviceid(rs.getInt("deviceid"));
				gwm.setModuleid(rs.getInt("moduleid"));
				gwm.setDescr(rs.getString("descr"));

				int moduleid = rs.getInt("moduleid");
				if (rs.getString("ifindex") != null && rs.getString("ifindex").length() > 0) {
					do {
						// Create vlan
						Vlan vlan = (Vlan)vlanMap.get(rs.getString("vlanid"));
						if (vlan == null) {
							vlan = rs.getString("vlan") == null ? gwm.vlanFactory(rs.getString("netident")) :
								gwm.vlanFactory(rs.getString("netident"), rs.getInt("vlan"));
							vlan.setVlanid(rs.getInt("vlanid"));
							vlan.setNettype(rs.getString("nettype"));
							vlan.setOrgid(rs.getString("orgid"));
							vlan.setUsageid(rs.getString("usageid"));
							vlan.setDescription(rs.getString("description"));

							vlanMap.put(rs.getString("vlanid"), vlan);
						} else {
							errl("FOUND DUP VLAN! " + vlan);
						}

						// Create gwport
						Gwport gwp = gwm.gwportFactory(rs.getString("ifindex"), rs.getString("interface"));
						gwp.setGwportid(rs.getInt("gwportid"));
						gwp.setMasterindex(rs.getInt("masterindex"));
						gwp.setSpeed(rs.getDouble("speed"));
						if (rs.getString("ospf") != null) gwp.setOspf(rs.getInt("ospf"));

						int gwportid = rs.getInt("gwportid");
						do {
							// Create prefices
							Prefix prefix = gwp.prefixFactory(rs.getString("gwip"), rs.getBoolean("hsrp"), rs.getString("netaddr"), rs.getInt("masklen"), vlan);
							prefix.setPrefixid(rs.getInt("prefixid"));

						} while (rs.next() && rs.getInt("gwportid") == gwportid);
							
					} while (rs.next() && rs.getInt("moduleid") == moduleid);
					rs.previous();
				}

				String key = rs.getString("netboxid")+":"+gwm.getKey();
				m.put(key, gwm);
			}

			moduleMap = m;
			dumpUsedTime = System.currentTimeMillis() - dumpBeginTime;
			Log.d("INIT", "Dumped swport in " + dumpUsedTime + " ms");

		} catch (SQLException e) {
			Log.e("INIT", "SQLException: " + e.getMessage());
		}
		*/

	}

	/**
	 * Return a DataContainer object used to return data to this
	 * DataHandler.
	 */
	public DataContainer dataContainerFactory() {
		return new GwportContainer(this);
	}
	
	/**
	 * Store the data in the DataContainer in the database.
	 */
	public void handleData(Netbox nb, DataContainer dc) {
		if (!(dc instanceof GwportContainer)) return;
		GwportContainer gc = (GwportContainer)dc;
		if (!gc.isCommited()) return;

		// Let ModuleHandler update the module table first
		ModuleHandler mh = new ModuleHandler();
		mh.handleData(nb, dc);

		Log.setDefaultSubsystem("GwportHandler");

		errl("Gwports for " + nb);


		// First we need to update vlanMap so we can do proper
		// auto-determination of nettype This requires two passes over all
		// vlans; one to remove old entries from vlanMap and one to
		// add the new ones.
		/*
		for (Iterator gwModules = gc.getGwModules(); gwModules.hasNext();) {
			GwModule gwm = (GwModule)gwModules.next();
			for (Iterator gwPorts = gwm.getGwports(); gwPorts.hasNext();) {
				Gwport gwp = (Gwport)gwPorts.next();
				for (Iterator gwportPrefices = gwp.getGwportPrefices(); gwportPrefices.hasNext();) {
					Vlan vl = ((Gwportprefix)gwportPrefices.next()).getVlan();

					// mm maps a netboxid to a set of ifindexes on this vlan
					MultiMap mm;
					if ( (mm=(MultiMap)vlanMap.get(p.getNetaddr())) == null) vlanMap.put(p.getNetaddr(), mm = new HashMultiMap());
					mm.remove(nb.getNetboxidS());
				}
			}
		}
		for (Iterator gwModules = gc.getGwModules(); gwModules.hasNext();) {
			GwModule gwm = (GwModule)gwModules.next();
			for (Iterator gwPorts = gwm.getGwports(); gwPorts.hasNext();) {
				Gwport gwp = (Gwport)gwPorts.next();
				for (Iterator gwportPrefices = gwp.getGwportPrefices(); gwportPrefices.hasNext();) {
					Vlan vl = ((Gwportprefix)gwportPrefices.next()).getVlan();
					boolean hsrp = ((Gwportprefix)gwportPrefices.next()).getHsrp();
					MultiMap mm = (MultiMap)prefixMap.get(p.getNetaddr());
					mm.put(nb.getNetboxidS(), (hsrp?"1":"0")+gwp.getIfindex());
				}
			}
		}
		*/
		
		// Dump old data from DB
		try {
			ResultSet rs;

			Map prefixDbMap = new HashMap();
			rs = Database.query("SELECT prefixid,netaddr AS cidr,host(netaddr) AS netaddr,masklen(netaddr) AS masklen,vlanid FROM prefix");
			while (rs.next()) {
				Vlan vl = new Vlan(null);
				vl.setVlanid(rs.getInt("vlanid"));
				Prefix p = new Prefix(rs.getString("netaddr"), rs.getInt("masklen"), vl);
				p.setPrefixid(rs.getInt("prefixid"));
				prefixDbMap.put(rs.getString("cidr"), p);
			}

			Map gwpDbMap = new HashMap();
			rs = Database.query("SELECT gwportid,gwip,hsrp,netaddr FROM gwportprefix JOIN prefix USING(prefixid)");
			while (rs.next()) {
				Prefix p = (Prefix)prefixDbMap.get(rs.getString("netaddr"));
				Gwportprefix gp = new Gwportprefix(rs.getString("gwip"), rs.getBoolean("hsrp"), p);
				gwpDbMap.put(rs.getString("gwip"), gp);
			}

			// module, gwport, prefix, vlan
			Map moduleMap = new HashMap();
			Map vlanDbMap = new HashMap();
			rs = Database.query("SELECT device.deviceid,serial,hw_ver,sw_ver,moduleid,module,descr,gwportid,ifindex,interface,masterindex,speed,ospf,prefix.prefixid,gwip,hsrp,host(netaddr) AS netaddr,masklen(netaddr) AS masklen,vlanid,vlan,nettype,vlan.orgid,usageid,netident,description FROM device JOIN module USING(deviceid) LEFT JOIN gwport USING(moduleid) LEFT JOIN gwportprefix USING(gwportid) LEFT JOIN prefix USING(prefixid) LEFT JOIN vlan USING(vlanid) JOIN netbox USING(netboxid) WHERE netboxid=" + nb.getNetboxid() + " ORDER BY moduleid,gwportid");
			while (rs.next()) {
				// Create module
				GwModule gwm = new GwModule(rs.getString("serial"), rs.getString("hw_ver"), rs.getString("sw_ver"), rs.getInt("module"));
				gwm.setDeviceid(rs.getInt("deviceid"));
				gwm.setModuleid(rs.getInt("moduleid"));
				gwm.setDescr(rs.getString("descr"));

				int moduleid = rs.getInt("moduleid");
				if (rs.getString("ifindex") != null && rs.getString("ifindex").length() > 0) {
					do {
						// Create vlan
						Vlan vlan = (Vlan)vlanDbMap.get(rs.getString("netident"));
						if (vlan == null) {
							vlan = rs.getString("vlan") == null ? gwm.vlanFactory(rs.getString("netident")) :
								gwm.vlanFactory(rs.getString("netident"), rs.getInt("vlan"));
							vlan.setVlanid(rs.getInt("vlanid"));
							vlan.setNettype(rs.getString("nettype"));
							vlan.setOrgid(rs.getString("orgid"));
							vlan.setUsageid(rs.getString("usageid"));
							vlan.setDescription(rs.getString("description"));

							vlanDbMap.put(rs.getString("netident"), vlan);
						} else {
							errl("FOUND DUP VLAN! " + vlan);
						}

						// Create gwport
						Gwport gwp = gwm.gwportFactory(rs.getString("ifindex"), rs.getString("interface"));
						gwp.setGwportid(rs.getInt("gwportid"));
						gwp.setMasterindex(rs.getInt("masterindex"));
						gwp.setSpeed(rs.getDouble("speed"));
						if (rs.getString("ospf") != null) gwp.setOspf(rs.getInt("ospf"));

						int gwportid = rs.getInt("gwportid");
						do {
							// Create prefices
							Prefix prefix = gwp.prefixFactory(rs.getString("gwip"), rs.getBoolean("hsrp"), rs.getString("netaddr"), rs.getInt("masklen"), vlan);
							prefix.setPrefixid(rs.getInt("prefixid"));

						} while (rs.next() && rs.getInt("gwportid") == gwportid);
						rs.previous();
												
					} while (rs.next() && rs.getInt("moduleid") == moduleid);
					rs.previous();
				}

				moduleMap.put(gwm.getKey(), gwm);
			}

			// DB dumped, check if we need to update
			for (Iterator gwModules = gc.getGwModules(); gwModules.hasNext();) {
				GwModule gwm = (GwModule)gwModules.next();

				// This one will always exists since it's handled by the module plugin
				GwModule oldgwm = (GwModule)moduleMap.get(gwm.getKey());
				if (oldgwm == null) {
					Log.e("HANDLE", "Old GwModule not found, this cannot happen, contact nav support!");
					return;
				}

				errl("  GwModule: " + gwm);
				
				for (Iterator gwPorts = gwm.getGwports(); gwPorts.hasNext();) {
					Gwport gwp = (Gwport)gwPorts.next();
					
					Gwport oldgwp = oldgwm.getGwport(gwp.getIfindex());
					String gwportid;
					if (oldgwp == null) {
						// Insert new
						Log.d("NEW_GWPORT", "Creating gwport: " + gwp);

						String masterindex = null;

						String[] ins = {
							"gwportid", "",
							"moduleid", oldgwm.getModuleidS(),
							"ifindex", gwp.getIfindex(),
							"link", gwp.getLinkS(),
							"masterindex", masterindex,
							"interface", gwp.getInterf(),
							"speed", gwp.getSpeedS(),
							"ospf", gwp.getOspfS()
						};
						gwportid = Database.insert("gwport", ins, null);

					} else {
						gwportid = oldgwp.getGwportidS();
						//if (!gwp.equalsGwport(oldgwp) || gwp.getModuleid() != oldgwp.getModuleid()) {
						if (!gwp.equalsGwport(oldgwp)) {
							// Vi må oppdatere
							Log.d("UPDATE_GWPORT", "Update gwportid: "+gwportid+" ifindex="+gwp.getIfindex());

							String masterindex = null;

							String[] set = {
								"moduleid", oldgwm.getModuleidS(),
								"ifindex", gwp.getIfindex(),
								"link", gwp.getLinkS(),
								"masterindex", masterindex,
								"interface", gwp.getInterf(),
								"speed", gwp.getSpeedS(),
								"ospf", gwp.getOspfS()
							};
							String[] where = {
								"gwportid", gwportid
							};
							Database.update("gwport", set, where);
						}
					}

					errl("    Gwport: " + gwp);

					for (Iterator gwportPrefices = gwp.getGwportPrefices(); gwportPrefices.hasNext();) {
						Gwportprefix gp = (Gwportprefix)gwportPrefices.next();

						String gwip = gp.getGwip();
						boolean hsrp = gp.getHsrp();
						Prefix p = gp.getPrefix();
						Vlan vl = p.getVlan();

						// First create/update the vlan
						Vlan dbvlan = (Vlan)vlanDbMap.get(vl.getNetident());
						String vlanid;
						if (dbvlan == null) {
							// Insert new
							Log.d("NEW_VLAN", "Creating vlan: " + vl);
							
							String[] ins = {
								"vlanid", "",
								"vlan", vl.getVlanS(),
								"nettype", vl.getNettype(),
								"orgid", vl.getOrgid(),
								"usageid", vl.getUsageid(),
								"netident", vl.getNetident(),
								"description", vl.getDescription()
							};
							vlanid = Database.insert("vlan", ins, null);
							vl.setVlanid(vlanid);
							vlanDbMap.put(vl.getNetident(), vl);
							
						} else {
							vlanid = dbvlan.getVlanidS();
							if (!vl.equalsVlan(dbvlan)) {
								// Vi må oppdatere
								Log.d("UPDATE_VLAN", "Update vlan " + vl);
								String[] set = {
									"vlan", vl.getVlanS(),
									"nettype", vl.getNettype(),
									"orgid", vl.getOrgid(),
									"usageid", vl.getUsageid(),
									"netident", vl.getNetident(),
									"description", vl.getDescription()
								};
								String[] where = {
									"vlanid", vlanid
								};
								Database.update("vlan", set, where);
							}
						}

						// Then gwportprefix / prefix
						Gwportprefix oldgp = oldgwp == null ? null : oldgwp.getGwportprefix(gwip);
						String prefixid;
						if (oldgp == null && !prefixDbMap.containsKey(p.getCidr())) {
							// Insert new
							Log.d("NEW_PREFIX", "Creating vlan: " + vl);
							
							String[] ins = {
								"prefixid", "",
								"netaddr", p.getCidr(),
								"vlanid", vlanid
							};
							prefixid = Database.insert("prefix", ins, null);
							p.setPrefixid(prefixid);
							prefixDbMap.put(p.getCidr(), p);

							String[] ins2 = {
								"gwportid", gwportid,
								"prefixid", prefixid,
								"gwip", gp.getGwip(),
								"hsrp", gp.getHsrp()?"t":"f"
							};
							Database.insert("gwportprefix", ins2);
							
						} else if (oldgp == null && !gwpDbMap.containsKey(gp.getGwip())) {
							// Insert into gwportprefix
							Log.d("APPEND_TO_PREFIX", "Prefix: " + p);
							
							String[] ins = {
								"gwportid", gwportid,
								"prefixid", ((Prefix)prefixDbMap.get(p.getCidr())).getPrefixidS(),
								"gwip", gp.getGwip(),
								"hsrp", gp.getHsrp()?"t":"f"
							};
							Database.insert("gwportprefix", ins);
						} else {
							// oldgp == null -> we must update prefix/gwportprefix
							// oldgp != null -> only update prefix/gwportprefix if changed
							oldgp = (Gwportprefix)gwpDbMap.get(gp.getGwip());
							Prefix oldp = (Prefix)prefixDbMap.get(p.getCidr());

							if (!p.equalsPrefix(oldp)) {
								// Update prefix
								Log.d("UPDATE_PREFIX", "Update prefix " + p);
								String[] set = {
								"netaddr", p.getCidr(),
								"vlanid", vlanid
								};
								String[] where = {
									"prefixid", oldp.getPrefixidS()
								};
								Database.update("prefix", set, where);
							}

							if (!gp.equalsGwportprefix(oldgp)) {
								// Update gwportprefix
								Log.d("UPDATE_GWPORTPREFIX", "Update gwportprefix " + gp);
								String[] set = {
									"gwportid", gwportid,
									"prefixid", oldp.getPrefixidS(),
									"hsrp", gp.getHsrp()?"t":"f"
								};
								String[] where = {
									"gwip", gp.getGwip()
								};
								Database.update("gwportprefix", set, where);
							}
						}


						/*
						if (vl.getNettype().equals("unknown")) {
							String nettype;

							// mm maps a netboxid to a set of ifindexes on this prefix
							MultiMap mm = (MultiMap)prefixMap.get(p.getNetaddr());
							
							// Now we can do auto-determination of nettype; we need to sum all ifindeces on the prefix
							int numGwp = 0;
							boolean hsrp = false;
							for (Iterator it = mm.values().iterator(); it.hasNext();) {
								Set ifSet = (Set)it.next();
								for (Iterator it2 = ifSet.values().iterator(); it2.hasNext();) {
								if (((String)it2.next()).charAt(0) == '1') hsrp = true;
								}
								numGwp += ((Set)it.next()).size();
							}

							
							if (numGwp == 0) {
								// This can't happen
								Log.e("HANDLE", "Prefix without any gwports, this cannot happen, contact nav support!");
								continue;
							}
							// Only one gwport = lan
							else if (numGwp == 1) {
								nettype = "lan";
							}
							// More than one gwport + hsrp = lan
							else if (hsrp && numGwp > 1) {
								nettype = "lan";
							}
							// Two gwports from different routers = link
							else if (numGwp == 2 && mm.size() > 1) {
								nettype = "link";
							}
							// More than two gwports without hsrp = stam
							else {
								nettype = "stam";
							}

							vl.setNettype(nettype);
						}
						*/

						
						


						errl("      Gwip: " + gwip);
						errl("      Hsrp: " + hsrp);
						errl("      Prefix: " + p);
						errl("      Vlan: " + vl);
					}
				}
			}
						


		} catch (SQLException e) {
			Log.e("HANDLE", "SQLException: " + e.getMessage());
			e.printStackTrace(System.err);
		}
	}

	private static void errl(Object o) {
		if (DEBUG_OUT) System.err.println(o);
	}

}
