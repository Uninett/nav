package no.ntnu.nav.eventengine.deviceplugins.Netel;

import java.util.*;
import java.sql.*;

import no.ntnu.nav.Database.*;
import no.ntnu.nav.logger.*;
import no.ntnu.nav.eventengine.*;
import no.ntnu.nav.eventengine.deviceplugins.Box.*;

public class Gw extends Netel
{
	protected static final boolean DEBUG_OUT = true;

	protected Gw() { }

	public Gw(DeviceDB devDB, ResultSet rs) throws SQLException
	{
		this(devDB, rs, null);
	}

	public Gw(DeviceDB devDB, ResultSet rs, Device d) throws SQLException
	{
		super(devDB, rs, d);
		update(rs);

		if (d instanceof Gw) {
			Gw gw = (Gw)d;
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
		Log.d("GW_DEVICEPLUGIN", "UPDATE_FROM_DB", "Fetching all GWs from database");
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
				"           GROUP BY netboxid) maintaggr USING (netboxid) " +
				"WHERE catid IN ('GW', 'GSW')");

		while (rs.next()) {
			try {

				int deviceid = rs.getInt("deviceid");

				Device d = (Device)ddb.getDevice(deviceid);
				if (d == null) {
					Gw gw = new Gw(ddb, rs);
					ddb.putDevice(gw);
				} else if (!ddb.isTouchedDevice(d)) {
					if (classEq(d, new Gw())) {
						((Gw)d).update(rs);
						ddb.touchDevice(d);
					} else {
						Gw gw = new Gw(ddb, rs, d);
						ddb.putDevice(gw);
					}
				}

			} catch (Exception e) {
				Log.e("GW_DEVICEPLUGIN", "UPDATE_FROM_DB", "Exception while creating devices: " + e.getMessage());
				e.printStackTrace(System.err);
				throw new RuntimeException(e.getMessage());
			}
		}

	}
	/*
	public void init(DeviceDb ddb)
	{


	}
	*/

	public String toString()
	{
		StringBuffer sb = new StringBuffer(super.toString());
		sb.append("\n  Gw ["+modules.size()+" modules]");
		for (Iterator i=modules.values().iterator(); i.hasNext();) {
			sb.append("\n    "+i.next());
		}
		return sb.toString();
	}

	/**
	 * Overridden from superclass. Routers are currently never in shadow.
	 *
	 */
	public void updateStatus()
	{

	}

	/**
	 * Check if b is reachable from this Netel. Currently, this methods
	 * always returns REACHABLE_YES for routers (type Gw) if it is up;
	 * REACHABLE_NO otherwise.
	 *
	 * @return REACHABLE_YES if this router is up; REACHABLE_NO otherwise
	 */
	protected int reachableFrom(Box b, int vlan, Set visited)
	{
		return isUp() ? REACHABLE_YES : REACHABLE_NO;
	}

}
