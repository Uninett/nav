package no.ntnu.nav.eventengine;

import java.util.*;
import java.sql.*;


public abstract class Device
{
	protected static final boolean DEBUG_OUT = true;

	int deviceid;

	protected Device() { }

	public Device(ResultSet rs, Device d) throws SQLException
	{
		deviceid = rs.getInt("deviceid");
	}

	public int getDeviceid() { return deviceid; }
	public Integer getDeviceidI() { return new Integer(deviceid); }

	public static void updateFromDB(DeviceDB ddb) throws SQLException { }
	public void init(DeviceDB ddb) { }

	public abstract void down();
	public abstract void up();
	public abstract boolean isUp();


	public static boolean classEq(Object o1, Object o2)
	{
		if (o1 == null || o2 == null) return false;
		return o1.getClass().getName().equals(o2.getClass().getName());
	}


	protected static void outd(Object o) { if (DEBUG_OUT) System.out.print(o); }
	protected static void outld(Object o) { if (DEBUG_OUT) System.out.println(o); }

	protected static void err(Object o) { System.err.print(o); }
	protected static void errl(Object o) { System.err.println(o); }
}
