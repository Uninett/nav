package no.ntnu.nav.getDeviceData.dataplugins.Swport;

import java.util.*;
import java.sql.*;

import no.ntnu.nav.logger.*;
import no.ntnu.nav.Database.*;
import no.ntnu.nav.getDeviceData.Netbox;
import no.ntnu.nav.getDeviceData.dataplugins.*;
import no.ntnu.nav.getDeviceData.dataplugins.Module.ModuleHandler;

/**
 * DataHandler plugin for getDeviceData; provides an interface for storing
 * switch data, which includes modules and switch ports.
 *
 * @see SwportContainer
 */

public class SwportHandler implements DataHandler {

	private static final boolean DB_UPDATE = true;
	private static final boolean DB_COMMIT = true;

	private static Map moduleMap;
	private static Map swportMap;
	

	/**
	 * Fetch initial data from swport table.
	 */
	public synchronized void init(Map persistentStorage) {
		if (persistentStorage.containsKey("initDone")) return;
		persistentStorage.put("initDone", null);

		Map m;
		Map swpMap;
		ResultSet rs;
		long dumpBeginTime,dumpUsedTime;

		Log.setDefaultSubsystem("SwportHandler");

		try {
		
			// module, swport
			dumpBeginTime = System.currentTimeMillis();
			m = Collections.synchronizedMap(new HashMap());
			swpMap = Collections.synchronizedMap(new HashMap());
			rs = Database.query("SELECT deviceid,serial,hw_ver,sw_ver,moduleid,module,netboxid,submodule,up,swport.swportid,port,ifindex,link,speed,duplex,media,trunk,portname,vlan,hexstring FROM device JOIN module USING (deviceid) LEFT JOIN swport USING (moduleid) LEFT JOIN swportallowedvlan USING (swportid) LEFT JOIN swportvlan ON (trunk='f' AND swport.swportid=swportvlan.swportid) ORDER BY moduleid");
			while (rs.next()) {
				SwModule md = new SwModule(rs.getString("serial"), rs.getString("hw_ver"), rs.getString("sw_ver"), rs.getString("module"), null);
				md.setDeviceid(rs.getInt("deviceid"));
				md.setModuleid(rs.getInt("moduleid"));
				md.setSubmodule(rs.getString("submodule"));

				int moduleid = rs.getInt("moduleid");
				if (rs.getString("ifindex") != null && rs.getString("ifindex").length() > 0) {
					do {
						Swport sd = new Swport(rs.getString("ifindex"));
						sd.setData(rs.getString("port") == null ? new Integer(0) : new Integer(rs.getInt("port")), rs.getString("link") == null ? 'x' : rs.getString("link").charAt(0), rs.getString("speed"), rs.getString("duplex") == null ? 'x' : rs.getString("duplex").charAt(0), rs.getString("media"), rs.getBoolean("trunk"), rs.getString("portname"));
						sd.setSwportid(rs.getInt("swportid"));
						sd.setVlan(rs.getInt("vlan") == 0 ? Integer.MIN_VALUE : rs.getInt("vlan"));
						sd.setHexstring(rs.getString("hexstring"));
						md.addSwport(sd);
						String key = rs.getString("netboxid")+":"+rs.getString("ifindex");
						if (swpMap.containsKey(key)) {
							System.err.println("ERROR! Non-unique ifindex, deleting...");
							Database.update("DELETE FROM swport WHERE swportid="+rs.getString("swportid"));
						} else {
							swpMap.put(rs.getString("netboxid")+":"+rs.getString("ifindex"), md);
						}
					} while (rs.next() && rs.getInt("moduleid") == moduleid);
					rs.previous();
				}

				//String key = rs.getString("netboxid")+":"+md.getKey();
				//m.put(key, md);
			}
			Database.commit();
			//moduleMap = m;
			swportMap = swpMap;
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
		return new SwportContainer(this);
	}
	
	/**
	 * Store the data in the DataContainer in the database.
	 */
	public void handleData(Netbox nb, DataContainer dc) {
		if (!(dc instanceof SwportContainer)) return;
		SwportContainer sc = (SwportContainer)dc;
		if (!sc.isCommited()) return;

		// Assign any module-less swports to module 1
		sc.assignSwportsWithoutModule();

		// Let ModuleHandler update the module table first
		ModuleHandler mh = new ModuleHandler();
		mh.handleData(nb, dc);

		Log.setDefaultSubsystem("SwportHandler");

		try {

			for (Iterator swModules = sc.getSwModules(); swModules.hasNext();) {
				SwModule md = (SwModule)swModules.next();
				String moduleid = md.getModuleidS();
				
				// OK, først sjekk om denne porten er i swport fra før
				/*
				String moduleKey = nb.getNetboxid()+":"+md.getKey();
				SwModule oldmd = (SwModule)moduleMap.get(moduleKey);
				moduleMap.put(moduleKey, md);
				*/

				// Så alle swportene
				for (Iterator j = md.getSwports(); j.hasNext();) {
					Swport sd = (Swport)j.next();

					// Finn evt. gammel
					String swportid;
					//Swport oldsd = (oldmd == null) ? null : oldmd.getSwport(sd.getIfindex());

					SwModule oldmd = (SwModule)swportMap.get(nb.getNetboxid()+":"+sd.getIfindex());
					Swport oldsd = (oldmd == null) ? null : oldmd.getSwport(sd.getIfindex());
					swportMap.put(sd.getIfindex(), md);
					
					if (oldsd == null) {
						// Sett inn ny
						Log.i("NEW_SWPORT", "New swport: " + sd);
						ResultSet rs = Database.query("SELECT nextval('swport_swportid_seq') AS swportid");
						rs.next();
						swportid = rs.getString("swportid");

						Log.d("NEW_SWPORT", "New swport, swportid="+swportid+", moduleid="+moduleid+", port="+sd.getPort()+", ifindex="+sd.getIfindex()+", link="+sd.getLink()+", speed="+sd.getSpeed()+", duplex="+sd.getDuplexS()+", media="+Database.addSlashes(sd.getMedia())+", trunk="+sd.getTrunkS()+", portname="+Database.addSlashes(sd.getPortname()));


						String[] inss = {
							"swportid", swportid,
							"moduleid", moduleid,
							"port", sd.getPortS(),
							"ifindex", sd.getIfindex(),
							"link", sd.getLinkS(),
							"speed", sd.getSpeed(),
							"duplex", sd.getDuplexS(),
							"media", Database.addSlashes(sd.getMedia()),
							"trunk", sd.getTrunkS(),
							"portname", Database.addSlashes(sd.getPortname())
						};
						if (DB_UPDATE) Database.insert("swport", inss);

					} else {
						swportid = oldsd.getSwportidS();
						if (!sd.equalsSwport(oldsd) || md.getModuleid() != oldmd.getModuleid()) {
							// Vi må oppdatere
							Log.i("UPDATE_SWPORT", "Update swportid: "+swportid+" ifindex="+sd.getIfindex());
							String[] set = {
								"moduleid", md.getModuleidS(),
								"ifindex", sd.getIfindex(),
								"port", sd.getPortS(),
								"link", sd.getLinkS(),
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

					if (sd.getTrunk() != null && !sd.getTrunk().booleanValue()) {
						if (oldsd != null && oldsd.getTrunk().booleanValue()) {
							// Går fra trunk -> non-trunk, slett alle så nær som et vlan fra swportvlan
							Database.update("DELETE FROM swportvlan WHERE swportid="+sd.getSwportid()+" AND vlan!=(SELCT MIN(vlan) FROM swportvlan WHERE swportid="+sd.getSwportid()+" GROUP BY swportid)");
						}

						// Også oppdater swportvlan
						if (oldsd == null || (oldsd.getVlan() != null && oldsd.getVlan().intValue() == Integer.MIN_VALUE)) {
							if (sd.getVlan() == null || sd.getVlan().intValue() <= 0) sd.setVlan(1);
							Database.update("INSERT INTO swportvlan (swportid,vlan) VALUES ('"+sd.getSwportid()+"','"+sd.getVlan()+"')");
						} else if (sd.getVlan() != null && sd.getVlan().intValue() > 0 && oldsd.getVlan() != null && oldsd.getVlan().intValue() != sd.getVlan().intValue()) {
							Database.update("UPDATE swportvlan SET vlan = '"+sd.getVlan()+"' WHERE swportid = '"+sd.getSwportid()+"'");
						}

						// Slett evt. fra swportallowedvlan
						if (oldsd != null && oldsd.getHexstring().length() > 0) {
							Database.update("DELETE FROM swportallowedvlan WHERE swportid='"+sd.getSwportid()+"'");
						}

					} else if (sd.getTrunk() != null) {
						// Trunk, da må vi evt. oppdatere swportallowedvlan
						if (sd.getHexstring().length() > 0) {
							if (oldsd == null || oldsd.getHexstring().length() == 0) {
								Database.update("INSERT INTO swportallowedvlan (swportid,hexstring) VALUES ('"+sd.getSwportid()+"','"+Database.addSlashes(sd.getHexstring())+"')");
							} else if (!oldsd.getHexstring().equals(sd.getHexstring())) {
								Database.update("UPDATE swportallowedvlan SET hexstring = '"+Database.addSlashes(sd.getHexstring())+"' WHERE swportid = '"+sd.getSwportid()+"'");
							}
						}
					}

				}

				if (DB_COMMIT) Database.commit(); else Database.rollback();

			}

		} catch (SQLException e) {
			Log.e("HANDLE", "SQLException: " + e.getMessage());
			e.printStackTrace(System.err);
		}
	}

}
