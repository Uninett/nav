/*
 *  DeviceTracker plugin for eventEngine
 *  Hans Jørgen Hoel (hansjorg@orakel.ntnu.no)
 *
 */

package no.ntnu.nav.eventengine.handlerplugins.DeviceTracker;

import no.ntnu.nav.eventengine.*;
import no.ntnu.nav.eventengine.deviceplugins.Box.*;
import no.ntnu.nav.eventengine.deviceplugins.Netel.*;

import no.ntnu.nav.Database.*;
import no.ntnu.nav.ConfigParser.*;
import no.ntnu.nav.logger.*;

import java.util.*;
import java.sql.ResultSet;
import java.sql.ResultSetMetaData;
import java.sql.SQLException;


public class DeviceTracker implements EventHandler
{
	private static final boolean DEBUG_OUT = true;

	public String[] handleEventTypes()
	{
		return new String[] { "deviceChanged", "deviceNotice" };
	}

	public void handle(DeviceDB ddb, Event e, ConfigParser cp)
	{
        Log.setDefaultSubsystem("DEVICE_TRACKER_HANDLER");
        if(DEBUG_OUT)
    		Log.d("HANDLE","DeviceTracker plugin handling event: " + e);

        String eventtype = e.getEventtypeid();
        // Variable alerttype must always be present for either event
        String alerttype = e.getVar("alerttype");

		// Create alert
		Alert a = ddb.alertFactory(e);
		a.addEvent(e);
    	a.setAlerttype(alerttype);
    	
        if (DEBUG_OUT)
    		Log.d("HANDLE","Added alert: " + a);

        if (eventtype.equals("deviceChanged")) {
            // deviceChanged event (stateful)
            if (alerttype.equals("deviceOrdered")) {
                a.copyHistoryVar(e, "username");
                if (e.getState() == Event.STATE_START) {
                    a.copyHistoryVars(e, new String[] { "orgid", "orderid", "retailer" });
                }
            } else if (alerttype.equals("deviceInOperation")) {
                // If there is already a deviceInOperation event for this device
                // which hasn't ended yet, set the end_time for that event to 
                // the start_time for this one (minus one minute, to avoid confusion)
                if (e.getState() == Event.STATE_START) {
                    try {
                        ResultSet rs = Database.query("SELECT alerthist.alerthistid FROM alerthist,alerttype WHERE alerthist.alerttypeid = alerttype.alerttypeid AND alerttype.alerttype = 'deviceInOperation' AND alerthist.deviceid = " + e.getDeviceid() + " AND alerthist.eventtypeid = 'deviceChanged' AND alerthist.end_time = 'infinity'");
                        ResultSetMetaData rsmd = rs.getMetaData();
                        if (rs.next()) {
                            // There should be only one result from this query as it
                            // is run every time a new deviceInOperation-start event
                            // is posted 
                            try {
                                // subtract one minute, ugly
                                Date end_time = new Date(e.getTime().getTime() - 1000*60);
                                // close event
                                Database.update("UPDATE alerthist SET end_time = '" + end_time + "' WHERE alerthistid = " + rs.getString("alerthistid"));
                                Database.commit(); 
                            } catch (SQLException exp) {
                                Log.e("HANDLE","Unable to update end_time of old deviceChanged (deviceInOperation) event: " + exp.getMessage());
                            }
                        }
                    } catch (SQLException exp) {
                        Log.e("HANDLE","Error while looking for old deviceChanged (deviceInOperation) event: " + exp.getMessage());
                    }
                    a.copyHistoryVars(e, new String[] { "username", "sysname", "moduleid", "roomid", "orgid", "catid" });
                } else if (e.getState() == Event.STATE_END) {
                    // An excplicit "out of operation" event
                    a.copyHistoryVar(e, "username");
                }
            } else if (alerttype.equals("deviceRma")) {
                a.copyHistoryVar(e, "username");
                if (e.getState() == Event.STATE_START) {
                    a.copyHistoryVars(e, new String[] { "rmanumber", "comment" });
                }
            } else {
                Log.e("HANDLE","Unknown alerttype '" + alerttype + "' for deviceChanged event.");
            }
        } else if (eventtype.equals("deviceNotice")) {
            // deviceNotice event (stateless)
            if (alerttype.equals("deviceRegistered")) {
                a.copyHistoryVars(e, new String[] { "username", "serial" });
            } else if (alerttype.equals("deviceError")) {
                a.copyHistoryVars(e, new String[] { "username", "description", "moduleid", "serviceid" });
            } else if (alerttype.equals("deviceHwUpgrade")) {
                a.copyHistoryVar(e, "description");
            } else if (alerttype.equals("deviceSwUpgrade")) {
                a.copyHistoryVars(e, new String[] { "oldversion", "newversion" });
            } else {
                Log.e("HANDLE","Unknown alerttype '" + alerttype + "' for deviceNotice event.");
            }
        }

		// Post the alert
		try {
			ddb.postAlert(a);
		} catch (PostAlertException exp) {
			Log.w("HANDLE","While posting alert, PostAlertException: " + exp.getMessage());
		}
		
	}
}
