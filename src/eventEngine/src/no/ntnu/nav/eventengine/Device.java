package no.ntnu.nav.eventengine;

import java.util.*;
import java.sql.*;


public abstract class Device
{
	int deviceid;

	public Device(int deviceid)
	{
		this.deviceid = deviceid;
	}
	public Device(Device d)
	{
		deviceid = d.deviceid;
	}

	public int getDeviceid() { return deviceid; }
	public Integer getDeviceidI() { return new Integer(deviceid); }

	public static void updateFromDB(DeviceDB ddb) throws SQLException { }

	public abstract void down();
	public abstract void up();
	public abstract boolean isUp();


	protected static void outd(Object o) { System.out.print(o); }
	protected static void outld(Object o) { System.out.println(o); }

	protected static void err(Object o) { System.err.print(o); }
	protected static void errl(Object o) { System.err.println(o); }
}
