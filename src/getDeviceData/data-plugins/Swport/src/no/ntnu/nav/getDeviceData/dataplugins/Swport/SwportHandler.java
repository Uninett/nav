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

	private static Map moduleMap;
	private static Map swportMap;

	/**
	 * Fetch initial data from swport table.
	 */
	public synchronized void init(Map persistentStorage, Set changedDeviceids) {
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
			rs = Database.query("SELECT deviceid,serial,hw_ver,sw_ver,moduleid,module,netboxid,descr,up,swport.swportid,ifindex,port,interface,link,speed,duplex,media,trunk,portname,vlan,hexstring FROM device JOIN module USING (deviceid) LEFT JOIN swport USING (moduleid) LEFT JOIN swportallowedvlan USING (swportid) ORDER BY moduleid");
			while (rs.next()) {
				SwModule md = new SwModule(rs.getString("serial"), rs.getString("hw_ver"), rs.getString("sw_ver"), rs.getInt("module"), null);
				md.setDeviceid(rs.getInt("deviceid"));
				md.setModuleid(rs.getInt("moduleid"));
				md.setDescr(rs.getString("descr"));

				int moduleid = rs.getInt("moduleid");
				if (rs.getString("ifindex") != null && rs.getString("ifindex").length() > 0) {
					do {
						Swport sd = new Swport(rs.getString("ifindex"));
						sd.setSwportid(rs.getInt("swportid"));
						
						if (rs.getString("port") != null) sd.setPort(new Integer(rs.getInt("port")));
						if (rs.getString("link") != null) sd.setLink(rs.getString("link").charAt(0));
						sd.setSpeed(rs.getString("speed"));
						if (rs.getString("duplex") != null) sd.setDuplex(rs.getString("duplex").charAt(0));
						sd.setMedia(rs.getString("media"));
						sd.setPortname(rs.getString("portname"));
						sd.setInterface(rs.getString("interface"));
						if (rs.getString("vlan") != null) sd.setVlan(rs.getInt("vlan"));
						if (rs.getString("trunk") != null) sd.setTrunk(rs.getBoolean("trunk"));
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
			}
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
	public void handleData(Netbox nb, DataContainer dc, Set changedDeviceids) {
		if (!(dc instanceof SwportContainer)) return;
		SwportContainer sc = (SwportContainer)dc;
		if (!sc.isCommited()) return;

		// Assign any module-less swports to module 1
		sc.assignSwportsWithoutModule();

		// Let ModuleHandler update the module table first
		ModuleHandler mh = new ModuleHandler();
		mh.handleData(nb, dc, changedDeviceids);

		Log.setDefaultSubsystem("SwportHandler");
		int newcnt = 0, updcnt = 0;

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

					// Check if this swport should be ignored
					if (sc.getIgnoreSwport(sd.getIfindex())) continue;

					// Finn evt. gammel
					String swportid;
					String swportKey = nb.getNetboxid()+":"+sd.getIfindex();

					SwModule oldmd = (SwModule)swportMap.get(swportKey);
					Swport oldsd = (oldmd == null) ? null : oldmd.getSwport(sd.getIfindex());
					swportMap.put(swportKey, md);
					
					if (oldsd == null) {
						// Sett inn ny
						ResultSet rs = Database.query("SELECT nextval('swport_swportid_seq') AS swportid");
						rs.next();
						swportid = rs.getString("swportid");

						Log.d("NEW_SWPORT", "New swport, swportid="+swportid+", moduleid="+moduleid+", port="+sd.getPort()+", ifindex="+sd.getIfindex()+", link="+sd.getLink()+", speed="+sd.getSpeed()+", duplex="+sd.getDuplexS()+", media="+Database.addSlashes(sd.getMedia())+", trunk="+sd.getTrunkS()+", portname="+Database.addSlashes(sd.getPortname()));

						String[] inss = {
							"swportid", swportid,
							"moduleid", moduleid,
							"port", sd.getPortS(),
							"ifindex", sd.getIfindex(),
							"interface", Database.addSlashes(sd.getInterface()),
							"link", sd.getLinkS(),
							"speed", sd.getSpeed(),
							"duplex", sd.getDuplexS(),
							"media", Database.addSlashes(sd.getMedia()),
							"vlan", sd.getVlanS(),
							"trunk", sd.getTrunkS(),
							"portname", Database.addSlashes(sd.getPortname())
						};
						Database.insert("swport", inss);
						changedDeviceids.add(md.getDeviceidS());
						newcnt++;

					} else {
						swportid = oldsd.getSwportidS();
						if (!sd.equalsSwport(oldsd) || md.getModuleid() != oldmd.getModuleid()) {
							// Vi må oppdatere
							Log.d("UPDATE_SWPORT", "Update swportid: "+swportid+" ifindex="+sd.getIfindex());
							Log.d("UPDATE_SWPORT", "Old: " + oldsd + ", New: " + sd);
							String[] set = {
								"moduleid", md.getModuleidS(),
								"ifindex", sd.getIfindex(),
								"port", sd.getPortS(),
								"interface", Database.addSlashes(sd.getInterface()),
								"link", sd.getLinkS(),
								"speed", sd.getSpeed(),
								"duplex", sd.getDuplexS(),
								"media", Database.addSlashes(sd.getMedia()),
								"vlan", sd.getVlanS(),
								"trunk", sd.getTrunkS(),
								"portname", Database.addSlashes(sd.getPortname())
							};
							String[] where = {
								"swportid", swportid
							};
							Database.update("swport", set, where);
							changedDeviceids.add(md.getDeviceidS());
							updcnt++;
						}
					}
					sd.setSwportid(swportid);

					if (sd.getTrunk() != null && !sd.getTrunk().booleanValue()) {
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

			}

		} catch (SQLException e) {
			Log.e("HANDLE", "SQLException: " + e.getMessage());
			e.printStackTrace(System.err);
		}

		if (newcnt > 0 || updcnt > 0) {
			Log.i("HANDLE", nb.getSysname() + ": New: " + newcnt + ", Updated: " + updcnt);
		}

	}

}
