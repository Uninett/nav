import java.io.File;
import java.io.IOException;
import java.sql.ResultSet;
import java.util.HashMap;
import java.util.Map;

import no.ntnu.nav.Path;
import no.ntnu.nav.ConfigParser.ConfigParser;
import no.ntnu.nav.Database.Database;
import no.ntnu.nav.event.Event;
import no.ntnu.nav.event.EventQ;
import no.ntnu.nav.event.EventQListener;

/**
 * Tests the EventQ class.
 */

class testEventQ implements EventQListener {
	public static final String scriptName = "getDeviceData";

	public static void main(String[] args) throws Exception {
		if (!connectDb()) return;

		String netbox = (args.length > 0) ? args[0] : "ntnu-gsw";

		ResultSet rs = Database.query("SELECT deviceid,netboxid FROM netbox WHERE sysname = '" + netbox + "'");
		int deviceid = 0;
		int netboxid = 0;
		if (rs.next()) {
			deviceid = rs.getInt("deviceid");
			netboxid = rs.getInt("netboxid");
		}

		EventQ.init(100);
		Thread.sleep(1000);
		EventQ.init(1000, false);

		// Set up a listener
		EventQ.addEventQListener("deviceManagement", "getDeviceData", new testEventQ() );

		// Get event
		Map m = new HashMap();
		m.put("testVar1", "testVal1");
		m.put("testVar2", "testVal2");
		Event e = EventQ.eventFactory("deviceManagement", "getDeviceData", deviceid, netboxid, 0, "info", Event.STATE_START, -1, -1, m);
		EventQ.postEvent(e);
		outl("Event posted");

	}

	public void handleEvent(Event e) {
		outl("Got event: " + e);
		e.dispose();
		outl("Event disposed");

		Database.closeConnection();
		System.exit(0);
	}

	private static boolean connectDb() throws Exception {
		if (!Database.openConnection(scriptName, "nav")) {
			errl("Error, could not connect to database!");
			return false;
		}
		return true;
	}

	private static void out(Object o) { System.out.print(o); }
	private static void outl(Object o) { System.out.println(o); }
	private static void outflush() { System.out.flush(); }
	private static void err(Object o) { System.err.print(o); }
	private static void errl(Object o) { System.err.println(o); }
	private static void errflush() { System.err.flush(); }

}
