package no.ntnu.nav.getDeviceData.deviceplugins.Typeoid;

import java.util.*;
import java.sql.ResultSet;
import java.sql.SQLException;

import no.ntnu.nav.logger.*;
import no.ntnu.nav.SimpleSnmp.*;
import no.ntnu.nav.ConfigParser.*;
import no.ntnu.nav.Database.*;
import no.ntnu.nav.event.*;
import no.ntnu.nav.util.*;
import no.ntnu.nav.getDeviceData.Netbox;
import no.ntnu.nav.getDeviceData.dataplugins.NetboxUpdatable;
import no.ntnu.nav.getDeviceData.deviceplugins.*;
import no.ntnu.nav.getDeviceData.dataplugins.*;

/**
 * <p>
 * DeviceHandler for checking and updating the type of netboxes.
 * </p>
 *
 * <p>
 * This plugin handles the following OID keys:
 * </p>
 *
 * <ul>
 *  <li>typeoid</li>
 * </ul>
 * </p>
 *
 */

public class Typeoid implements DeviceHandler
{
	private static String[] canHandleOids = {
		"typeoid",
	};

	private SimpleSnmp sSnmp;

	public int canHandleDevice(Netbox nb) {
		// Typeoid should run first, before any normal ALWAYS_HANDLE plugins
		int v = nb.isSupportedOids(canHandleOids) ? -100 : NEVER_HANDLE;
		Log.d("TYPEOID_CANHANDLE", "CHECK_CAN_HANDLE", "Can handle device: " + v);
		return v;
	}

	public void handleDevice(Netbox nb, SimpleSnmp sSnmp, ConfigParser cp, DataContainers containers) throws TimeoutException
	{
		Log.setDefaultSubsystem("TYPEOID_DEVHANDLER");
		NetboxUpdatable nu = (NetboxUpdatable)nb;

		// Fetch the typeoid
		sSnmp.onlyAskModule("0");
		List l;
		try {
			l = sSnmp.getNext(nb.getOidNoCheck("typeoid"), 1, true, false);
			if (l == null || l.isEmpty()) {
				Log.w("HANDLE_DEVICE", "No returned results from typeoid (" + nb + ","+nb.getType()+","+nb.getOid("typeoid")+"), cannot update type! ("+l+")");
				return;
			}
		} finally {
			sSnmp.onlyAskModule(null);
		}

		String sysobjectid = ((String[])l.get(0))[1];

		try {
			ResultSet rs = Database.query("SELECT typeid,typename FROM type WHERE sysobjectid = '" + sysobjectid + "'");
			if (!rs.next()) {
				Log.w("HANDLE_DEVICE", "Type not found for sysobjectid: " + sysobjectid + " on " + nb);
				return;
			}
			String typeid = rs.getString("typeid");
			if (!typeid.equals(nu.getTypeid())) {
				// Type has changed!
				{
					// Send event
					Log.d("HANDLE_DEVICE", "Type changed from " + nb.getType() + "("+nu.getTypeid()+") to " + rs.getString("typename") + "("+typeid+")");
					Map varMap = new HashMap();
					varMap.put("alerttype", "netboxTypeChanged");
					varMap.put("old_typename", (nb.getType()==null?"unknownType":nb.getType()));
					varMap.put("new_typename", rs.getString("typename"));
					EventQ.createAndPostEvent("getDeviceData", "eventEngine", nb.getDeviceid(), nb.getNetboxid(), 0, "info", Event.STATE_NONE, 0, 0, varMap);
				}
				
				// Delete the netbox and insert new netbox with correct type
				rs = Database.query("SELECT ip,roomid,deviceid,sysname,catid,orgid,ro,rw,prefixid,up FROM netbox WHERE netboxid = '"+nb.getNetboxid()+"'");
				rs.next();

				Log.i("HANDLE_DEVICE", "Deleting netbox from database: " + nb);

				Database.beginTransaction();
				Database.update("DELETE FROM netbox WHERE netboxid = '"+nb.getNetboxid()+"'");

				/*
				String[] insDev = {
					"deviceid", "",
				};
				String deviceid = Database.insert("device", insDev, null);
				*/
				
				String[] insNb = {
					"ip", rs.getString("ip"),
					"roomid", rs.getString("roomid"),
					"typeid", typeid,
					"deviceid", rs.getString("deviceid"),
					"sysname", rs.getString("sysname"),
					"catid", rs.getString("catid"),
					"orgid", rs.getString("orgid"),
					"ro", rs.getString("ro"),
					"rw", rs.getString("rw"),
					"prefixid", rs.getString("prefixid"),
					"up", rs.getString("up")
				};
				Database.insert("netbox", insNb);

				Database.commit();

				// It is now safe to remove the netbox
				nu.remove(true);

			}
		} catch (SQLException e) {
			Log.e("HANDLE_DEVICE", "Error while trying to change type for netbox " + nb);
			Log.d("HANDLE_DEVICE", "SQLException: " + e);
			try {
				Database.rollback();
			} catch (SQLException er) {
				Log.d("HANDLE_DEVICE", "SQLException during rollback: " + er);
			}
			e.printStackTrace(System.err);
		}

	}

}
