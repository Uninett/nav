package no.ntnu.nav.eventengine.deviceplugins.Netel;

import java.util.*;
import java.sql.*;
import no.ntnu.nav.Database.*;

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
		outld("Gw.updateFromDB");
		ResultSet rs = Database.query("SELECT deviceid,netboxid,ip,sysname,vlan,up FROM netbox LEFT JOIN prefix USING(prefixid) WHERE catid IN ('GW')");

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
				errl("Exception: " + e.getMessage());
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
		for (Iterator i=modules.iterator(); i.hasNext();) {
			sb.append("\n    "+i.next());
		}
		return sb.toString();
	}

	/**
	 * Check if b is reachable from this Netel. Currently, this methods
	 * always returns true for routers (type Gw) if it is up.
	 *
	 * @return true if this router is up
	 */
	protected boolean reachableFrom(Box b, int vlan, Set visited)
	{
		return isUp();
	}

}