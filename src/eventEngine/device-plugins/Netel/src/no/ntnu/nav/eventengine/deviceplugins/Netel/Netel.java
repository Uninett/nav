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
	/*
	int boxid;
	int status;

	String ip;
	String sysname;
	*/

	protected Netel() { }

	public Netel(ResultSet rs) throws SQLException
	{
		this(rs, null);
	}

	public Netel(ResultSet rs, Device d) throws SQLException
	{
		super(rs, d);
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
		outld("Netel.updateFromDB");
		ResultSet rs = Database.query("SELECT boksid AS deviceid,boksid,ip,sysname FROM boks WHERE kat IN ('GW','SW','KANT')");

		while (rs.next()) {
			try {

			int deviceid = rs.getInt("deviceid");

			//outld("new Netel("+deviceid+")");

			Device d = (Device)ddb.getDevice(deviceid);
			if (d == null) {
				Netel n = new Netel(rs);
				ddb.putDevice(n);
			} else if (!ddb.isTouchedDevice(d)) {
				if (classEq(d, new Netel())) {
					((Netel)d).update(rs);
					ddb.touchDevice(d);
				} else {
					Netel n = new Netel(rs, d);
					ddb.putDevice(n);
				}
			}

			} catch (Exception e) {
				errl("Exception: " + e.getMessage());
				e.printStackTrace(System.err);
				throw new RuntimeException(e.getMessage());
			}
		}

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
		modules.remove(m);
	}
	protected void moduleDown(Module m)
	{
		if (moduleDownCount++ == 0) {
			downMap.put(new Integer(boxid), this);
			moduleStatus = MODULE_STATUS_DOWN;
		}
		modulesDown.put(m.getDeviceidI(), m);
	}
	protected void moduleUp(Module m)
	{
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


	// Override to traverse the network graph and check which boxes are in shadow
	public static Iterator findBoxesDown()
	{


		return Box.findBoxesDown();
	}



}