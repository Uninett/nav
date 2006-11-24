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
	private static ConfigParser navCp;

	/**
	 * Fetch initial data from module/gwport/prefix/vlan tables.
	 */
	public synchronized void init(Map persistentStorage, Map changedDeviceids) {
		if (persistentStorage.containsKey("initDone")) return;
		persistentStorage.put("initDone", null);
		navCp = (ConfigParser)persistentStorage.get("navCp");

	}

	/**
	 * Return a DataContainer object used to return data to this
	 * DataHandler.
	 */
	public DataContainer dataContainerFactory() {
		return new GwportContainer(this);
	}

	Map gwportMap = new HashMap();
	Map vlanMap = new HashMap();
	Map prefixMap = new HashMap();
	Map gwpMap = new HashMap();
	Map gwVlanMap = new HashMap();

	private Vlan vlanFactory(ResultSet rs) throws SQLException {
		Vlan vlan = new Vlan(rs.getString("netident"), rs.getInt("vlan"));
		vlan.setVlanid(rs.getInt("vlanid"));
		vlan.setNettype(rs.getString("nettype"));
		vlan.setOrgid(rs.getString("orgid"));
		vlan.setUsageid(rs.getString("usageid"));
		vlan.setDescription(rs.getString("description"));
		vlanMap.put(rs.getString("vlanid"), vlan);
		return vlan;
	}

	private Vlan getVlan(String vlanid) throws SQLException {
		// Create vlan
		Vlan vlan = (Vlan)vlanMap.get(vlanid);
		if (vlan == null) {
			ResultSet rs = Database.query("SELECT vlanid,vlan,nettype,orgid,usageid,netident,description FROM vlan WHERE vlanid='"+vlanid+"'");
			if (rs.next()) {
				// Create vlan
				vlan = new Vlan(rs.getString("netident"), rs.getInt("vlan"));
				vlan.setVlanid(rs.getInt("vlanid"));
				vlan.setNettype(rs.getString("nettype"));
				vlan.setOrgid(rs.getString("orgid"));
				vlan.setUsageid(rs.getString("usageid"));
				vlan.setDescription(rs.getString("description"));
				vlanMap.put(rs.getString("vlanid"), vlan);
			}
		}
		return vlan;
	}

	private Prefix getPrefix(String cidr) throws SQLException {
		Prefix p = (Prefix)prefixMap.get(cidr);
		if (p == null) {
			ResultSet rs = Database.query("SELECT prefixid,netaddr AS cidr,host(netaddr) AS netaddr,masklen(netaddr) AS masklen,vlanid,gwportid FROM prefix LEFT JOIN gwportprefix USING(prefixid) WHERE netaddr='"+cidr+"'");
			if (rs.next()) {
				p = new Prefix(rs.getString("netaddr"), rs.getInt("masklen"), getVlan(rs.getString("vlanid")));
				p.setPrefixid(rs.getInt("prefixid"));
				prefixMap.put(rs.getString("cidr"), p);
				if (rs.getInt("gwportid") != 0) {
					do {
						p.addGwport(rs.getString("gwportid"));
					} while (rs.next());
				}
			}
		}
		return p;
	}

	private Gwportprefix getGwportprefix(String gwip) throws SQLException {
		Gwportprefix gp = (Gwportprefix)gwpMap.get(gwip);
		if (gp == null) {
			ResultSet rs = Database.query("SELECT gwportid,gwip,hsrp,netaddr AS cidr FROM gwportprefix JOIN prefix USING(prefixid) WHERE gwip='"+gwip+"'");
			if (rs.next()) {
				gp = new Gwportprefix(rs.getString("gwip"), rs.getBoolean("hsrp"), getPrefix(rs.getString("cidr")));
				gwpMap.put(rs.getString("gwip"), gp);
			}
		}
		return gp;
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

			try {
				// Fill gwVlanMap
				{
					ResultSet rs = Database.query("SELECT vlanid,vlan,nettype,orgid,usageid,netident,description FROM vlan JOIN prefix USING(vlanid) JOIN gwportprefix USING(prefixid) JOIN gwport USING(gwportid) JOIN module USING(moduleid) WHERE vlan IS NOT NULL AND netboxid='"+nb.getNetboxid()+"'");
					while (rs.next()) {
						String vlKey = nb.getNetboxid()+":"+rs.getString("vlan");
						if (gwVlanMap.containsKey(vlKey)) {
							Vlan vl = (Vlan)gwVlanMap.get(vlKey);
							if (vl.getVlanid() != rs.getInt("vlanid")) {
								System.err.println("Detected duplicate vlan("+vlKey+") on same gw, deleting ...");
								String prefixid = rs.getString("prefixid");
								System.err.println("  Want to delete: " + rs.getString("vlanid") + ", dbvl: " + vl.getVlanid() + " p: " + rs.getString("prefixid"));
								Database.update("UPDATE prefix SET vlanid='"+vl.getVlanid()+"' WHERE vlanid='"+rs.getString("vlanid")+"'");
								Database.update("DELETE FROM vlan WHERE vlanid='"+rs.getString("vlanid")+"'");
							}
						} else {
							gwVlanMap.put(vlKey, vlanFactory(rs));
						}
					}
				}

				Map removeGwipMap = new HashMap();
				Set prefixUpdateSet = new HashSet();

				for (Iterator gwModules = gc.getGwModules(); gwModules.hasNext();) {
					GwModule gwm = (GwModule)gwModules.next();
					String moduleid = gwm.getModuleidS();
					if ("0".equals(moduleid)) {
						System.err.println("Moduleid is null!! " + gwm);
					}

					// Fetch old gwp from database
					ResultSet rs = Database.query("SELECT gwportid,ifindex,interface,masterindex,speed,metric AS ospf,gwip,hsrp,prefixid,netaddr AS cidr,host(netaddr) AS netaddr,masklen(netaddr) AS masklen,vlanid,vlanid,vlan,nettype,orgid,usageid,netident,description FROM gwport LEFT JOIN gwportprefix USING(gwportid) LEFT JOIN prefix USING(prefixid) LEFT JOIN vlan USING(vlanid) WHERE moduleid='"+moduleid+"'", true);
					while (rs.next()) {
						// Create vlan
						Vlan vlan = (Vlan)vlanMap.get(rs.getString("vlanid"));
						if (vlan == null && rs.getInt("vlanid") > 0) {
							vlan = vlanFactory(rs);
						}

						// Create prefix
						Prefix p = null;
						if (rs.getInt("prefixid") > 0) {
							p = getPrefix(rs.getString("cidr"));
						}

						// Create gwport
						Gwport gwp = new Gwport(rs.getString("ifindex"), rs.getString("interface"));
						gwp.setGwportid(rs.getInt("gwportid"));
						gwp.setMasterindex(rs.getInt("masterindex"));
						gwp.setSpeed(rs.getDouble("speed"));
						if (rs.getString("ospf") != null) gwp.setOspf(rs.getInt("ospf"));
						gwportMap.put(rs.getString("ifindex"), gwp);
						
						if (rs.getString("gwip") != null) {
							// Create gwpMap
							if (gwpMap.containsKey(rs.getString("gwip"))) {
								System.err.println("***** ERROR - duplicate gwip " + rs.getString("gwip"));
							}
							Gwportprefix gp = new Gwportprefix(rs.getString("gwip"), rs.getBoolean("hsrp"), p);
							p.addGwport(rs.getString("gwportid"));
							gwpMap.put(rs.getString("gwip"), gp);
							gwp.addGwportprefix(rs.getString("gwip"), gp);
						}
					}
					Database.free(rs);

					errl("  GwModule: " + gwm);
				
					for (Iterator gwPorts = gwm.getGwports(); gwPorts.hasNext();) {
						Gwport gwp = (Gwport)gwPorts.next();
						errl("    Gwport: " + gwp);

						// Check if this is a static entry
						for (Iterator gwportPrefices = gwp.getGwportPrefices(); gwportPrefices.hasNext();) {
							Gwportprefix gp = (Gwportprefix)gwportPrefices.next();
							Prefix p = gp.getPrefix();
							Vlan vl = p.getVlan();
							if ("static".equals(vl.getNettype())) {
								// If nexthop is in gwpDbMap, don't add the static route
								rs = Database.query("SELECT prefixid FROM gwportprefix WHERE gwip='"+p.getNexthop()+"'");
								if (rs.next()) {
									//System.err.println("Removing nexthop: " + p.getNexthop() + ", " + gwpDbMap.get(p.getNexthop()));
									gwportPrefices.remove();
								} else {
									rs = Database.query("SELECT prefixid FROM prefix WHERE netaddr='"+p.getCidr()+"'");
									if (rs.next()) {
										// Don't overwrite a non-static vlan with a static one
										Prefix oldp = getPrefix(p.getCidr());
										Vlan oldv = oldp.getVlan();
										if (!"static".equals(oldv.getNettype())) {
											//System.err.println("At " + nb.getSysname() + ", removed static prefix: " + p.getCidr() + " + p: " + p + " vl: " + vl + " oldp: " + oldp + " oldvl: " + oldv);
											gwportPrefices.remove();
										}
									}
								}
							}
						}
						if (!gwp.getGwportPrefices().hasNext()) {
							errl("    Not adding gwp because no prefices: " + gwp);
							continue;
						}

						// Find old if exists
						String gwportid;
						//System.err.println("   GWP: " + gwp);
						//System.err.println("OLDGWP: " + oldgwp);

						Gwport oldgwp = (Gwport)gwportMap.remove(gwp.getIfindex());
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
								"metric", gwp.getOspfS()
							};
							gwportid = Database.insert("gwport", ins, null);
							newcnt++;

						} else {
							gwportid = oldgwp.getGwportidS();
							if (!gwp.equalsGwport(oldgwp)) {
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
									"metric", gwp.getOspfS()
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
							if (!removeGwip.isEmpty()) removeGwipMap.put(gwportid, removeGwip);

						}
						gwp.setGwportid(gwportid);

						for (Iterator gwportPrefices = gwp.getGwportPrefices(); gwportPrefices.hasNext();) {
							Gwportprefix gp = (Gwportprefix)gwportPrefices.next();

							String gwip = gp.getGwip();
							boolean hsrp = gp.getHsrp();
							Prefix p = gp.getPrefix();
							Vlan vl = p.getVlan();
							//if (!vl.getNettype().equals("elink")) vl.setNettype(Vlan.UNKNOWN_NETTYPE);
							//if (vl.getNettype().equals("elink")) vl.setNetident(null);
							//vl.setNettype(Vlan.UNKNOWN_NETTYPE);
							if (vl.getNetident() != null) {
								vl.setNetident(util.remove(vl.getNetident(), navCp.get("DOMAIN_SUFFIX")));
							}

							errl("      Gwip: " + gwip);
							errl("      Hsrp: " + hsrp);
							errl("      Prefix: " + p);
							errl("      Vlan: " + vl);

							String prefixid;
							Prefix oldp = getPrefix(p.getCidr());
							if (oldp == null) {
								// There is no old gwportprefix and prefix does not contains the netaddr
								// Note: the gwpMap cannot contain getGwip now, so the next section will also match

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
									fixupPrefix = true;
								}
							
								String[] ins = {
									"prefixid", "",
									"netaddr", p.getCidr(),
									"vlanid", vl.getVlanidS(),
								};
								prefixid = Database.insert("prefix", ins, null);
								oldp = getPrefix(p.getCidr());
								newPrefixCnt++;
							} else {
								prefixid = oldp.getPrefixidS();
							}
							p.setPrefixid(prefixid);
							p.addGwports(oldp);
							
							Gwportprefix oldgp = getGwportprefix(gp.getGwip());
							if (oldgp == null) {
								// The prefix exists, but there is no old gwportprefix with the same gwip
								Log.d("NEW GWPORTPREFIX", "Gwportprefix: " + gp);
							
								String[] ins = {
									"gwportid", gwportid,
									"prefixid", p.getPrefixidS(),
									"gwip", gp.getGwip(),
									"hsrp", gp.getHsrp()?"t":"f"
								};
								Database.insert("gwportprefix", ins);

							} else {
								if (gp != oldgp || p != oldp) {
									// gwip moved to different gwport / prefix changed
									String[] set = {
										"gwportid", gwportid,
										"prefixid", prefixid,
										"hsrp", gp.getHsrp()?"t":"f",
									};
									String[] where = {
										"gwip", gp.getGwip()
									};
									Database.update("gwportprefix", set, where);
								} else {									
									if (!gp.equalsGwportprefix(oldgp)) {
										// Update gwportprefix
										Log.d("UPDATE_GWPORTPREFIX", "Update gwportprefix " + gp);
										String[] set = {
											"hsrp", gp.getHsrp()?"t":"f",
										};
										String[] where = {
											"gwip", gp.getGwip()
										};
										Database.update("gwportprefix", set, where);
										fixupPrefix = true;
									}
								}
							}

							boolean unknownNettype = vl.getNettype().equals(Vlan.UNKNOWN_NETTYPE);
							
							Vlan dbvl = oldp.getVlan();
							if (vl.getVlan() == null || vl.getVlan().equals(dbvl.getVlan())) {
								if (!vl.equalsVlan(dbvl)) {
									// Update vlan and dbvl object
									if (!unknownNettype || !vl.equalsDataVlan(dbvl)) {
										if (!vl.equalsOrgid(dbvl) || !vl.equalsUsageid(dbvl)) {
											if (!vl.equalsOrgid(dbvl)) reportMissingOrgid(vl);
											if (!vl.equalsUsageid(dbvl)) reportMissingUsageid(vl);
										} else {
											Log.d("UPDATE_VLAN", "Update vlan " + vl + " db: " + dbvl);
										}
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
								String vlKey = nb.getNetboxid()+":"+vl.getVlanS();
								if (gwVlanMap.containsKey(vlKey)) {
									Vlan gwvl = (Vlan)gwVlanMap.get(vlKey);
									vl.setVlanid(gwvl.getVlanid());
								} else {
									createVlan(vl);
									gwVlanMap.put(vlKey, vl);
									fixupPrefix = true;
								}
							}

							if (!p.equalsPrefix(oldp)) {
								// Update prefix
								Log.d("UPDATE_PREFIX", "Update prefix " + p + " (db: " + oldp + ")");
								String[] set = {
									"vlanid", vl.getVlanidS(),
								};
								String[] where = {
									"prefixid", prefixid,
								};
								Database.update("prefix", set, where);
								fixupPrefix = true;
							}

							// This gwport now points to this prefix
							p.addGwport(gwportid);
						
							// Add prefix for autodetermination of nettype
							if (unknownNettype) {
								prefixMap.put(p.getCidr(), p);
								prefixUpdateSet.add(p.getCidr());
							} else if (vl.getNettype().equals("elink")) {
								setElinkNetident(nb, p);
								updateVlan(vl, false);
							}
						}
					}
				}

				// Remove gwports missing
				if (!gwportMap.isEmpty()) {
					StringBuffer sb = new StringBuffer();
					for (Iterator it = gwportMap.values().iterator(); it.hasNext();) {
						Gwport gwp = (Gwport)it.next();
						sb.append(gwp.getGwportidS()+",");
					}
					sb.deleteCharAt(sb.length()-1);
					Database.update("DELETE FROM gwport WHERE gwportid IN ("+sb.toString()+")");
					fixupPrefix = true;
				}

				if (!removeGwipMap.isEmpty()) {
					fixupPrefix = true;
					removeGwips(removeGwipMap, gc.isStaticCommited());
				}

				// Do autodetermination of nettype
				if (!prefixUpdateSet.isEmpty()) {
					// gwportid -> netboxid + interface
					Map gwportidMap = new HashMap();

					// Fetch info for all required gwportids
					Set gwportidUpdateSet = new HashSet();
					for (Iterator it = prefixUpdateSet.iterator(); it.hasNext();) {
						Prefix p = (Prefix)getPrefix((String)it.next());
						p.addGwportsTo(gwportidUpdateSet);
					}
					ResultSet rs = Database.query("SELECT gwport.gwportid,sysname,ifindex,interface,hsrp FROM netbox JOIN module USING(netboxid) JOIN gwport USING(moduleid) LEFT JOIN gwportprefix ON (gwport.gwportid=gwportprefix.gwportid AND hsrp='t') WHERE gwport.gwportid IN (" + join(gwportidUpdateSet) + ")");
					while (rs.next()) {
						gwportidMap.put(rs.getString("gwportid"), new String[] { rs.getString("sysname"), rs.getString("interface"), String.valueOf(rs.getBoolean("hsrp")), rs.getString("ifindex") });
					}

					for (Iterator it = prefixUpdateSet.iterator(); it.hasNext();) {
						String DOMAIN_SUFFIX = navCp.get("DOMAIN_SUFFIX");
						Prefix p = (Prefix)getPrefix((String)it.next());
						Vlan vl = p.getVlan();

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
								setElinkNetident(nb, p);
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
				}

				if (newPrefixCnt > 0) {
					// Update netbox with new prefixids
					// Check overlapping prefices
					// select * from prefix a join prefix b on (a.netaddr << b.netaddr) join vlan on (b.vlanid=vlan.vlanid) and nettype not in ('scope','netaddr');
					// select netboxid,count(*) from netbox join prefix on (ip << netaddr) natural join vlan where nettype not in ('static','scope') group by netboxid having count(*) > 1;
					Database.update("UPDATE netbox SET prefixid = (SELECT prefixid FROM prefix JOIN vlan USING(vlanid) WHERE ip << netaddr AND nettype NOT IN ('scope','static') ORDER BY masklen(netaddr) DESC LIMIT 1) WHERE prefixid IS NULL");
				}

				if (fixupPrefix) {
					int delPrefix = Database.update("DELETE FROM prefix WHERE prefixid NOT IN (SELECT prefixid FROM gwportprefix) AND vlanid NOT IN (SELECT vlanid FROM vlan JOIN swportvlan USING(vlanid) UNION SELECT vlanid FROM vlan WHERE nettype='scope')");
					int delVlan = Database.update("DELETE FROM vlan WHERE vlanid NOT IN (SELECT vlanid FROM prefix UNION SELECT vlanid FROM swportvlan UNION SELECT vlanid FROM vlan WHERE nettype='scope')");
					Log.d("FIXUP_PREFIX", "Deleted " + delPrefix + " prefices, " + delVlan + " VLANs no longer in use");
				}

			} catch (SQLException e) {
				Log.e("HANDLE", "SQLException: " + e.getMessage());
				e.printStackTrace(System.err);
			}
		}
	}

	private String join(Collection c) {
		StringBuffer sb = new StringBuffer();
		for (Iterator it = c.iterator(); it.hasNext();) {
			sb.append("'" + it.next() + "',");
		}
		if (sb.length() > 0) sb.deleteCharAt(sb.length()-1);
		return sb.toString();
	}

	private void reportMissingOrgid(Vlan vl) throws SQLException {
		ResultSet rs = Database.query("SELECT orgid FROM org WHERE orgid='"+vl.getOrgid()+"'");
		if (!rs.next()) {
			Log.d("MISSING_ORGID", "Orgid " + vl.getOrgid() + " is missing for vlan " + vl.getVlan());
		}
	}

	private void reportMissingUsageid(Vlan vl) throws SQLException {
		ResultSet rs = Database.query("SELECT usageid FROM usage WHERE usageid='"+vl.getUsageid()+"'");
		if (!rs.next()) {
			Log.d("MISSING_USAGEID", "Usageid " + vl.getUsageid() + " is missing for vlan " + vl.getVlan());
		}
	}

	private void setElinkNetident(Netbox nb, Prefix p) throws SQLException {
		// Try to find elink name from CDP so we can set netident
		String DOMAIN_SUFFIX = navCp.get("DOMAIN_SUFFIX");
		Vlan vl = p.getVlan();
		if (vl.getVlan() != null) {
			ResultSet myrs = Database.query("SELECT ifindex FROM swport JOIN module USING(moduleid) WHERE netboxid="+nb.getNetboxid()+" and vlan='"+vl.getVlan()+"'");
			if (myrs.next()) {
				String remoteCdp = NetboxInfo.getSingleton(nb.getNetboxidS(), "unrecognizedCDP", myrs.getString("ifindex"));
				if (remoteCdp != null) vl.setNetident(util.remove(nb.getSysname(), DOMAIN_SUFFIX) + "," + util.remove(remoteCdp, DOMAIN_SUFFIX));
			}
		}
	}

	private static void removeGwips(Map removeGwipMap, boolean isStaticCommited) throws SQLException {
		// Remove all gwips from gwports where they no longer exist.
		for (Iterator it = removeGwipMap.entrySet().iterator(); it.hasNext();) {
			Map.Entry me = (Map.Entry)it.next();
			String gwportid = (String)me.getKey();
			StringBuffer sb = new StringBuffer();
			for (Iterator gwipIt = ((Set)me.getValue()).iterator(); gwipIt.hasNext();) {
				String rgwip = (String)gwipIt.next();
				sb.append("'"+rgwip+"',");
			}
			sb.deleteCharAt(sb.length()-1);
			Database.update("DELETE FROM gwportprefix WHERE gwportid='"+gwportid+"' AND gwip IN ("+sb.toString()+") AND gwip NOT IN (SELECT gwip FROM gwportprefix JOIN prefix USING(prefixid) JOIN vlan USING(vlanid) WHERE nettype='static')");
		}

		/*
		if (hasDeleted) {
			Database.update("DELETE FROM gwport WHERE masterindex IS NOT NULL AND gwportid NOT IN (SELECT gwportid FROM gwportprefix)");
			Database.update("DELETE FROM gwport WHERE masterindex IS NULL AND ifindex NOT IN (SELECT masterindex FROM gwport WHERE masterindex IS NOT NULL AND moduleid = gwport.moduleid) AND gwportid NOT IN (SELECT gwportid FROM gwportprefix)");
		}
		*/
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
