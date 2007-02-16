package no.ntnu.nav.eventengine.deviceplugins.Box;

import java.util.*;
import java.sql.*;

import no.ntnu.nav.Database.*;
import no.ntnu.nav.logger.*;
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

	protected boolean onMaintenance;

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
		onMaintenance = rs.getBoolean("on_maintenance");
		char up = rs.getString("up").charAt(0);
		switch (up) {
			case 'y': status = STATUS_UP; break;
			case 'n': status = STATUS_DOWN; break;
			case 's': status = STATUS_SHADOW; break;
		}

		boxidToDeviceid.put(new Integer(boxid), new Integer(deviceid));
	}

	public static void updateFromDB(DeviceDB ddb) throws SQLException
	{
		Log.d("BOX_DEVICEPLUGIN", "UPDATE_FROM_DB", "Fetching all boxes from database");
		ResultSet rs = Database.query(
				"SELECT deviceid,netboxid,ip,sysname,vlan,up, " +
				"       CASE WHEN maintenance > 0 THEN TRUE ELSE FALSE END AS on_maintenance " +
				"FROM netbox " +
				"LEFT JOIN prefix USING(prefixid) " +
				"LEFT JOIN vlan USING(vlanid) " +
				"LEFT JOIN (SELECT netboxid, count(*) as maintenance " +
				"           FROM alerthist " +
				"           WHERE eventtypeid='maintenanceState' " +
				"             AND end_time='infinity' " +
				"           GROUP BY netboxid) maintaggr USING (netboxid)");
	       
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

	/**
	 * Returns true if this box is on maintenance; false otherwise.
	 */
	public boolean onMaintenance() {
		return onMaintenance;
	}

	/**
	 * Take the box on/off maintenance.
	 */
	public void onMaintenance(boolean onMaintenance) {
		this.onMaintenance = onMaintenance;
	}

	public static int boxDownCount()
	{
		return downMap.size();
	}

	public static int boxidToDeviceid(int boxid)
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
	 * do nothing, it is up to subclasses to do something useful here.
	 *
	 */
	public void updateStatus()
	{

	}

	public void down()
	{
		downMap.put(new Integer(boxid), this);
		status = STATUS_DOWN;

		updateDbNetboxStatus();
	}

	public void shadow()
	{
		downMap.put(new Integer(boxid), this);
		status = STATUS_SHADOW;

		updateDbNetboxStatus();
	}

	public void up()
	{
		downMap.remove(new Integer(boxid));
		status = STATUS_UP;

		updateDbNetboxStatus();
	}

	private void updateDbNetboxStatus()
	{
		char c;
		switch (status) {
			case STATUS_UP: c = 'y'; break;
			case STATUS_DOWN: c = 'n'; break;
			case STATUS_SHADOW: c= 's'; break;
			default: return;
		}

		try {
			Database.update("UPDATE netbox SET up='"+c+"' WHERE netboxid="+boxid);
		} catch (SQLException e) {
			Log.w("BOX_DEVICEPLUGIN", "UPDATE_DB_NETBOX_STATUS", "Could not change status for netboxid=" + boxid);
		}
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
