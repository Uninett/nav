package no.ntnu.nav.eventengine.deviceplugins.Netel;

import java.util.*;
import java.sql.*;
import no.ntnu.nav.Database.*;

import no.ntnu.nav.eventengine.*;
import no.ntnu.nav.eventengine.deviceplugins.Box.*;

public class Netel extends Box
{
	protected static final boolean DEBUG_OUT = true;

	public static final int MODULE_STATUS_UP = 0;
	public static final int MODULE_STATUS_DOWN = 10;
	protected int moduleStatus;
	private int moduleDownCount;

	List modules = new ArrayList();
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
			errl("Exception: " + e.getMessage());
			e.printStackTrace(System.err);
			throw new RuntimeException(e.getMessage());
		}

		outld("Netel.updateFromDB");
		ResultSet rs = Database.query("SELECT deviceid,netboxid,ip,sysname,vlan,up FROM netbox JOIN prefix USING(prefixid) WHERE catid IN ('SW','KANT')");

		while (rs.next()) {
			try {

			int deviceid = rs.getInt("deviceid");

			//outld("new Netel("+deviceid+")");

			Device d = (Device)ddb.getDevice(deviceid);
			if (d == null) {
				Netel n = new Netel(ddb, rs);
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
				errl("Exception: " + e.getMessage());
				e.printStackTrace(System.err);
				throw new RuntimeException(e.getMessage());
			}
		}

		// Module class
		try {
			Module.updateFromDB(ddb);
		} catch (Exception e) {
			errl("Exception: " + e.getMessage());
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
		modules.add(m);
	}
	protected void removeModule(Module m)
	{
		// If it is down, bring it up first
		moduleUp(m);
		modules.remove(m);
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
		return modules.iterator();
	}
	public Iterator getModulesDown()
	{
		return modulesDown.values().iterator();
	}

	// Override to avoid box going up if there is still modules down
	public void up()
	{
		super.up();
		if (moduleDownCount > 0) downMap.put(new Integer(boxid), this);
	}

	public String toString()
	{
		StringBuffer sb = new StringBuffer(super.toString());
		sb.append("\n  Netel ["+modules.size()+" modules]");
		for (Iterator i=modules.iterator(); i.hasNext();) {
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

		outld("reachableFrom: @"+sysname+", vlan="+vlan);

		// No downlink to overselves
		if (b == this) {
			foundDownlink = true;
			visited.add(getDeviceidI());
		} else {
			// If we are down, b is obviously not reachable from here :)
			if (!isUp()) return REACHABLE_NO;
		}

		for (Iterator i=modules.iterator(); reachable != REACHABLE_YES && i.hasNext();) {
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
			if (!m.isUp()) continue;

			outld("  Scan for uplink..., module: " + m.getModule());

			// Try to find an uplink which has the correct vlan reachable
			for (Iterator j=m.getPorts(); j.hasNext();) {
				Port p = (Port)j.next();
				int dir = p.vlanDirection(vlan);
				outld("    Port: " + p.getPort() + " dir: " + dir + " behind: " + p.getBoxidBehind() + "dev: " + boxidToDeviceid(p.getBoxidBehind()));
				if (dir != Port.DIRECTION_NONE && dir != Port.DIRECTION_DOWN) {
					Device d = devDB.getDevice(boxidToDeviceid(p.getBoxidBehind()));
					if (d instanceof Netel) {
						Netel n = (Netel)d;
						outld("  Reachable from uplink " + n.sysname + "?");

						// Visit this box if we have not already
						if (visited.add(n.getDeviceidI())) {
							int r = reachableFrom(this, vlan, visited);
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
						outld("  Error! Device not Netel: " + d);
					}
				}
			}

		}

		if (!foundDownlink) {
			errl("Netel.reachableFrom: Box " + b.getSysname() + " has uplink to " + sysname + ", but no downlink (on same vlan) found!");
		}

		return reachable;
	}


}
