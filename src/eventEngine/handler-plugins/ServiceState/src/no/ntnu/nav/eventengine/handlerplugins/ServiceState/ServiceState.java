package no.ntnu.nav.eventengine.handlerplugins.ServiceState;

import no.ntnu.nav.eventengine.*;
import no.ntnu.nav.eventengine.deviceplugins.Box.*;
import no.ntnu.nav.eventengine.deviceplugins.Netel.*;

import no.ntnu.nav.Database.*;

import java.util.*;
import java.sql.ResultSet;
import java.sql.ResultSetMetaData;
import java.sql.SQLException;


public class ServiceState implements EventHandler
{
	private static final boolean DEBUG_OUT = true;

	public String[] handleEventTypes()
	{
		return new String[] { "serviceState" };
	}

	public void handle(DeviceDB ddb, Event e)
	{
		outld("ServiceState handling event: " + e);

		// Create alert
		Alert a = ddb.alertFactory(e);
		a.addEvent(e);

		outld("  added alert: " + a);

		// Set time
		a.addVar("time", e.getTimeS());

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
			errl("EventImpl: SQLException when fetching data from serviceproperty("+e.getSubid()+"): " + exp.getMessage());
		}

		// Post the alert
		try {
			ddb.postAlert(a);
		} catch (PostAlertException exp) {
			errl("ServiceState.classback: While posting service alert, PostAlertException: " + exp.getMessage());
		}

	}

	private static void outd(Object o) { if (DEBUG_OUT) System.out.print(o); }
	private static void outld(Object o) { if (DEBUG_OUT) System.out.println(o); }

	private static void err(Object o) { System.err.print(o); }
	private static void errl(Object o) { System.err.println(o); }

}
