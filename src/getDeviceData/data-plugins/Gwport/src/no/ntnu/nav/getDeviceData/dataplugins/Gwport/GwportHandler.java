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
			/*
			rs = Database.query("SELECT deviceid,serial,hw_ver,sw_ver,moduleid,module,netboxid,submodule,up,swport.swportid,port,ifindex,link,speed,duplex,media,trunk,portname,vlan,hexstring FROM device JOIN module USING (deviceid) LEFT JOIN swport USING (moduleid) LEFT JOIN swportallowedvlan USING (swportid) LEFT JOIN swportvlan ON (trunk='f' AND swport.swportid=swportvlan.swportid) ORDER BY moduleid");
			while (rs.next()) {
				SwModule md = new SwModule(rs.getString("serial"), rs.getString("hw_ver"), rs.getString("sw_ver"), rs.getString("module"));
				md.setDeviceid(rs.getInt("deviceid"));
				md.setModuleid(rs.getInt("moduleid"));
				md.setSubmodule(rs.getString("submodule"));

				int moduleid = rs.getInt("moduleid");
				if (rs.getString("port") != null && rs.getString("port").length() > 0) {
					do {
						Swport sd = new Swport(new Integer(rs.getInt("port")), rs.getString("ifindex"), rs.getString("link").charAt(0), rs.getString("speed"), rs.getString("duplex").charAt(0), rs.getString("media"), rs.getBoolean("trunk"), rs.getString("portname"));
						sd.setSwportid(rs.getInt("swportid"));
						sd.setVlan(rs.getInt("vlan") == 0 ? Integer.MIN_VALUE : rs.getInt("vlan"));
						sd.setHexstring(rs.getString("hexstring"));
						md.addSwport(sd);
					} while (rs.next() && rs.getInt("moduleid") == moduleid);
					rs.previous();
				}

				String key = rs.getString("netboxid")+":"+md.getKey();
				m.put(key, md);
			}
			*/
			Database.query("");
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

		try {

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
			Database.query("");

		} catch (SQLException e) {
			Log.e("HANDLE", "SQLException: " + e.getMessage());
			e.printStackTrace(System.err);
		}
	}

}
