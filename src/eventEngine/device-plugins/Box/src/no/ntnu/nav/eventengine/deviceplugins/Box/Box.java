package no.ntnu.nav.eventengine.deviceplugins.Box;

import java.util.*;
import java.sql.*;
import no.ntnu.nav.Database.*;

import no.ntnu.nav.eventengine.*;

public class Box extends Device
{
	static Map downMap = new HashMap();

	int boxid;
	boolean status;

	public Box(int deviceid, int boxid)
	{
		super(deviceid);
		this.boxid = boxid;
	}
	public Box(Device d)
	{
		super(d);
		if (d instanceof Box) {
			Box b = (Box)d;
			boxid = b.boxid;
			status = b.status;
		}
	}

	public static void updateFromDB(DeviceDB ddb) throws SQLException
	{
		System.out.println("Box.updateFromDB");
		ResultSet rs = Database.query("SELECT boksid FROM boks");

		while (rs.next()) {
			int boxid = rs.getInt("boksid");
			int deviceid = boxid;

			//outld("new Box("+deviceid+")");

			Device d = (Device)ddb.getDevice(deviceid);
			if (d == null) {
				d = new Box(deviceid, boxid);
				ddb.putDevice(d);
			} else if (!ddb.isTouchedDevice(d)) {
				Box b = new Box(d);
				ddb.putDevice(b);
			}
		}
	}

	public static Iterator findBoxesDown()
	{
		return downMap.values().iterator();
	}

	public void down()
	{
		downMap.put(new Integer(boxid), this);
		status = false;
	}

	public void up()
	{
		downMap.remove(new Integer(boxid));
		status = true;
	}

	public boolean isUp()
	{
		return status;
	}


}
