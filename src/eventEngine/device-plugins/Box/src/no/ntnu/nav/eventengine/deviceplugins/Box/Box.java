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

	protected Box() { }

	public Box(ResultSet rs) throws SQLException
	{
		this(rs, null);
	}

	public Box(ResultSet rs, Device d) throws SQLException
	{
		super(rs, d);
		update(rs);

		if (d instanceof Box) {
			Box b = (Box)d;
			status = b.status;
		}
	}


	protected void update(ResultSet rs) throws SQLException
	{
		boxid = rs.getInt("boksid");
		ip = rs.getString("ip");
		sysname = rs.getString("sysname");
	}

	public static void updateFromDB(DeviceDB ddb) throws SQLException
	{
		outld("Box.updateFromDB");
		ResultSet rs = Database.query("SELECT boksid AS deviceid, boksid,ip,sysname FROM boks");

		while (rs.next()) {
			int deviceid = rs.getInt("deviceid");

			//outld("new Box("+deviceid+")");

			Device d = (Device)ddb.getDevice(deviceid);
			if (d == null) {
				Box b = new Box(rs);
				ddb.putDevice(b);
			} else if (!ddb.isTouchedDevice(d)) {
				if (classEq(d, new Box())) {
					((Box)d).update(rs);
					ddb.touchDevice(d);
				} else {
					Box b = new Box(rs, d);
					ddb.putDevice(b);
				}
			}
		}
	}

	public static int boxDownCount()
	{
		return downMap.size();
	}

	public static Iterator findBoxesDown()
	{
		return downMap.values().iterator();
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
