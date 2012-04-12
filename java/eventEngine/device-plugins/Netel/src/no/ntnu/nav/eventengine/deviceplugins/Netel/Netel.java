package no.ntnu.nav.eventengine.deviceplugins.Netel;

import java.util.*;
import java.sql.*;

import no.ntnu.nav.Database.*;
import no.ntnu.nav.logger.*;
import no.ntnu.nav.eventengine.*;
import no.ntnu.nav.eventengine.deviceplugins.Box.*;

public class Netel extends Box
{
	public static final int MODULE_STATUS_UP = 0;
	public static final int MODULE_STATUS_DOWN = 10;
	protected int moduleStatus;
	private int moduleDownCount;

	//List modules = new ArrayList();
	Map modules = new HashMap();
	Map modulesDown = new HashMap();

	protected Netel() { }

	public Netel(DeviceDB devDB, ResultSet rs) throws SQLException
	{
		this(devDB, rs, null);
	}

	public Netel(DeviceDB devDB, ResultSet rs, Device d) throws SQLException
	{
		super(devDB, rs, d);
		update(rs);

		if (d instanceof Netel) {
			Netel n = (Netel)d;
			//status = b.status;
		}
	}


	/*
	private void update(ResultSet rs) throws SQLException
	{

	}
	*/

	public static void updateFromDB(DeviceDB ddb) throws SQLException
	{
		/* Since only the updateFromDB() methods in the plugin class is invoked, we need to also
		 * invoke this methods for the other classes in this plugin. The order is important.
		 * (yes, these classes should go into their own plugins; then event engine will take
		 * care of the ordering automatically)
		 */
		// Gw class
		try {
			Gw.updateFromDB(ddb);
		} catch (Exception e) {
			Log.e("NETEL_DEVICEPLUGIN", "UPDATE_FROM_DB", "Exception while calling Gw.updateFromDB: " + e.getMessage());
			e.printStackTrace(System.err);
			throw new RuntimeException(e.getMessage());
		}

		Log.d("NETEL_DEVICEPLUGIN", "UPDATE_FROM_DB", "Fetching all netboxes from database");
		ResultSet rs = Database.query(
				"SELECT deviceid,netboxid,ip,sysname,vlan,up, " +
				"       CASE WHEN maintenance > 0 THEN TRUE ELSE FALSE END AS on_maintenance " +
				"FROM netbox " +
				"LEFT JOIN netboxprefix USING (netboxid) " +
				"LEFT JOIN prefix USING(prefixid) " +
				"LEFT JOIN vlan USING(vlanid) " +
				"LEFT JOIN (SELECT netboxid, count(*) as maintenance " +
				"           FROM alerthist " +
				"           WHERE eventtypeid='maintenanceState' " +
				"             AND end_time='infinity' " +
				"           GROUP BY netboxid) maintaggr USING (netboxid) " +
				"WHERE catid IN ('SW','EDGE','WLAN','SRV','OTHER')");

		while (rs.next()) {
			try {

			int deviceid = rs.getInt("deviceid");

			Device d = (Device)ddb.getDevice(deviceid);
			if (d == null) {
				Netel n = new Netel(ddb, rs);
				ddb.putDevice(n);
			} else if (classEq(d, new Module())) {
				// Add the module and then overwrite
				Netel n = new Netel(ddb, rs, d);
				n.addModule((Module)d);
				ddb.putDevice(n);					
			} else if (!ddb.isTouchedDevice(d)) {
				if (classEq(d, new Netel())) {
					((Netel)d).update(rs);
					ddb.touchDevice(d);
				} else {
					Netel n = new Netel(ddb, rs, d);
					ddb.putDevice(n);
				}
			}

			} catch (Exception e) {
				Log.e("NETEL_DEVICEPLUGIN", "UPDATE_FROM_DB", "Exception while creating devices: " + e.getMessage());
				e.printStackTrace(System.err);
				throw new RuntimeException(e.getMessage());
			}
		}

		// Module class
		try {
			Module.updateFromDB(ddb);
		} catch (Exception e) {
			Log.e("NETEL_DEVICEPLUGIN", "UPDATE_FROM_DB", "Exception while calling Module.updateFromDB: " + e.getMessage());
			e.printStackTrace(System.err);
			throw new RuntimeException(e.getMessage());
		}

	}
	/*
	public void init(DeviceDb ddb)
	{


	}
	*/

	protected void addModule(Module m)
	{
		modules.put(m.getDeviceidI(), m);
		//if (!m.isUp()) moduleDown(m);
	}
	protected void removeModule(Module m)
	{
		// If it is down, bring it up first
		//moduleUp(m);
		modules.remove(m.getDeviceidI());
	}
	public Module getModule(int deviceid)
	{
		return (Module)modules.get(new Integer(deviceid));
	}
	protected Set getModuleIdSet()
	{
		return modules.keySet();
	}
	protected void moduleDown(Module m)
	{
		if (modulesDown.containsKey(m.getDeviceidI())) return;
		if (moduleDownCount++ == 0) {
			downMap.put(new Integer(boxid), this);
			moduleStatus = MODULE_STATUS_DOWN;
		}
		modulesDown.put(m.getDeviceidI(), m);
	}
	protected void moduleUp(Module m)
	{
		if (!modulesDown.containsKey(m.getDeviceidI())) return;
		if (--moduleDownCount == 0) {
			if (isUp()) downMap.remove(new Integer(boxid));
			moduleStatus = MODULE_STATUS_UP;
		}
		modulesDown.remove(m.getDeviceidI());
	}
	protected Iterator getModules()
	{
		return modules.values().iterator();
	}
	public Iterator getModulesDown()
	{
		return modulesDown.values().iterator();
	}

	// Override to avoid box going up if there are still modules down
	public void up()
	{
		super.up();
		if (moduleDownCount > 0) downMap.put(new Integer(boxid), this);
	}

	public String toString()
	{
		StringBuffer sb = new StringBuffer(super.toString());
		sb.append("\n  Netel ["+modules.size()+" modules]");
		for (Iterator i=modules.values().iterator(); i.hasNext();) {
			sb.append("\n    "+i.next());
		}
		return sb.toString();
	}

	/**
	 * Overridden from superclass. We ask all uplinks recursivly if this box is reachable from it,
	 * and if one of them says yes, then we are not in shadow.
	 *
	 */
	public void updateStatus()
	{
		super.updateStatus();
		if (isUp()) return;

		if (reachableFrom(this, vlan, new HashSet()) == REACHABLE_NO) {
			shadow();
		}
		outld("");
	}

	protected static final int REACHABLE_YES = 0; 
	protected static final int REACHABLE_NO = 1; 
	protected static final int REACHABLE_UNKNOWN = 2; 

	/**
	 * Check if b is reachable from this Netel.
	 *
	 * @return REACHABLE_YES if b is reachable from this Netel; REACHABLE_NO if not; or REACHABLE_UNKNOWN if we don't know
	 */
	protected int reachableFrom(Box b, int vlan, Set visited)
	{

		boolean foundDownlink = false;
		int reachable = REACHABLE_UNKNOWN;

		outld("reachableFrom: @"+sysname+", vlan="+vlan + ", b="+b.getSysname() + ", modules="+modules.size());

		// No downlink to overselves
		if (b == this) {
			foundDownlink = true;
			visited.add(getDeviceidI());
		} else {
			// If we are down, b is obviously not reachable from here :)
			if (!isUp()) outld("  No. (down)");
			if (!isUp()) return REACHABLE_NO;
		}

		for (Iterator i=modules.values().iterator(); reachable != REACHABLE_YES && i.hasNext();) {
			Module m = (Module)i.next();
			// Verify that we have a downlink to b on the correct vlan
			for (Iterator j=m.getPortsTo(b); !foundDownlink && j.hasNext();) {
				Port p = (Port)j.next();
				int dir = p.vlanDirection(vlan);
				if (dir != Port.DIRECTION_NONE && dir != Port.DIRECTION_UP) {
					// This port is a downlink to b on the correct vlan
					foundDownlink = true;
				}
			}

			// If the module is down there is no point in checking its ports
			if (!m.isUp()) outld("  Skip module.");
			if (!m.isUp()) continue;

			outld("  Scan for uplink..., module: " + m.getModule() + " (" + m.getPortCount()+" ports)");

			// Try to find an uplink which has the correct vlan reachable
			for (Iterator j=m.getPorts(); j.hasNext();) {
				Port p = (Port)j.next();
				if (p.getBoxidBehind() == 0) continue;

				int dir = p.vlanDirection(vlan);
// 				if (p.getBoxidBehind() != 0) {
// 					Device d = devDB.getDevice(boxidToDeviceid(p.getBoxidBehind()));
// 					if (d instanceof Netel) {
// 						Netel n = (Netel)d;
// 						outld("    Ifindex: " + p.getIfindex() + " Port: " + p.getPort() + " dir: " + dir + " behind: " + p.getBoxidBehind() + " dev: " + boxidToDeviceid(p.getBoxidBehind()) + " name: " + (n!=null?n.getSysname():"NA") );
// 					} else {
// 						System.err.println("    Device is not instance of Netel: " + d);
// 					}
// 				}
				if (dir != Port.DIRECTION_NONE && dir != Port.DIRECTION_DOWN) {
					Device d = devDB.getDevice(boxidToDeviceid(p.getBoxidBehind()));
					if (d instanceof Netel) {
						Netel n = (Netel)d;
						outld("  Reachable from uplink " + n.sysname + "?");

						// Visit this box if we have not already
						if (visited.add(n.getDeviceidI())) {
							int r = n.reachableFrom(this, vlan, visited);
							if (r == REACHABLE_YES) {
								outld("  Yes.");
								reachable = r;
								break;
							}
							if (r == REACHABLE_NO) {
								outld("  No.");
								reachable = r;
							} else {
								outld("  Unknown.");
							}
						}
					} else {
						//outld("  Error! Device not Netel: " + d);
						System.err.println("  Error! Device not Netel: " + d + ", this: " + this + " port: " + p + ", dir: " + dir);
					}
				}
			}

		}

		if (!foundDownlink) {
			Log.w("NETEL_DEVICEPLUGIN", "Box " + b.getSysname() + " has uplink to " + sysname + ", but no downlink (on same vlan) found!");
		}

		return reachable;
	}

	static void outld(String s) {
		//System.err.println(s);
	}

	public Port getPort(int interfaceid) {
		Log.d("BOX_DEVICEPLUGIN", "GET_PORT", "Fetching port w/interfaceid=" + interfaceid);
		try {
			ResultSet rs = Database.query(
					"SELECT " +
					"  netbox.deviceid AS parent_deviceid, " +
					"  '' AS name, " +
					"  ifindex, " +
					"  baseport AS port, " +
					"  to_netboxid, " +
					"  vlan.vlan, " +
					"  direction " +
					"FROM interface " +
					"JOIN netbox USING (netboxid) " +
					"LEFT JOIN swportvlan USING (interfaceid) " +
					"LEFT JOIN vlan USING (vlanid) " +
					"WHERE interfaceid=" + interfaceid +" AND netboxid="+boxid);
			if (rs.next()) {
				Port p = new Port(rs);
				return p;
			}
		} catch (SQLException e) { }
		return null;
	}

}
