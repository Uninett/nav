package no.ntnu.nav.eventengine.deviceplugins.Netel;

import java.util.*;
import java.sql.*;
import no.ntnu.nav.Database.*;

import no.ntnu.nav.eventengine.*;
//import no.ntnu.nav.eventengine.deviceplugins.Box.*;

public class Module extends Device
{
	protected static final boolean DEBUG_OUT = true;
	protected static final boolean VERBOSE_TOSTRING = false;

	int parentDeviceid;
	int parentBoxid;
	String module;
	boolean status;
	Netel parent;
	Map ports = new HashMap();

	protected Module() { }

	public Module(ResultSet rs) throws SQLException
	{
		this(rs, null);
	}

	public Module(ResultSet rs, Device d) throws SQLException
	{
		super(rs, d);
		update(rs);

		if (d instanceof Module) {
			Module m = (Module)d;
			status = m.status;
		}
	}

	protected void update(ResultSet rs) throws SQLException
	{
		parentDeviceid = rs.getInt("parent_deviceid");
		parentBoxid = rs.getInt("parent_boxid");
		module = rs.getString("module");
		do {
			Port p = new Port(rs);
			ports.put(p.getPortI(), p);
		} while (rs.next() && rs.getString("module").equals(module));
		rs.previous();
	}

	public static void updateFromDB(DeviceDB ddb) throws SQLException
	{
		outld("Module.updateFromDB");
		ResultSet rs = Database.query("SELECT moduleid+10000 AS deviceid,module.boksid AS parent_deviceid,module.boksid AS parent_boxid,modul AS module,port,boksbak AS boksid_behind FROM module JOIN swport ON (module.boksid=swport.boksid AND modulenumber=modul) WHERE status='up' ORDER BY moduleid,port");

		while (rs.next()) {
			int deviceid = rs.getInt("deviceid");

			//outld("new Module("+deviceid+")");

			Device d = (Device)ddb.getDevice(deviceid);
			if (d == null) {
				Module m = new Module(rs);
				ddb.putDevice(m);
			} else if (!ddb.isTouchedDevice(d)) {
				if (classEq(d, new Module())) {
					((Module)d).update(rs);
					ddb.touchDevice(d);
				} else {
					Module m = new Module(rs, d);
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
	protected Iterator getPorts()
	{
		return ports.values().iterator();
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