package no.ntnu.nav.eventengine;

import java.util.*;
import java.sql.*;

/**
 * The Device class forms the root of the class hierarchy for
 * representing devices. Device plugins can inherit this class to
 * provide classes which describes devices in more detail.
 */

public abstract class Device
{
	protected DeviceDB devDB;

	protected int deviceid;

	protected Device() { }

	public Device(DeviceDB devDB, ResultSet rs, Device d) throws SQLException
	{
		this.devDB = devDB;
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

}
