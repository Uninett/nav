package no.ntnu.nav.eventengine.deviceplugins.Netel;

import java.util.*;
import java.sql.*;
import no.ntnu.nav.Database.*;

import no.ntnu.nav.eventengine.*;
import no.ntnu.nav.eventengine.deviceplugins.Box.*;

public class Module extends Device
{
	protected static final boolean DEBUG_OUT = true;
	protected static final boolean VERBOSE_TOSTRING = true;

	protected int parentDeviceid;
	protected int parentBoxid;
	protected String module;
	protected boolean status = true; // default is up
	protected Netel parent;
	protected Map ports = new HashMap();

	protected Module() { }

	public Module(DeviceDB devDB, ResultSet rs) throws SQLException
	{
		this(devDB, rs, null);
	}

	public Module(DeviceDB devDB, ResultSet rs, Device d) throws SQLException
	{
		super(devDB, rs, d);
		update(rs);

		if (d instanceof Module) {
			Module m = (Module)d;
			status = m.status;
		}
	}

	protected void update(ResultSet rs) throws SQLException
	{
		parentDeviceid = rs.getInt("parent_deviceid");
		parentBoxid = rs.getInt("parent_netboxid");
		module = rs.getString("module");
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

	public static void updateFromDB(DeviceDB ddb) throws SQLException
	{
		outld("Module.updateFromDB");
		ResultSet rs = Database.query("SELECT module.deviceid,netbox.deviceid AS parent_deviceid,module.netboxid AS parent_netboxid,module,port,to_netboxid,vlan,direction FROM module JOIN netbox USING (netboxid) JOIN swport USING(moduleid) JOIN swportvlan USING(swportid) WHERE module.up='y' ORDER BY moduleid,module,port");

		while (rs.next()) {
			int deviceid = rs.getInt("deviceid");

			//outld("new Module("+deviceid+")");
			if (rs.getInt("parent_deviceid") == 237) {
				rs.previous();
				rs.previous();
				errl("Boxid: " + rs.getInt("parent_deviceid") + " Port: " + rs.getInt("port") + " parent: " + rs.getInt("to_netboxid"));
				rs.next();
				rs.next();
			}

			Device d = (Device)ddb.getDevice(deviceid);
			if (d == null) {
				Module m = new Module(ddb, rs);
				if (m.parentDeviceid == 237) errl("Module: " + m);
				ddb.putDevice(m);
			} else if (!ddb.isTouchedDevice(d)) {
				if (classEq(d, new Module())) {
					((Module)d).update(rs);
					ddb.touchDevice(d);
				} else {
					Module m = new Module(ddb, rs, d);
					ddb.putDevice(m);
				}
			}
		}
	}

	public void init(DeviceDB ddb)
	{
		Device d = (Device)ddb.getDevice(parentDeviceid);
		if (d instanceof Netel) {
			parent = (Netel)d;
			parent.addModule(this);
		} else {
			errl("Module error, parentDeviceid="+parentDeviceid+" is not an instance of Netel!");
			return;
		}
	}

	public void remove(DeviceDB ddb)
	{
		if (parent != null) {
			parent.removeModule(this);
		}
	}

	public void down()
	{
		status = false;
		parent.moduleDown(this);
	}
	public void up()
	{
		status = true;
		parent.moduleUp(this);
	}
	public boolean isUp()
	{
		return status;
	}

	public String getModule()
	{
		return module;
	}

	public Port getPort(int port)
	{
		return (Port)ports.get(new Integer(port));
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


}