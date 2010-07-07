package no.ntnu.nav.eventengine.deviceplugins.Netel;

import java.util.*;
import java.sql.*;

import no.ntnu.nav.Database.*;
import no.ntnu.nav.logger.*;
import no.ntnu.nav.eventengine.*;
import no.ntnu.nav.eventengine.deviceplugins.Box.*;

public class Module extends Device
{
	protected static final boolean DEBUG_OUT = true;
	protected static final boolean VERBOSE_TOSTRING = false;

	protected int parentDeviceid;
	protected int parentBoxid;
	protected String module;
	protected boolean status = true; // default is up
	protected Netel parent;
	protected Map ports = new HashMap();

	protected Module() { }

	/*
	public Module(DeviceDB devDB, ResultSet rs) throws SQLException
	{
		this(devDB, rs, null);
	}
	*/

	public Module(DeviceDB devDB, ResultSet rs, Netel parent) throws SQLException
	{
		super(devDB, rs, null);
		update(rs);

		this.parent = parent;
		/*
		if (d instanceof Module) {
			Module m = (Module)d;
			status = m.status;
		}
		*/
	}

	protected void update(ResultSet rs) throws SQLException
	{
		parentDeviceid = rs.getInt("parent_deviceid");
		parentBoxid = rs.getInt("parent_netboxid");
		module = rs.getString("module");
		status = "y".equals(rs.getString("up"));
		if (rs.getString("swportid") != null) {
			do {
				//errl("Debug " + deviceid + ", Module("+module+"): New port: " + rs.getInt("port"));
				Port p;
				if ( (p=(Port)ports.get(Port.getKey(rs))) != null) {
					p.update(rs);
				} else {
					p = new Port(rs);
					ports.put(p.getKey(), p);
				}
			} while (rs.next() && rs.getInt("parent_deviceid") == parentDeviceid && rs.getString("module").equals(module));
			rs.previous();
		}
	}

	public static void updateFromDB(DeviceDB ddb) throws SQLException
	{
		Log.d("MODULE_DEVICEPLUGIN", "UPDATE_FROM_DB", "Fetching all modules from database");
		ResultSet rs = Database.query("SELECT " +
		                              "  module.deviceid, " +
					      "  netbox.deviceid AS parent_deviceid, " +
					      "  module.netboxid AS parent_netboxid, " +
					      "  module, " +
					      "  module.up, " +
					      "  interfaceid AS swportid, " +
					      "  ifindex, " +
					      "  baseport AS port, " +
					      "  to_netboxid, " +
					      "  vlan.vlan, " +
					      "  direction " +
					      "FROM module " +
					      "JOIN netbox USING (netboxid) " +
					      "LEFT JOIN interface USING (moduleid) " +
					      "LEFT JOIN swportvlan USING (interfaceid) " +
					      "LEFT JOIN vlan USING (vlanid) " +
					      "ORDER BY " +
					      "  moduleid, " +
					      "  module, " +
					      "  ifindex");

		while (rs.next()) {
			int deviceid = rs.getInt("deviceid");

			Device p = (Device)ddb.getDevice(rs.getInt("parent_Deviceid"));
			if (p instanceof Netel) {
				Netel np = (Netel)p;
				Module m = np.getModule(rs.getInt("deviceid"));
				if (m != null) {
					m.update(rs);
				} else {
					m = new Module(ddb, rs, np);
					np.addModule(m);
				}
			}

			//outld("new Module("+deviceid+")");
			/*
			if (rs.getInt("parent_deviceid") == 278) {
				rs.previous();
				rs.previous();
				errl("Boxid: " + rs.getInt("parent_deviceid") + " Port: " + rs.getInt("port") + " parent: " + rs.getInt("to_netboxid"));
				rs.next();
				rs.next();
			}
			*/

			/*
			Device d = (Device)ddb.getDevice(deviceid);
			if (d == null) {
				Module m = new Module(ddb, rs);
				ddb.putDevice(m);
			} else if (classEq(d, new Netel())) {
				// Add ourselves to the netbox
				Module m = new Module(ddb, rs, d);
				((Netel)d).addModule(m);
			} else if (!ddb.isTouchedDevice(d)) {
				if (classEq(d, new Module())) {
					((Module)d).update(rs);
					ddb.touchDevice(d);
				} else {
					Module m = new Module(ddb, rs, d);
					ddb.putDevice(m);
				}
			}
			*/
		}
	}

	/*
	public void init(DeviceDB ddb)
	{
		Device d = (Device)ddb.getDevice(parentDeviceid);
		if (d instanceof Netel) {
			parent = (Netel)d;
			parent.addModule(this);
		} else {
			Log.w("MODULE_DEVICEPLUGIN", "INIT", "ParentDeviceid="+parentDeviceid+" is not an instance of Netel ("+d+")!");
			return;
		}
	}
	*/

	/**
	 * Return the deviceid of the box this module is part of.
	 */
	public int getParentDeviceid() {
		return parentDeviceid;
	}

	public void remove(DeviceDB ddb)
	{
		if (parent != null) {
			parent.removeModule(this);
		}
	}

	public void down()
	{
		boolean prevStatus = status;
		status = false;
		updateDbModuleStatus(status != prevStatus);
		parent.moduleDown(this);
	}
	public void up()
	{
		status = true;
		updateDbModuleStatus(true);
		parent.moduleUp(this);
	}
	public boolean isUp()
	{
		return status;
	}

	// If changeStatus is true and the module is down we do not want to
	// overwrite a previously set downsince and this has to check this
	// condition
	private void updateDbModuleStatus(boolean changeStatus)
	{
		char c = status ? 'y' : 'n';
		String downsince;
		if (status) {
			downsince = "null";
		} else if (changeStatus) {
			downsince = "now()";
		} else {
			// Check if we should update or not
			try {
				ResultSet rs = Database.query("SELECT downsince FROM module WHERE deviceid="+deviceid);
				if (rs.next() && rs.getString("downsince") != null) {
					downsince = "downsince";
				} else {
					downsince = "now()";
				}
			} catch (SQLException e) {
				Log.w("MODULE_DEVICEPLUGIN", "UPDATE_DB_MODULE_STATUS", "Could not read previous downsince for deviceid=" + deviceid);
				downsince = "now()";
			}
		}
		
		try {
			Database.update("UPDATE module SET up='"+c+"', downsince = "+downsince+" WHERE deviceid="+deviceid);
		} catch (SQLException e) {
			Log.w("MODULE_DEVICEPLUGIN", "UPDATE_DB_MODULE_STATUS", "Could not change status for deviceid=" + deviceid);
		}
	}


	public String getModule()
	{
		return module;
	}

	public Port getPort(int ifindex)
	{
		return (Port)ports.get(new Integer(ifindex));
	}
	public int getPortCount()
	{
		return ports.size();
	}
	public Iterator getPorts()
	{
		return ports.values().iterator();
	}
	public Iterator getPortsTo(Box b)
	{
		int boxid = b.getBoxid();

		List l = new ArrayList();
		for (Iterator i=getPorts(); i.hasNext();) {
			Port p = (Port)i.next();
			if (p.getBoxidBehind() == boxid) {
				l.add(p);
			}
		}
		return l.iterator();
	}


	public String toString()
	{
		StringBuffer sb = new StringBuffer("Module [module="+module+", status="+status+", "+ports.size()+" ports]");
		if (VERBOSE_TOSTRING) {
			for (Iterator i=ports.values().iterator(); i.hasNext();) {
				sb.append("\n      "+i.next());
			}
		}
		return sb.toString();
	}

	public Netel getParent() {
		return parent;
	}

}
