package no.ntnu.nav.eventengine.handlerplugins.ServiceState;

import java.util.*;
import java.sql.ResultSet;
import java.sql.ResultSetMetaData;
import java.sql.SQLException;

import no.ntnu.nav.Database.*;
import no.ntnu.nav.ConfigParser.*;
import no.ntnu.nav.logger.*;

import no.ntnu.nav.eventengine.*;
import no.ntnu.nav.eventengine.deviceplugins.Box.*;
import no.ntnu.nav.eventengine.deviceplugins.Netel.*;

/**
 * EventHandler for serviceState events.
 *
 */

public class ServiceState implements EventHandler
{
	private static final boolean DEBUG_OUT = true;

	public static final int BOX_DOWN_SEVERITY_DEDUCTION = 30;

	public String[] handleEventTypes()
	{
		return new String[] { "serviceState" };
	}

	public void handle(DeviceDB ddb, Event e, ConfigParser cp)
	{
		Log.setDefaultSubsystem("SERVICE_STATE_DEVICEHANDLER");
		Log.d("HANDLE", "Event: " + e);

		// Create alert
		Alert a = ddb.alertFactory(e);
		a.addEvent(e);

		Log.d("HANDLE", "Added alert: " + a);

		boolean onMaint = false;

		// Lookup the server
		Device d = ddb.getDevice(e.getDeviceid());
		if (d != null) {
			if (d instanceof Box) {
				Box b = (Box)d;
				onMaint = b.onMaintenance();
			}
				
			String deviceup;
			if (!d.isUp()) {
				// Lower the severity by BOX_DOWN_SEVERITY_DEDUCTION, but not below zero
				a.setSeverity(Math.max(e.getSeverity()-BOX_DOWN_SEVERITY_DEDUCTION,0));
				deviceup = "No";
			} else {
				deviceup = "Yes";
			}
			a.addVar("deviceup", deviceup);
		} else {
			Log.w("HANDLE", "Device for deviceid("+e.getDeviceid()+") not found!");
		}

		char up = 'x';
		if (e.getState() == Event.STATE_START) {
			up = 'n';
		}
		else if (e.getState() == Event.STATE_END) {
			up = 'y';
		}
		
		if (up != 'x') {
			// Update up in service
			try {
				Database.update("UPDATE service SET up = '" + up + "' WHERE serviceid = " + e.getSubid());
				Database.commit();
			} catch (SQLException exp) {
				Log.w("HANDLE", "SQLException when trying to update up-field (set to " + up + ") in service: " + exp.getMessage());
			}
		}
		
		// Update varMap from database
		try {
			ResultSet rs = Database.query("SELECT * FROM service LEFT JOIN serviceproperty USING(serviceid) WHERE serviceid = " + e.getSubid());
			ResultSetMetaData rsmd = rs.getMetaData();
			if (rs.next()) {
				HashMap hm = Database.getHashFromResultSet(rs, rsmd);
				a.addVars(hm);
				String handler = rs.getString("handler");
				String state = e.getState()==Event.STATE_NONE?"":e.getState()==Event.STATE_START?"Down":"Up";
				if (handler != null) a.setAlerttype(handler+state);
			}
		} catch (SQLException exp) {
			Log.w("HANDLE", "SQLException when fetching data from serviceproperty("+e.getSubid()+"): " + exp.getMessage());
		}

		if (onMaint) {
			// Do not post to alertq if box is on maintenace
			Log.d("HANDLE", "Not posting alert to alertq as the box is on maintenance");
			a.setPostAlertq(false);
		}

		// Post the alert
		try {
			ddb.postAlert(a);
		} catch (PostAlertException exp) {
			Log.w("HANDLE", "While posting service alert, PostAlertException: " + exp.getMessage());
		}
		
	}

}
