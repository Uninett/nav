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
		return new String[] { "deviceOrdered", "deviceRegistered", "deviceOnService", "deviceInOperation", "deviceError", "deviceHwUpgrade", "deviceSwUpgrade", "deviceRma" };
	}

	public void handle(DeviceDB ddb, Event e, ConfigParser cp)
	{
        Log.setDefaultSubsystem("DEVICE_TRACKER_HANDLER");
        if(DEBUG_OUT)
    		Log.d("HANDLE","DeviceTracker plugin handling event: " + e);

        String eventtype = e.getEventtypeid();

		// Create alert
		Alert a = ddb.alertFactory(e);
		a.addEvent(e);
		
        if (DEBUG_OUT)
    		Log.d("HANDLE","Added alert: " + a);

        // Add history vars for the different events
        if (eventtype.equals("deviceOrdered")) {
            if (e.getVar("username") != null)
                a.addHistoryVar("username",e.getVar("username"));
            if (e.getState() == Event.STATE_START) {
                if (e.getVar("orgid") != null)
                    a.addHistoryVar("orgid",e.getVar("orgid"));
                if (e.getVar("dealer") != null)
                    a.addHistoryVar("dealer",e.getVar("dealer"));
                if (e.getVar("orderid") != null)
                    a.addHistoryVar("orderid",e.getVar("orderid"));
            }
        } else if (eventtype.equals("deviceRegistered")) {
            if (e.getVar("username") != null)
                a.addHistoryVar("username",e.getVar("username"));
        } else if (eventtype.equals("deviceOnService")) {
            if (e.getVar("username") != null)
                a.addHistoryVar("username",e.getVar("username"));
        } else if (eventtype.equals("deviceInOperation")) {
            // If there is already a deviceInOperation event for this device
            // which hasn't ended yet, set the end_time for that event to 
            // the start_time for this one (minus one minute, to avoid confusion)
            if (e.getState() == Event.STATE_START) {
                try {
                    ResultSet rs = Database.query("SELECT alerthistid FROM alerthist WHERE deviceid = " + e.getDeviceid() + " AND end_time = 'infinity'");
                    ResultSetMetaData rsmd = rs.getMetaData();
                    if (rs.next()) {
                        // There should be only one result from this query as it
                        // is run every time a new deviceInOperation-start event
                        // is posted 
                        try {
                            // subtract one minute, ugly
                            Date end_time = new Date(e.getTime().getTime() - 1000*60);
                            Database.update("UPDATE alerthist SET end_time = '" + end_time + "' WHERE alerthistid = " + rs.getString("alerthistid"));
                            Database.commit(); 
                        } catch (SQLException exp) {
                            Log.e("HANDLE","Unable to update end_time of old deviceInOperation event: " + exp.getMessage());
                        }
                    }
                } catch (SQLException exp) {
                    Log.e("HANDLE","Error while looking for old deviceInOperation event: " + exp.getMessage());
                }
                if (e.getVar("username") != null)
                    a.addHistoryVar("username",e.getVar("username"));
                if (e.getVar("sysname") != null)
                    a.addHistoryVar("sysname",e.getVar("sysname"));
                if (e.getVar("module") != null)
                    a.addHistoryVar("module",e.getVar("module"));
                if (e.getVar("room") != null)
                    a.addHistoryVar("room",e.getVar("room"));
            } else if (e.getState() == Event.STATE_END) {
                // An excplicit "out of operation" event
                if (e.getVar("username") != null)
                    a.addHistoryVar("username",e.getVar("username"));
            }
        } else if (eventtype.equals("deviceError")) {
            if (e.getVar("username") != null)
                a.addHistoryVar("username",e.getVar("username"));
            if (e.getVar("comment") != null)
                a.addHistoryVar("comment",e.getVar("comment"));
        } else if (eventtype.equals("deviceHwUpgrade")) {
            if (e.getVar("description") != null)
                a.addHistoryVar("description",e.getVar("description"));
        } else if (eventtype.equals("deviceSwUpgrade")) {
            if (e.getVar("oldversion") != null)
                a.addHistoryVar("oldversion",e.getVar("oldversion"));
            if (e.getVar("newversion") != null)
                a.addHistoryVar("newversion",e.getVar("newversion"));
        } else if (eventtype.equals("deviceRma")) {
            if (e.getVar("username") != null)
                a.addHistoryVar("username",e.getVar("username"));
            if (e.getVar("rmanumber") != null)
                a.addHistoryVar("rmanumber",e.getVar("rmanumber"));
            if (e.getVar("comment") != null)
                a.addHistoryVar("comment",e.getVar("comment"));
        }

		// Post the alert
		try {
			ddb.postAlert(a);
		} catch (PostAlertException exp) {
			Log.w("HANDLE","While posting alert, PostAlertException: " + exp.getMessage());
		}
		
	}
}
