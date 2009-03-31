import java.util.*;
import java.io.*;
import java.sql.ResultSet;

import no.ntnu.nav.netboxinfo.*;
import no.ntnu.nav.ConfigParser.*;
import no.ntnu.nav.Database.*;
import no.ntnu.nav.Path;

/**
 * Tests the NetboxInfo class.
 */

class testNetboxInfo {
	public static final String scriptName = "getDeviceData";

	public static void main(String[] args) throws Exception {
		if (!connectDb()) return;

		String netbox = (args.length > 0) ? args[0] : "ntnu-gsw";

		ResultSet rs = Database.query("SELECT netboxid FROM netbox WHERE sysname = '" + netbox + "'");
		if (!rs.next()) {
			outl("Test netbox " + netbox + " not found! Aborting...");
			return;
		}
		NetboxInfo.setDefaultNetboxid(rs.getString("netboxid"));

		// Test remove
		if (NetboxInfo.remove("testKeyD", "testVarD") > 0) {
			outl("Failed delete test for testKeyD and testVarD!");
		}
		if (NetboxInfo.remove("testVarD") > 0) {
			outl("Failed delete test for testVarD!");
		}

		// Test put/get
		NetboxInfo.put("testKey", "testVar", "testVal");
		if (!NetboxInfo.getSingleton("testKey", "testVar").equals("testVal")) {
			outl("Failed put/get for testKey and testVar!");
		}

		// Test put/get
		NetboxInfo.put("testKey", "testVar", new String[] { "1", "2", "3" } );
		{
			Iterator it = NetboxInfo.get("testKey", "testVar");
			for (int i=1; it.hasNext(); i++) {
				if (!String.valueOf(i).equals(it.next())) {
					outl("Failed put/get for multi testKey and testVar!");
				}
			}
		}

		NetboxInfo.put("testKeyR", "testVarR", new String[] { "1", "2", "3" } );
		if (NetboxInfo.remove("testKeyR", "testVarR") != 3) {
			outl("Failed put/remove test for testKeyR and testVarR!");
		}

		Database.closeConnection();
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
