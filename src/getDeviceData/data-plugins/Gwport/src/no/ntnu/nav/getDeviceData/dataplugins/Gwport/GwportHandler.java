package no.ntnu.nav.getDeviceData.dataplugins.Gwport;

import java.util.*;
import java.sql.*;

import no.ntnu.nav.logger.*;
import no.ntnu.nav.Database.*;
import no.ntnu.nav.ConfigParser.*;
import no.ntnu.nav.util.*;
import no.ntnu.nav.netboxinfo.*;
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

	private static MultiMap nbGwpMap = new HashMultiMap();
	private static Map devidMap = Collections.synchronizedMap(new HashMap());
	private static Map moduleMap;

	private static Map prefixDbMap;
	private static Map gwpDbMap;
	private static Map gwportidMap;
	private static Map gwVlanMap;

	private static ConfigParser navCp;

	// MultiMap from gwportid to gwip,prefixid
	//private static MultiMap gwipMap;
	//private static MultiMap prefixidMap;
	

	/**
	 * Fetch initial data from module/gwport/prefix/vlan tables.
	 */
	public synchronized void init(Map persistentStorage, Map changedDeviceids) {
		// Remove any devices no longer present
		if (!changedDeviceids.isEmpty()) {
			synchronized(getClass()) {
				Map removeGwipMap = new HashMap();
				for (Iterator it = changedDeviceids.entrySet().iterator(); it.hasNext();) {
					Map.Entry me = (Map.Entry)it.next();
					if (((Integer)me.getValue()).intValue() == DataHandler.DEVICE_DELETED) {
						GwModule gwm = (GwModule)devidMap.remove(me.getKey());
						if (gwm != null) {
							for (Iterator gwIt = gwm.getGwports(); gwIt.hasNext();) {
								Gwport gwp = (Gwport)gwIt.next();
								removeGwipMap.put(gwp.getGwportidS(), gwp.gwipSet());
							}
						}
					}
				}
				try {
					removeGwips(removeGwipMap);
				} catch (SQLException e) {
					Log.e("INIT-REMOVE-GWIP", "SQLException: " + e.getMessage());
				}
			}
		}
		if (persistentStorage.containsKey("initDone")) return;
		persistentStorage.put("initDone", null);
		navCp = (ConfigParser)persistentStorage.get("navCp");

		ResultSet rs;
		long dumpBeginTime,dumpUsedTime;

		Log.setDefaultSubsystem("GwportHandler");

		try {
			// gwportid -> netboxid + interface
			gwportidMap = Collections.synchronizedMap(new HashMap());
			rs = Database.query("SELECT gwport.gwportid,sysname,ifindex,interface,hsrp FROM netbox JOIN module USING(netboxid) JOIN gwport USING(moduleid) LEFT JOIN gwportprefix ON (gwport.gwportid=gwportprefix.gwportid AND hsrp='t')");
			while (rs.next()) {
				gwportidMap.put(rs.getString("gwportid"), new String[] { rs.getString("sysname"), rs.getString("interface"), String.valueOf(rs.getBoolean("hsrp")), rs.getString("ifindex") });
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
			Map gwVlMap = Collections.synchronizedMap(new HashMap());
			rs = Database.query("SELECT deviceid,serial,hw_ver,fw_ver,sw_ver,moduleid,netboxid,module,model,descr,gwportid,ifindex,interface,masterindex,speed,ospf,gwip FROM device JOIN module USING(deviceid) LEFT JOIN gwport USING(moduleid) LEFT JOIN gwportprefix USING(gwportid) ORDER BY moduleid,gwportid");
			while (rs.next()) {
				// Create module
				GwModule gwm = new GwModule(rs.getString("serial"), rs.getString("hw_ver"), rs.getString("fw_ver"), rs.getString("sw_ver"), rs.getInt("module"));
				gwm.setDeviceid(rs.getInt("deviceid"));
				gwm.setModuleid(rs.getInt("moduleid"));
				gwm.setModel(rs.getString("model"));
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
						nbGwpMap.put(rs.getString("netboxid"), gwp);

						int gwportid = rs.getInt("gwportid");
						do {
							// Add prefices
							String gwip = rs.getString("gwip");
							Gwportprefix gwpp = (Gwportprefix)gwpDbMap.get(gwip);
							if (gwpp != null) {
								gwp.addGwportprefix(gwip, gwpp);
								Vlan vl = gwpp.getPrefix().getVlan();
								if (vl.getVlan() != null) {
									String vlKey = rs.getString("netboxid")+":"+gwpp.getPrefix().getVlan().getVlanS();
									if (gwVlMap.containsKey(vlKey)) {
										if (vl != gwVlMap.get(vlKey)) {
											System.err.println("Detected duplicate vlan("+vlKey+") on same gw, deleting ...");
											Vlan dbvl = (Vlan)gwVlMap.get(vlKey);
											Prefix dbp = gwpp.getPrefix();
											System.err.println("  Want to delete: " + vl.getVlanidS()+ ", dbvl: " + dbvl.getVlanidS() + " p: " + dbp.getPrefixidS());
											Database.update("UPDATE prefix SET vlanid='"+dbvl.getVlanidS()+"' WHERE prefixid='"+dbp.getPrefixidS()+"'");
											Database.update("DELETE FROM vlan WHERE vlanid='"+vl.getVlanidS()+"'");
											dbp.setVlan(dbvl);
										}
									} else {
										gwVlMap.put(vlKey, vl);
									}
								}
							}

						} while (rs.next() && rs.getInt("gwportid") == gwportid);
						rs.previous();

					} while (rs.next() && rs.getInt("moduleid") == moduleid);
					rs.previous();
				}

				//String key = rs.getString("netboxid")+":"+rs.getString("moduleid");
				String key = rs.getString("moduleid");
				m.put(key, gwm);
				devidMap.put(gwm.getDeviceidS(), gwm);
			}

			moduleMap = m;
			this.gwVlanMap = gwVlMap;
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
	public void handleData(Netbox nb, DataContainer dc, Map changedDeviceids) {
		if (!(dc instanceof GwportContainer)) return;
		GwportContainer gc = (GwportContainer)dc;
		if (!gc.isCommited()) return;

		// Let ModuleHandler update the module table first
		ModuleHandler mh = new ModuleHandler();
		mh.handleData(nb, dc, changedDeviceids);

		// We protect the whole update procedure to be on the safe
		// side. This code executes very quickly compared to data
		// collection in any case.
		synchronized(getClass()) {
			Log.setDefaultSubsystem("GwportHandler");
			int newcnt = 0, updcnt = 0, newPrefixCnt=0;
			boolean fixupPrefix = false;

			//errl("Gwports for " + nb);
			Map foundGwps = new HashMap();

			try {

				Map removeGwipMap = new HashMap();
				Set prefixUpdateSet = new HashSet();
				//Map vlanMap = new IdentityHashMap();

				// DB dumped, check if we need to update
				for (Iterator gwModules = gc.getGwModules(); gwModules.hasNext();) {
					GwModule gwm = (GwModule)gwModules.next();
					String moduleid = gwm.getModuleidS();

					//String gwportKey = nb.getNetboxid()+":"+moduleid;
					String gwportKey = moduleid;
					//System.err.println("gwportKey: " + gwportKey);
					GwModule oldgwm = (GwModule)moduleMap.get(gwportKey);
					//System.err.println("   GWM: " + gwm);
					//System.err.println("OLDGWM: " + oldgwm);
					devidMap.put(gwm.getDeviceidS(), gwm);
					moduleMap.put(gwportKey, gwm);

					errl("  GwModule: " + gwm);
				
					for (Iterator gwPorts = gwm.getGwports(); gwPorts.hasNext();) {
						Gwport gwp = (Gwport)gwPorts.next();
						errl("    Gwport: " + gwp);

						// Check if this is a static entry
						for (Iterator gwportPrefices = gwp.getGwportPrefices(); gwportPrefices.hasNext();) {
							Gwportprefix gp = (Gwportprefix)gwportPrefices.next();
							Prefix p = gp.getPrefix();
							Vlan vl = p.getVlan();
							if ("static".equals(vl.getNettype()) && prefixDbMap.containsKey(p.getCidr())) {
								Prefix oldp = (Prefix)prefixDbMap.get(p.getCidr());
								Vlan oldv = oldp.getVlan();
								if (!"static".equals(oldv.getNettype())) {
									System.err.println("Removed static prefix: " + p.getCidr());
									gwportPrefices.remove();
								}
							}
						}
						if (!gwp.getGwportPrefices().hasNext()) {
							System.err.println("  Not adding gwp because no prefices: " + gwp);
							continue;
						}
						foundGwps.put(gwp.getIfindex(), gwp);

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
							gwportidMap.put(gwportid, new String[] { nb.getSysname(), gwp.getInterf(), (gwp.hsrpCount()>0?"true":"false"), gwp.getIfindex() });
							changedDeviceids.put(gwm.getDeviceidS(), new Integer(DataHandler.DEVICE_ADDED));							
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
								changedDeviceids.put(gwm.getDeviceidS(), new Integer(DataHandler.DEVICE_UPDATED));
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
							//if (!vl.getNettype().equals("elink")) vl.setNettype(Vlan.UNKNOWN_NETTYPE);
							if (vl.getNettype().equals("elink")) vl.setNetident(null);
							//vl.setNettype(Vlan.UNKNOWN_NETTYPE);

							errl("      Gwip: " + gwip);
							errl("      Hsrp: " + hsrp);
							errl("      Prefix: " + p);
							errl("      Vlan: " + vl);

							Gwportprefix oldgp = oldgwp == null ? null : oldgwp.getGwportprefix(gwip);
							String prefixid;
							if (!prefixDbMap.containsKey(p.getCidr())) {
								// There is no old gwportprefix and prefix does not contains the netaddr
								// Note: the gwpDbMap cannot contain getGwip now, so the next section will also match

								// Check if the vlan already exists on the gw
								if (vl.getVlan() != null) {
									String vlKey = nb.getNetboxid()+":"+vl.getVlanS();
									if (gwVlanMap.containsKey(vlKey)) {
										Vlan gwvl = (Vlan)gwVlanMap.get(vlKey);
										vl.setVlanid(gwvl.getVlanid());
									} else {
										gwVlanMap.put(vlKey, vl);
									}
								}

								if (vl.getVlanid() == 0) {
									Log.d("NEW_PREFIX", "Creating vlan: " + vl);
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

							if (!gwpDbMap.containsKey(gp.getGwip())) {
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
									Log.d("GWPORTPREFIX", "********* ERROR ********** oldgp != dbgp !!! ("+oldgp+","+dbgp+")");
									System.err.println("********* ERROR ********** oldgp != dbgp !!! ("+oldgp+","+dbgp+")");
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
									fixupPrefix = true;
								}
								gp = dbgp;
							}

							// gp must now be equal to dbgp
							if (gp != gwpDbMap.get(gp.getGwip())) {
								Log.d("GWPORTPREFIX", "********* ERROR ********** gp != dbgp !!! ("+gp+","+gwpDbMap.get(gp.getGwip())+")");
								System.err.println("********* ERROR ********** gp != dbgp !!! ("+gp+","+gwpDbMap.get(gp.getGwip())+")");
								return;
							}

							Prefix dbp = gp.getPrefix();
							Vlan dbvl = dbp.getVlan();

							if (dbvl == null) {
								Log.d("GWPORTPREFIX", "********* ERROR ********** dbvl == null for prefix: " + dbp + " !!!");
								System.err.println("********* ERROR ********** dbvl == null for prefix: " + dbp + " !!!");
								return;
							}

							boolean unknownNettype = vl.getNettype().equals(Vlan.UNKNOWN_NETTYPE);

							if (vl.getVlan() == null || vl.getVlan().equals(dbvl.getVlan())) {
								if (!vl.equalsVlan(dbvl)) {
									// Update vlan and dbvl object
									if (!unknownNettype || !vl.equalsDataVlan(dbvl)) {
										Log.d("UPDATE_VLAN", "Update vlan " + vl);
										vl.setVlanid(dbvl.getVlanid());
										updateVlan(vl, unknownNettype);
										fixupPrefix = true;
									}
									dbvl.setEqual(vl);
								}
								vl = dbvl;
								p.setVlan(vl);
							} else {
								// We must create a new vlan
								//System.err.println("Create 2("+nb.getSysname()+"): " + vl);
								//System.err.println("  (" + dbvl.getVlanid() + "): " + dbvl);
								String vlKey = nb.getNetboxid()+":"+vl.getVlanS();
								if (gwVlanMap.containsKey(vlKey)) {
									Vlan gwvl = (Vlan)gwVlanMap.get(vlKey);
									vl.setVlanid(gwvl.getVlanid());
								} else {
									createVlan(vl);
									gwVlanMap.put(vlKey, vl);
								}
							}

							if (!p.equalsPrefix(dbp)) {
								// Update prefix and dbp object
								if (prefixDbMap.containsKey(p.getCidr()) && !dbp.getCidr().equals(p.getCidr())) {
									Database.update("DELETE FROM prefix WHERE netaddr='"+p.getCidr()+"'");
								}
								
								Log.d("UPDATE_PREFIX", "Update prefix " + p + " (db: " + dbp + ")");
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
								fixupPrefix = true;
							}
							p = dbp;

							// Make sure the gwport refers to the correct gwportprefix
							gwp.addGwportprefix(gp.getGwip(), (Gwportprefix)gwpDbMap.get(gp.getGwip()));

							// This gwport now points to this prefix
							p.addGwport(gwportid);
						
							// Add prefix for autodetermination of nettype
							if (unknownNettype) {
								prefixUpdateSet.add(p.getCidr());
							}
						
						}
					}
				}

				// Remove gwports missing
			    Map oldIfindex = new HashMap();
				Set oldgwpSet = nbGwpMap.get(nb.getNetboxidS());
				nbGwpMap.remove(nb.getNetboxidS());
				for (Iterator it = oldgwpSet.iterator(); it.hasNext();) {
					Gwport gwp = (Gwport)it.next();
					oldIfindex.put(gwp.getIfindex(), gwp);
				}
				nbGwpMap.putAll(nb.getNetboxidS(), new HashSet(foundGwps.values()));
				oldIfindex.keySet().removeAll(foundGwps.keySet());
				
				for (Iterator it = oldIfindex.values().iterator(); it.hasNext();) {
					Gwport gwp = (Gwport)it.next();
					removeGwipMap.put(gwp.getGwportidS(), gwp.gwipSet());
				}

				if (!removeGwipMap.isEmpty()) fixupPrefix = true;
				removeGwips(removeGwipMap);

				// Do autodetermination of nettype
				for (Iterator it = prefixUpdateSet.iterator(); it.hasNext();) {
					Prefix p = (Prefix)prefixDbMap.get(it.next());
					Vlan vl = p.getVlan();
					String DOMAIN_SUFFIX = navCp.get("DOMAIN_SUFFIX");

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
						System.err.println("Prefix without any gwports: " + p);
						Log.e("HANDLE", "Prefix without any gwports, this cannot happen, contact nav support!");
						Log.d("HANDLE", "Prefix without any gwports: " + p + ", vlan: " + vl);
						continue;
					}
					// Only one gwport = loopback, elink or lan (default)
					else if (numGwp == 1) {
						String interf = ((String[])gwportidMap.get(p.getGwportidIterator().next()))[1];
						if (interf.toLowerCase().indexOf("loopback") >= 0) {
							nettype = "loopback";
						} else if (p.getMasklen() == 30) {
							nettype = "elink";
							// Try to find elink name from CDP so we can set netident
							String ifindex = ((String[])gwportidMap.get(p.getGwportidIterator().next()))[3];
							// This is the swport ifindex, we need the gwport ifindex
							if (vl.getVlan() != null) {
								ResultSet myrs = Database.query("SELECT ifindex FROM swport JOIN module USING(moduleid) WHERE netboxid="+nb.getNetboxid()+" and vlan='"+vl.getVlan()+"'");
								if (myrs.next()) {
									String remoteCdp = NetboxInfo.getSingleton(nb.getNetboxidS(), "unrecognizedCDP", myrs.getString("ifindex"));
									if (remoteCdp != null) vl.setNetident(util.remove(nb.getSysname(), DOMAIN_SUFFIX) + "," + util.remove(remoteCdp, DOMAIN_SUFFIX));
								}
							}
						} else {
							nettype = "lan";
						}
					}
					// Two different routers + hsrp = lan
					else if (hsrpCnt > 0 && sysnameSet.size() == 2) {
						nettype = "lan";
					}
					// Two gwports from different routers = link
					else if (numGwp == 2 && sysnameSet.size() == 2 && hsrpCnt == 0) {
						nettype = "link";
						Iterator sIt = sysnameSet.iterator();
						if (vl.getConvention() == Vlan.CONVENTION_NTNU) {
							netident = util.remove((String)sIt.next(), DOMAIN_SUFFIX) + "," + util.remove((String)sIt.next(), DOMAIN_SUFFIX);
						}
					}
					// More than two gwports without hsrp = core
					else {
						nettype = "core";
					}
					/*
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
					// More than two gwports without hsrp = core
					else {
						nettype = "core";
					}
					*/

					Log.d("AUTO_NETTYPE", "Autodetermination of nettype: " + vl + " New: " + nettype);

					if (!Vlan.equals(vl.getNettype(), nettype) ||
						(netident != null && !netident.equals(vl.getNetident()))) {
						vl.setNettype(nettype);
						if (netident != null) vl.setNetident(netident);
					
						updateVlan(vl, false);
						fixupPrefix = true;
						//System.err.println("Update(" + vl.getVlanid() + "): " + vl);
					}
				}

				if (newPrefixCnt > 0) {
					// Update netbox with new prefixids
					// Check overlapping prefices
					// select * from prefix a join prefix b on (a.netaddr << b.netaddr) join vlan on (b.vlanid=vlan.vlanid) and nettype not in ('scope','netaddr');
					// select netboxid,count(*) from netbox join prefix on (ip << netaddr) natural join vlan where nettype not in ('static','scope') group by netboxid having count(*) > 1;
					Database.update("UPDATE netbox SET prefixid = (SELECT prefixid FROM prefix JOIN vlan USING(vlanid) WHERE ip << netaddr AND nettype NOT IN ('scope','static')) WHERE prefixid IS NULL");
				}

				if (fixupPrefix) {
					int delPrefix = Database.update("DELETE FROM prefix WHERE prefixid NOT IN (SELECT prefixid FROM gwportprefix) AND vlanid NOT IN (SELECT vlanid FROM vlan JOIN swportvlan USING(vlanid))");
					int delVlan = Database.update("DELETE FROM vlan WHERE vlanid NOT IN (SELECT vlanid FROM prefix UNION SELECT vlanid FROM swportvlan)");
					Log.d("FIXUP_PREFIX", "Deleted " + delPrefix + " prefices, " + delVlan + " VLANs no longer in use");
				}

			} catch (SQLException e) {
				Log.e("HANDLE", "SQLException: " + e.getMessage());
				e.printStackTrace(System.err);
			}
		}
	}

	private static void removeGwips(Map removeGwipMap) throws SQLException {
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

	}
	
	private static void createVlan(Vlan vl) throws SQLException {
		String[] ins = {
			"vlanid", "",
			"vlan", vl.getVlanS(),
			"nettype", vl.getNettype(),
			"orgid", "(SELECT orgid FROM org WHERE orgid='"+vl.getOrgid()+"')",
			"usageid", "(SELECT usageid FROM usage WHERE usageid='"+vl.getUsageid()+"')",
			"netident", vl.getNetident(),
			"description", vl.getDescription()
		};
		String vlanid = Database.insert("vlan", ins, null);
		vl.setVlanid(vlanid);
	}

	private static void updateVlan(Vlan vl, boolean unknownNettype) throws SQLException {
		String[] set = {
			"nettype", unknownNettype ? null : vl.getNettype(),
			"orgid", "(SELECT orgid FROM org WHERE orgid='"+vl.getOrgid()+"')",
			"usageid", "(SELECT usageid FROM usage WHERE usageid='"+vl.getUsageid()+"')",
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
