package no.ntnu.nav.eventengine.deviceplugins.Box;

import java.util.*;
import java.sql.*;
import no.ntnu.nav.Database.*;

import no.ntnu.nav.eventengine.*;

public class Box extends Device
{
	public static final int STATUS_UP = 0;
	public static final int STATUS_SHADOW = 10;
	public static final int STATUS_DOWN = 20;

	protected static Map downMap = new HashMap();

	protected int boxid;
	protected int status;

	protected String ip;
	protected String sysname;
	//protected int gwdeviceid;
	protected int vlan;

	// Translate boxid -> deviceid
	private static Map boxidToDeviceid = new HashMap();

	protected Box() { }

	public Box(DeviceDB devDB, ResultSet rs) throws SQLException
	{
		this(devDB, rs, null);
	}

	public Box(DeviceDB devDB, ResultSet rs, Device d) throws SQLException
	{
		super(devDB, rs, d);
		update(rs);

		if (d instanceof Box) {
			Box b = (Box)d;
			status = b.status;
			vlan = b.vlan;
		}
	}


	protected void update(ResultSet rs) throws SQLException
	{
		boxid = rs.getInt("netboxid");
		ip = rs.getString("ip");
		sysname = rs.getString("sysname");
		vlan = rs.getInt("vlan");

		boxidToDeviceid.put(new Integer(boxid), new Integer(deviceid));
	}

	public static void updateFromDB(DeviceDB ddb) throws SQLException
	{
		outld("Box.updateFromDB");
		ResultSet rs = Database.query("SELECT deviceid,netboxid,ip,sysname,vlan FROM netbox JOIN prefix USING(prefixid)");

		while (rs.next()) {
			int deviceid = rs.getInt("deviceid");

			//outld("new Box("+deviceid+")");

			Device d = (Device)ddb.getDevice(deviceid);
			if (d == null) {
				Box b = new Box(ddb, rs);
				ddb.putDevice(b);
			} else if (!ddb.isTouchedDevice(d)) {
				if (classEq(d, new Box())) {
					((Box)d).update(rs);
					ddb.touchDevice(d);
				} else {
					Box b = new Box(ddb, rs, d);
					ddb.putDevice(b);
				}
			}
		}
	}

	public int getBoxid()
	{
		return boxid;
	}

	public String getSysname()
	{
		return sysname;
	}

	public static int boxDownCount()
	{
		return downMap.size();
	}

	public int boxidToDeviceid(int boxid)
	{
		Integer i;
		if ( (i=(Integer)boxidToDeviceid.get(new Integer(boxid))) != null) return i.intValue();
		return 0;
	}

	public static Iterator findBoxesDown()
	{
		return downMap.values().iterator();
	}

	/**
	 * Update status; basically check if this box is in shadow if it is down. The default is to
	 * to nothing, it is up to subclasses to do something useful here.
	 *
	 */
	public void updateStatus()
	{

	}

	public void down()
	{
		downMap.put(new Integer(boxid), this);
		status = STATUS_DOWN;
	}

	public void shadow()
	{
		downMap.put(new Integer(boxid), this);
		status = STATUS_SHADOW;
	}

	public void up()
	{
		downMap.remove(new Integer(boxid));
		status = STATUS_UP;
	}

	public boolean isUp() { return status == STATUS_UP; }

	public int getStatus()
	{
		return status;
	}

	public String getStatusS()
	{
		return statusToString(getStatus());
	}

	public String toString()
	{
		return "Box [ip="+ip+", sysname="+sysname+", status="+statusToString(status)+"]";
	}


	private static String statusToString(int status)
	{
		switch (status) {
			case STATUS_UP: return "up";
			case STATUS_SHADOW: return "shadow";
			case STATUS_DOWN: return "down";
		}
		return null;
	}

}
