package no.ntnu.nav.getDeviceData.dataplugins.Gwport;

import java.util.*;
import java.sql.*;

import no.ntnu.nav.logger.*;
import no.ntnu.nav.Database.*;
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

	private static final boolean DB_COMMIT = true;

	private static Map moduleMap;

	private static Map vlanMap;
	private static Map prefixMap;
	

	/**
	 * Fetch initial data from module/gwport/prefix/vlan tables.
	 */
	public synchronized void init(Map persistentStorage) {
		if (persistentStorage.containsKey("initDone")) return;
		persistentStorage.put("initDone", null);

		Map m;
		ResultSet rs;
		long dumpBeginTime,dumpUsedTime;

		Log.setDefaultSubsystem("GwportHandler");

		try {
			// module, gwport, prefix, vlan
			dumpBeginTime = System.currentTimeMillis();
			m = Collections.synchronizedMap(new HashMap());
			rs = Database.query("SELECT serial,hw_ver,sw_ver,moduleid,module,gwportid,ifindex,interface,masterindex,speed,ospf,prefixid,gwip,hsrp,host(netaddr) AS netaddr,masklen(netaddr) AS masklen,vlanid,vlan,nettype,orgid,usageid,netident,description FROM device JOIN module USING(deviceid) LEFT JOIN gwport USING(moduleid) LEFT JOIN gwportprefix USING(gwportid) LEFT JOIN prefix USING(prefixid) LEFT JOIN vlan USING(vlanid) ORDER BY moduleid,gwportid");
			while (rs.next()) {
				// Create module
				GwModule gwm = new GwModule(rs.getString("serial"), rs.getString("hw_ver"), rs.getString("sw_ver"), rs.getString("module"));
				gwm.setDeviceid(rs.getInt("deviceid"));
				gwm.setModuleid(rs.getInt("moduleid"));

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
							System.err.println("FOUND DUP VLAN!");
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

		System.err.println("Gwports for " + nb);

		try {
			for (Iterator gwModules = gc.getGwModules(); gwModules.hasNext();) {
				GwModule gwm = (GwModule)gwModules.next();

				System.err.println("  GwModule: " + gwm);
				
				for (Iterator gwPorts = gwm.getGwports(); gwPorts.hasNext();) {
					Gwport gwp = (Gwport)gwPorts.next();

					System.err.println("    Gwport: " + gwp);
					
					for (Iterator gwportPrefices = gwp.getGwportPrefices(); gwportPrefices.hasNext();) {
						Gwportprefix gp = (Gwportprefix)gwportPrefices.next();

						String gwip = gp.getGwip();
						boolean hsrp = gp.getHsrp();
						Prefix p = gp.getPrefix();
						Vlan vl = p.getVlan();

						System.err.println("      Gwip: " + gwip);
						System.err.println("      Hsrp: " + hsrp);
						System.err.println("      Prefix: " + p);
						System.err.println("      Vlan: " + vl);
					}
				}
			}
						

			/*
			for (Iterator swModules = sc.getSwModules(); swModules.hasNext();) {
				SwModule md = (SwModule)swModules.next();
				
				// OK, først sjekk om denne porten er i swport fra før
				String moduleKey = nb.getNetboxid()+":"+md.getKey();
				String moduleid = md.getModuleidS();
				SwModule oldmd = (SwModule)moduleMap.get(moduleKey);
				moduleMap.put(moduleKey, md);

				// Så alle swportene
				for (Iterator j = md.getSwports(); j.hasNext();) {
					Swport sd = (Swport)j.next();

					// Finn evt. gammel
					String swportid;
					Swport oldsd = (oldmd == null) ? null : oldmd.getSwport(sd.getPort());
					if (oldsd == null) {
						// Sett inn ny
						Log.i("NEW_SWPORT", "New swport: " + sd.getPort());
						ResultSet rs = Database.query("SELECT nextval('swport_swportid_seq') AS swportid");
						rs.next();
						swportid = rs.getString("swportid");

						Log.d("NEW_SWPORT", "New swport, swportid="+swportid+", moduleid="+moduleid+", port="+sd.getPort()+", ifindex="+sd.getIfindex()+", link="+sd.getLink()+", speed="+sd.getSpeed()+", duplex="+sd.getDuplexS()+", media="+Database.addSlashes(sd.getMedia())+", trunk="+sd.getTrunkS()+", portname="+Database.addSlashes(sd.getPortname()));


						String[] inss = {
							"swportid", swportid,
							"moduleid", moduleid,
							"port", sd.getPort().toString(),
							"ifindex", sd.getIfindex(),
							"link", String.valueOf(sd.getLink()),
							"speed", sd.getSpeed(),
							"duplex", sd.getDuplexS(),
							"media", Database.addSlashes(sd.getMedia()),
							"trunk", sd.getTrunkS(),
							"portname", Database.addSlashes(sd.getPortname())
						};
						if (DB_UPDATE) Database.insert("swport", inss);

					} else {
						swportid = oldsd.getSwportidS();
						if (!oldsd.equals(sd)) {
							// Vi må oppdatere
							Log.i("UPDATE_SWPORT", "Update swportid: "+swportid+" ifindex="+sd.getIfindex());
							String[] set = {
								"ifindex", sd.getIfindex(),
								"link", String.valueOf(sd.getLink()),
								"speed", sd.getSpeed(),
								"duplex", sd.getDuplexS(),
								"media", Database.addSlashes(sd.getMedia()),
								"trunk", sd.getTrunkS(),
								"portname", Database.addSlashes(sd.getPortname())
							};
							String[] where = {
								"swportid", swportid
							};
							Database.update("swport", set, where);
						}
					}
					sd.setSwportid(swportid);

					if (!sd.getTrunk()) {
						if (oldsd != null && oldsd.getTrunk()) {
							// Går fra trunk -> non-trunk, slett alle så nær som et vlan fra swportvlan
							Database.update("DELETE FROM swportvlan WHERE swportid="+sd.getSwportid()+" AND vlan!=(SELCT MIN(vlan) FROM swportvlan WHERE swportid="+sd.getSwportid()+" GROUP BY swportid)");
						}

						// Også oppdater swportvlan
						if (oldsd == null || oldsd.getVlan() == Integer.MIN_VALUE) {
							if (sd.getVlan() <= 0) sd.setVlan(1);
							Database.update("INSERT INTO swportvlan (swportid,vlan) VALUES ('"+sd.getSwportid()+"','"+sd.getVlan()+"')");
						} else if (sd.getVlan() > 0 && oldsd.getVlan() != sd.getVlan()) {
							Database.update("UPDATE swportvlan SET vlan = '"+sd.getVlan()+"' WHERE swportid = '"+sd.getSwportid()+"'");
						}

						// Slett evt. fra swportallowedvlan
						if (oldsd != null && oldsd.getHexstring().length() > 0) {
							Database.update("DELETE FROM swportallowedvlan WHERE swportid='"+sd.getSwportid()+"'");
						}

					} else {
						// Trunk, da må vi evt. oppdatere swportallowedvlan
						if (sd.getHexstring().length() > 0) {
							if (oldsd == null || oldsd.getHexstring().length() == 0) {
								Database.update("INSERT INTO swportallowedvlan (swportid,hexstring) VALUES ('"+sd.getSwportid()+"','"+sd.getHexstring()+"')");
							} else if (!oldsd.getHexstring().equals(sd.getHexstring())) {
								Database.update("UPDATE swportallowedvlan SET hexstring = '"+sd.getHexstring()+"' WHERE swportid = '"+sd.getSwportid()+"'");
							}
						}
					}

				}

				if (DB_COMMIT) Database.commit(); else Database.rollback();

			}
			*/
			Database.query("SELECT 1");

		} catch (SQLException e) {
			Log.e("HANDLE", "SQLException: " + e.getMessage());
			e.printStackTrace(System.err);
		}
	}

}
