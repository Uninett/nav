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

	private static Map prefixDbMap;
	private static Map gwpDbMap;
	private static Map gwportidMap;

	// MultiMap from gwportid to gwip,prefixid
	//private static MultiMap gwipMap;
	//private static MultiMap prefixidMap;
	

	/**
	 * Fetch initial data from module/gwport/prefix/vlan tables.
	 */
	public synchronized void init(Map persistentStorage) {
		if (persistentStorage.containsKey("initDone")) return;
		persistentStorage.put("initDone", null);

		ResultSet rs;
		long dumpBeginTime,dumpUsedTime;

		Log.setDefaultSubsystem("GwportHandler");

		try {
			// gwportid -> netboxid + interface
			gwportidMap = Collections.synchronizedMap(new HashMap());
			rs = Database.query("SELECT gwport.gwportid,sysname,interface,hsrp FROM netbox JOIN module USING(netboxid) JOIN gwport USING(moduleid) LEFT JOIN gwportprefix ON (gwport.gwportid=gwportprefix.gwportid AND hsrp='t')");
			while (rs.next()) {
				gwportidMap.put(rs.getString("gwportid"), new String[] { rs.getString("sysname"), rs.getString("interface"), String.valueOf(rs.getBoolean("hsrp")) });
			}

			// Create vlanMap; only used locally to as the prefices stores references to these
			Map vlanMap = new HashMap();
			rs = Database.query("SELECT vlanid,vlan,nettype,orgid,usageid,netident,description FROM vlan");
			while (rs.next()) {
				// Create vlan
				Vlan vlan = (Vlan)vlanMap.get(rs.getString("vlanid"));
				if (vlan == null) {
					vlan = new Vlan(rs.getString("netident"), rs.getInt("vlan"));
					vlan.setVlanid(rs.getInt("vlanid"));
					vlan.setNettype(rs.getString("nettype"));
					vlan.setOrgid(rs.getString("orgid"));
					vlan.setUsageid(rs.getString("usageid"));
					vlan.setDescription(rs.getString("description"));
					
					vlanMap.put(rs.getString("vlanid"), vlan);
				}
			}				

			// Create prefixDbMap
			prefixDbMap = Collections.synchronizedMap(new HashMap());
			rs = Database.query("SELECT prefixid,netaddr AS cidr,host(netaddr) AS netaddr,masklen(netaddr) AS masklen,vlanid FROM prefix");
			while (rs.next()) {
				Vlan vl = (Vlan)vlanMap.get(rs.getString("vlanid"));
				Prefix p = new Prefix(rs.getString("netaddr"), rs.getInt("masklen"), vl);
				p.setPrefixid(rs.getInt("prefixid"));
				prefixDbMap.put(rs.getString("cidr"), p);
			}
			
			// Create gwpDbMap
			gwpDbMap = Collections.synchronizedMap(new HashMap());
			rs = Database.query("SELECT gwportid,gwip,hsrp,netaddr FROM gwportprefix JOIN prefix USING(prefixid)");
			while (rs.next()) {
				Prefix p = (Prefix)prefixDbMap.get(rs.getString("netaddr"));
				Gwportprefix gp = new Gwportprefix(rs.getString("gwip"), rs.getBoolean("hsrp"), p);
				p.addGwport(rs.getString("gwportid"));
				gwpDbMap.put(rs.getString("gwip"), gp);
			}

			// Fill moduleMap from module, gwport
			dumpBeginTime = System.currentTimeMillis();
			Map m = Collections.synchronizedMap(new HashMap());
			rs = Database.query("SELECT deviceid,serial,hw_ver,sw_ver,moduleid,netboxid,module,descr,gwportid,ifindex,interface,masterindex,speed,ospf,gwip FROM device JOIN module USING(deviceid) LEFT JOIN gwport USING(moduleid) LEFT JOIN gwportprefix USING(gwportid) ORDER BY moduleid,gwportid");
			while (rs.next()) {
				// Create module
				GwModule gwm = new GwModule(rs.getString("serial"), rs.getString("hw_ver"), rs.getString("sw_ver"), rs.getInt("module"));
				gwm.setDeviceid(rs.getInt("deviceid"));
				gwm.setModuleid(rs.getInt("moduleid"));
				gwm.setDescr(rs.getString("descr"));

				int moduleid = rs.getInt("moduleid");
				if (rs.getString("ifindex") != null && rs.getString("ifindex").length() > 0) {
					do {
						// Create gwport
						Gwport gwp = gwm.gwportFactory(rs.getString("ifindex"), rs.getString("interface"));
						gwp.setGwportid(rs.getInt("gwportid"));
						gwp.setMasterindex(rs.getInt("masterindex"));
						gwp.setSpeed(rs.getDouble("speed"));
						if (rs.getString("ospf") != null) gwp.setOspf(rs.getInt("ospf"));

						int gwportid = rs.getInt("gwportid");
						do {
							// Add prefices
							String gwip = rs.getString("gwip");
							gwp.addGwportprefix(gwip, (Gwportprefix)gwpDbMap.get(gwip));

						} while (rs.next() && rs.getInt("gwportid") == gwportid);
						rs.previous();

					} while (rs.next() && rs.getInt("moduleid") == moduleid);
					rs.previous();
				}

				String key = rs.getString("netboxid")+":"+rs.getString("moduleid");
				m.put(key, gwm);
			}

			moduleMap = m;
			dumpUsedTime = System.currentTimeMillis() - dumpBeginTime;
			Log.d("INIT", "Dumped gwport in " + dumpUsedTime + " ms");

		} catch (SQLException e) {
			Log.e("INIT", "SQLException: " + e.getMessage());
		}

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

		// We protect the whole update procedure to be on the safe
		// side. This code executes very quickly compared to data
		// collection in any case.
		synchronized(getClass()) {
			Log.setDefaultSubsystem("GwportHandler");
			int newcnt = 0, updcnt = 0, newPrefixCnt=0;

			errl("Gwports for " + nb);

			try {

				Map removeGwipMap = new HashMap();
				Set prefixUpdateSet = new HashSet();
				Map vlanMap = new IdentityHashMap();

				// DB dumped, check if we need to update
				for (Iterator gwModules = gc.getGwModules(); gwModules.hasNext();) {
					GwModule gwm = (GwModule)gwModules.next();
					String moduleid = gwm.getModuleidS();

					String gwportKey = nb.getNetboxid()+":"+moduleid;
					//System.err.println("gwportKey: " + gwportKey);
					GwModule oldgwm = (GwModule)moduleMap.get(gwportKey);
					//System.err.println("   GWM: " + gwm);
					//System.err.println("OLDGWM: " + oldgwm);
					moduleMap.put(gwportKey, gwm);

					errl("  GwModule: " + gwm);
				
					for (Iterator gwPorts = gwm.getGwports(); gwPorts.hasNext();) {
						Gwport gwp = (Gwport)gwPorts.next();

						errl("    Gwport: " + gwp);

						// Find old if exists
						String gwportid;
						Gwport oldgwp = (oldgwm == null) ? null : oldgwm.getGwport(gwp.getIfindex());
						//System.err.println("   GWP: " + gwp);
						//System.err.println("OLDGWP: " + oldgwp);

						if (oldgwp == null) {
							// Insert new
							Log.d("NEW_GWPORT", "Creating gwport: " + gwp);

							String masterindex = null;

							String[] ins = {
								"gwportid", "",
								"moduleid", moduleid,
								"ifindex", gwp.getIfindex(),
								"link", gwp.getLinkS(),
								"masterindex", masterindex,
								"interface", Database.addSlashes(gwp.getInterf()),
								"speed", gwp.getSpeedS(),
								"ospf", gwp.getOspfS()
							};
							gwportid = Database.insert("gwport", ins, null);
							gwportidMap.put(gwportid, new String[] { nb.getSysname(), gwp.getInterf(), (gwp.hsrpCount()>0?"true":"false") });
							newcnt++;

						} else {
							gwportid = oldgwp.getGwportidS();
							if (!gwp.equalsGwport(oldgwp) || gwm.getModuleid() != oldgwm.getModuleid()) {
								//if (!gwp.equalsGwport(oldgwp)) {
								// Vi må oppdatere
								Log.d("UPDATE_GWPORT", "Update gwportid: "+gwportid+" ifindex="+gwp.getIfindex());

								String masterindex = null;

								String[] set = {
									"moduleid", gwm.getModuleidS(),
									"ifindex", gwp.getIfindex(),
									"link", gwp.getLinkS(),
									"masterindex", masterindex,
									"interface", Database.addSlashes(gwp.getInterf()),
									"speed", gwp.getSpeedS(),
									"ospf", gwp.getOspfS()
								};
								String[] where = {
									"gwportid", gwportid
								};
								Database.update("gwport", set, where);
								updcnt++;
							}

							// Check which prefices are present in oldgwp, but not in
							// gwp, and remove them from the mentioned gwportprefix
							// entries
							Set removeGwip = oldgwp.gwipIntersection(gwp.gwipSet());
							removeGwipMap.put(gwportid, removeGwip);

						}
						gwp.setGwportid(gwportid);

						for (Iterator gwportPrefices = gwp.getGwportPrefices(); gwportPrefices.hasNext();) {
							Gwportprefix gp = (Gwportprefix)gwportPrefices.next();

							String gwip = gp.getGwip();
							boolean hsrp = gp.getHsrp();
							Prefix p = gp.getPrefix();
							Vlan vl = p.getVlan();
							if (!vl.getNettype().equals("elink")) vl.setNettype(Vlan.UNKNOWN_NETTYPE);

							errl("      Gwip: " + gwip);
							errl("      Hsrp: " + hsrp);
							errl("      Prefix: " + p);
							errl("      Vlan: " + vl);

							Gwportprefix oldgp = oldgwp == null ? null : oldgwp.getGwportprefix(gwip);
							String prefixid;
							if (oldgp == null && !prefixDbMap.containsKey(p.getCidr())) {
								// There is no old gwportprefix and prefix does not contains the netaddr
								// Note: the gwpDbMap cannot contain getGwip now, so the next section will also match
								Log.d("NEW_PREFIX", "Creating vlan: " + vl);
								//System.err.println("Create 1("+vl.getVlanid()+": " + vl);
								if (vl.getVlanid() == 0) {
									createVlan(vl);
								}
							
								String[] ins = {
									"prefixid", "",
									"netaddr", p.getCidr(),
									"vlanid", vl.getVlanidS(),
								};
								prefixid = Database.insert("prefix", ins, null);
								p.setPrefixid(prefixid);
								prefixDbMap.put(p.getCidr(), p);
								newPrefixCnt++;
							}

							if (oldgp == null && !gwpDbMap.containsKey(gp.getGwip())) {
								// The prefix exists, but there is no old gwportprefix with the same gwip
								Log.d("NEW GWPORTPREFIX", "Gwportprefix: " + gp);
								Prefix dbp = (Prefix)prefixDbMap.get(p.getCidr());
							
								String[] ins = {
									"gwportid", gwportid,
									"prefixid", dbp.getPrefixidS(),
									"gwip", gp.getGwip(),
									"hsrp", gp.getHsrp()?"t":"f"
								};
								Database.insert("gwportprefix", ins);
								gwpDbMap.put(gp.getGwip(), gp);
								gp.setPrefix(dbp);

							} else {
								// oldgp == null -> gwip moved to other gwport, we must update gwportprefix
								// oldgp != null -> only update prefix/gwportprefix if changed. oldgp and dbgp are the same reference
								Gwportprefix dbgp = (Gwportprefix)gwpDbMap.get(gp.getGwip());

								// oldgp must now be equal to dbgp
								if (oldgp != null && oldgp != dbgp) {
									System.err.println("********* ERROR ********** oldgp != dbgp !!!");
									return;
								}

								if (!gp.equalsGwportprefix(oldgp)) {
									// Update gwportprefix and dbgp object
									Log.d("UPDATE_GWPORTPREFIX", "Update gwportprefix " + gp);
									String[] set = {
										"gwportid", gwportid,
										"hsrp", gp.getHsrp()?"t":"f",
									};
									String[] where = {
										"gwip", gp.getGwip()
									};
									Database.update("gwportprefix", set, where);
									dbgp.setHsrp(gp.getHsrp());
								}
								gp = dbgp;
							}

							// gp must now be equal to dbgp
							if (gp != gwpDbMap.get(gp.getGwip())) {
								System.err.println("********* ERROR ********** gp != dbgp !!!");
								return;
							}

							Prefix dbp = gp.getPrefix();
							Vlan dbvl = dbp.getVlan();

							if (dbvl == null) {
								System.err.println("********* ERROR ********** dbvl == null for prefix: " + dbp + " !!!");
								return;
							}

							if (vl.getVlan() == null || vl.getVlan().equals(dbvl.getVlan())) {
								if (!vl.equalsVlan(dbvl)) {
									// Update vlan and dbvl object
									Log.d("UPDATE_VLAN", "Update vlan " + vl);
									if (!vl.getNettype().equals(Vlan.UNKNOWN_NETTYPE)) {
										vl.setVlanid(dbvl.getVlanid());
										updateVlan(vl);
									}
									dbvl.setEqual(vl);
								}
								vl = dbvl;
								p.setVlan(vl);
							} else {
								// We must create a new vlan
								//System.err.println("Create 2("+nb.getSysname()+"): " + vl);
								//System.err.println("  (" + dbvl.getVlanid() + "): " + dbvl);
								createVlan(vl);
								vlanMap.put(vl, null);
							}
						
							if (!p.equalsPrefix(dbp)) {
								// Update prefix and dbp object
								Log.d("UPDATE_PREFIX", "Update prefix " + p);
								String[] set = {
									"netaddr", p.getCidr(),
									"vlanid", vl.getVlanidS(),
								};
								String[] where = {
									"prefixid", dbp.getPrefixidS()
								};
								Database.update("prefix", set, where);
								dbp.setNetaddr(p.getNetaddr());
								dbp.setMasklen(p.getMasklen());
								dbp.setVlan(vl);
								p = dbp;
							}

							// Make sure the gwport refers to the correct gwportprefix
							gwp.addGwportprefix(gp.getGwip(), (Gwportprefix)gwpDbMap.get(gp.getGwip()));

							// This gwport now points to this prefix
							p.addGwport(gwportid);
						
							// Add prefix for autodetermination of nettype
							prefixUpdateSet.add(p.getCidr());
						
						}
					}
				}

				// Remove all gwips from gwports where they no longer exist.
				for (Iterator it = removeGwipMap.entrySet().iterator(); it.hasNext();) {
					Map.Entry me = (Map.Entry)it.next();
					String gwportid = (String)me.getKey();
					for (Iterator gwipIt = ((Set)me.getValue()).iterator(); gwipIt.hasNext();) {
						String rgwip = (String)gwipIt.next();
						if (gwpDbMap.containsKey(rgwip)) {
							Gwportprefix rgwp = (Gwportprefix)gwpDbMap.get(rgwip);
							rgwp.getPrefix().removeGwport(gwportid);

							// Delete it
							Database.update("DELETE FROM gwportprefix WHERE gwip='" + rgwip + "'");
							gwpDbMap.remove(rgwip);
						}
					}
				}

				// Do autodetermination of nettype
				for (Iterator it = prefixUpdateSet.iterator(); it.hasNext();) {
					Prefix p = (Prefix)prefixDbMap.get(it.next());
					Vlan vl = p.getVlan();

					if (vl.getNettype().equals(Vlan.UNKNOWN_NETTYPE)) {
						String nettype, netident = null;
						int numGwp = p.gwportCount();
					
						Set sysnameSet = new HashSet();
						int hsrpCnt = 0;
						for (Iterator gwIt = p.getGwportidIterator(); gwIt.hasNext();) {
							String[] s = (String[])gwportidMap.get(gwIt.next());
							sysnameSet.add(s[0]);
							boolean hsrp = s[2].startsWith("t");
							if (hsrp) hsrpCnt++;
						}

						//System.err.println("Prefix: " + p + ", num: " + numGwp + ", hsrpCnt: " + hsrpCnt + ", sysnames: " + sysnameSet);

						if (numGwp == 0) {
							// This can't happen
							System.err.println("Prefix without any gwports, this cannot happen, contact nav support!");
							Log.e("HANDLE", "Prefix without any gwports, this cannot happen, contact nav support!");
							continue;
						}
						// Only one gwport = lan
						else if (numGwp == 1) {
							String interf = ((String[])gwportidMap.get(p.getGwportidIterator().next()))[1];
							if (interf.toLowerCase().indexOf("loopback") >= 0) {
								nettype = "loopback";
							} else {
								nettype = "lan";
							}
						}
						// More than one gwport + hsrp = lan
						else if (hsrpCnt > 0 && numGwp > 1) {
							nettype = "lan";
						}
						// Two gwports from different routers = link
						else if (numGwp == 2 && sysnameSet.size() == 2) {
							nettype = "link";
							Iterator sIt = sysnameSet.iterator();
							netident = sIt.next()+","+sIt.next();
						}
						// More than two gwports without hsrp = stam
						else {
							nettype = "stam";
						}

						vl.setNettype(nettype);
						if (netident != null) vl.setNetident(netident);

						Log.d("AUTO_NETTYPE", "Autodetermination of nettype: " + nettype);
					
						updateVlan(vl);
						//System.err.println("Update(" + vl.getVlanid() + "): " + vl);
					}
				}

				if (newPrefixCnt > 0) {
					// Update netbox with new prefixids
					Database.update("UPDATE netbox SET prefixid = (SELECT prefixid FROM prefix JOIN vlan USING(vlanid) WHERE ip << netaddr AND nettype!='scope') WHERE prefixid IS NULL");
				}

			} catch (SQLException e) {
				Log.e("HANDLE", "SQLException: " + e.getMessage());
				e.printStackTrace(System.err);
			}
		}
	}
	
	private static void createVlan(Vlan vl) throws SQLException {
		String[] ins = {
			"vlanid", "",
			"vlan", vl.getVlanS(),
			"nettype", vl.getNettype(),
			"orgid", vl.getOrgid(),
			"usageid", vl.getUsageid(),
			"netident", vl.getNetident(),
			"description", vl.getDescription()
		};
		String vlanid = Database.insert("vlan", ins, null);
		vl.setVlanid(vlanid);
	}

	private static void updateVlan(Vlan vl) throws SQLException {
		String[] set = {
			"nettype", vl.getNettype(),
			"orgid", vl.getOrgid(),
			"usageid", vl.getUsageid(),
			"netident", vl.getNetident(),
			"description", vl.getDescription()
		};
		String[] where = {
			"vlanid", vl.getVlanidS()
		};
		Database.update("vlan", set, where);
	}

	private static void errl(Object o) {
		if (DEBUG_OUT) System.err.println(o);
	}

}
