package no.ntnu.nav.eventengine.handlerplugins.MaintenanceState;

import java.util.*;

import no.ntnu.nav.Database.*;
import java.sql.ResultSet;
import java.sql.SQLException;
import no.ntnu.nav.ConfigParser.*;
import no.ntnu.nav.logger.*;

import no.ntnu.nav.eventengine.*;
import no.ntnu.nav.eventengine.deviceplugins.Box.*;

/**
 * MaintenanceState plugin for eventengine. Handles all events dealing with
 * netboxes and their modules going on/off maintenance.
 */

public class MaintenanceState implements EventHandler
{
	public String[] handleEventTypes()
	{
		return new String[] { "maintenanceState" };
	}

	public void handle(DeviceDB ddb, Event e, ConfigParser cp)
	{
		Log.setDefaultSubsystem("MAINTENANCE_HANDLER");
		Log.d("HANDLE", "Event: " + e);

		Device d = ddb.getDevice(e.getDeviceid());
		if (d == null) {
			Log.w("HANDLE", "Device with deviceid="+e.getDeviceid()+" not found!");
			e.defer("Device with deviceid="+e.getDeviceid()+" not found!");
			return;
		}

		Alert a;

		if (d instanceof Box) {
			Box b = (Box)d;
			if (e.getState() == Event.STATE_START) {
				b.onMaintenance(true);
				a = ddb.alertFactory(e, "onMaintenance");
				// Copy all variables from start event to the alert history
				// This makes sure the alert in alerthist can be correlated to a maintenance task
				a.addHistoryVars(e.getVarMap());
			} else if (e.getState() == Event.STATE_END) {
				b.onMaintenance(false);
				a = ddb.alertFactory(e, "offMaintenance");

				// The Box may have been replaced by a different
				// physical device during the maintenance period.  Look
				// up the original device id from the alerthist table
				int deviceid = getOriginalDeviceId(b);
				a.setDeviceid(deviceid);
			} else {
				Log.w("HANDLE", "MaintenanceState events cannot be stateless, ignoring event");
				return;
			}
				
		} else {
			Log.w("HANDLE", "Device " + d + " not Box or sub-class of Box: " + d.getClassH());
			return;
		}
		
		a.addEvent(e);

		try {
			ddb.postAlert(a);
		} catch (PostAlertException exp) {
			Log.e("HANDLE", "Exception when trying to post alert " + a+ ", msg: " + exp);
		}
	}

	protected int getOriginalDeviceId(Box box)
	{
		try {
			ResultSet rs = Database.query("SELECT deviceid FROM alerthist WHERE end_time='infinity' AND netboxid=" + box.getBoxid() + " AND eventtypeid='maintenanceState'");
			if (rs.next()) {
				return rs.getInt(1);
			}
		} catch (SQLException e) {
			Log.e("HANDLE", "Error while looking for old deviceid of box " + box.getBoxid() + "(" + box.getSysname() + "):" + e.getMessage());
		}
		// If, for some reason, we couldn't find the down alert, use
		// the posted device id
		return box.getDeviceid();
	}
}
