package no.ntnu.nav.eventengine.handlerplugins.DeviceTracker;

import no.ntnu.nav.eventengine.*;
import no.ntnu.nav.eventengine.deviceplugins.Box.*;
import no.ntnu.nav.eventengine.deviceplugins.Netel.*;

import no.ntnu.nav.Database.*;
import no.ntnu.nav.ConfigParser.*;

import java.util.*;
import java.sql.ResultSet;
import java.sql.ResultSetMetaData;
import java.sql.SQLException;


public class DeviceTracker implements EventHandler
{
	private static final boolean DEBUG_OUT = true;

	public String[] handleEventTypes()
	{
		return new String[] { "deviceOrdered", "deviceRegistered", "deviceOnService", "deviceInOperation", "deviceError", "deviceHwUpgrade", "deviceSwUpgrade" };
	}

	public void handle(DeviceDB ddb, Event e, ConfigParser cp)
	{
		outld("DeviceTracker plugin handling event: " + e);

        String eventtype = e.getEventtypeid();

		// Create alert
		Alert a = ddb.alertFactory(e);
		a.addEvent(e);
		
		outld("  added alert: " + a);

        // Add history vars for the different events
        if (eventtype.equals("deviceOrdered")) {
            a.addHistoryVar("username",e.getVar("username"));
            if(e.getState() == Event.STATE_START) {
                a.addHistoryVar("orgid",e.getVar("orgid"));
                a.addHistoryVar("dealer",e.getVar("dealer"));
                a.addHistoryVar("orderid",e.getVar("orderid"));
            }
        } else if (eventtype.equals("deviceRegistered")) {
            a.addHistoryVar("username",e.getVar("username"));
        } else if (eventtype.equals("deviceOnService")) {
            a.addHistoryVar("username",e.getVar("username"));
        } else if (eventtype.equals("deviceInOperation")) {
            // If there is already a deviceInOperation event for this device
            // then send a deviceOperation end event
        } else if (eventtype.equals("deviceError")) {
            a.addHistoryVar("username",e.getVar("username"));
            a.addHistoryVar("comment",e.getVar("comment"));
        } else if (eventtype.equals("deviceHwUpgrade")) {
            a.addHistoryVar("description",e.getVar("description"));
        } else if (eventtype.equals("deviceSwUpgrade")) {
            a.addHistoryVar("oldversion",e.getVar("oldversion"));
            a.addHistoryVar("newversion",e.getVar("newversion"));
        }



		// Post the alert
		try {
			ddb.postAlert(a);
		} catch (PostAlertException exp) {
			errl("DeviceTracker: While posting alert, PostAlertException: " + exp.getMessage());
		}
		
	}
	
	private static void outd(Object o) { if (DEBUG_OUT) System.out.print(o); }
	private static void outld(Object o) { if (DEBUG_OUT) System.out.println(o); }

	private static void err(Object o) { System.err.print(o); }
	private static void errl(Object o) { System.err.println(o); }

}
