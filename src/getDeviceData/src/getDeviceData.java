/*
 *
 *
 *
 */

import java.io.*;
import java.util.*;
import java.util.jar.*;
import java.net.*;
import java.text.*;

import java.sql.*;

import no.ntnu.nav.logger.*;
import no.ntnu.nav.ConfigParser.*;
import no.ntnu.nav.Database.*;
import no.ntnu.nav.SimpleSnmp.*;
import no.ntnu.nav.getDeviceData.Netbox;
import no.ntnu.nav.getDeviceData.dataplugins.*;
import no.ntnu.nav.getDeviceData.deviceplugins.*;
import no.ntnu.nav.Path;

// select swportid,boksid,sysname,typeid,ifindex,modul,port,status,speed,duplex,media,trunk from swport join boks using (boksid) join type using (typeid) where typegruppe like '3%' and swport.static='f' order by boksid,modul,port;
// select count(*) from swport join boks using (boksid) join type using (typeid) where typegruppe like '3%' and swport.static='f';
// SELECT DISTINCT typeid FROM swport JOIN boks USING(boksid) WHERE swport.static='t';


// For å slette alle swportvlan records dette scriptet fyller inn
// DELETE FROM swportvlan WHERE swportid IN (SELECT swportid FROM swport JOIN boks USING(boksid) NATURAL JOIN type WHERE watch='f' AND (typegruppe LIKE '3%' OR typegruppe IN ('catmeny-sw', 'cat1900-sw')))

class getDeviceData
{
	public static final String dbConfigFile = (Path.sysconfdir + "/db.conf").replace('/', File.separatorChar);
	public static final String configFile = (Path.sysconfdir + "/getDeviceData.conf").replace('/', File.separatorChar);
	public static final String scriptName = "getDeviceData";
	public static final String logFile = (Path.localstatedir + "/log/getDeviceData.log").replace('/', File.separatorChar);

	public static int NUM_THREADS = 16;
	public static final int SHOW_TOP = 25;

	public static final boolean DB_COMMIT = true;


	public static void main(String[] args) throws SQLException
	{
		String cf = null;
		String qNetbox = null;
		// Check arguments
		if (args.length > 0) {
			try {
				NUM_THREADS = Integer.parseInt(args[0]);
			} catch (NumberFormatException e) {
				// Assume this argument is a netbox name
				qNetbox = args[0].trim();
				System.out.println("Overriding netbox: " + qNetbox);
				// Is next arg number of threads?
				if (args.length > 1) {
					try {
						NUM_THREADS = Integer.parseInt(args[1]);
					} catch (NumberFormatException ee) {
						// Assume this argument is the name of the config file
						File f = new File(args[0]);
						if (f.exists() && !f.isDirectory()) {
							cf = f.getAbsolutePath();
							System.out.println("Overriding configfile: " + f.getAbsolutePath());
						}
						// Is next arg number of threads?
						if (args.length > 2) {
							try {
								NUM_THREADS = Integer.parseInt(args[2]);
								System.out.println("Overriding number of threads: " + NUM_THREADS);
							} catch (NumberFormatException eee) {
								System.out.println("Error, unrecognized argument: " + args[2]);
								return;
							}
						}
					}
				}
			}
			if (NUM_THREADS > 128) {
				System.out.println("Error, more than 128 threads not recommended, re-compile needed.");
				return;
			}
		}

		// Init logger
		Log.init(logFile, "getDeviceData");
		Log.setDefaultSubsystem("MAIN");

		Log.i("INIT", "============ getDeviceData starting ============");
		Log.i("INIT", "Running with " + NUM_THREADS + " threads (max)");

		ConfigParser cp, dbCp;
		try {
			if (cf == null) cf = configFile;
			cp = new ConfigParser(cf);
		} catch (IOException e) {
			Log.e("INIT", "Could not read config file: " + cf);
			return;
		}
		try {
			dbCp = new ConfigParser(dbConfigFile);
		} catch (IOException e) {
			Log.e("INIT", "Could not read config file: " + dbConfigFile);
			return;
		}
		if (!Database.openConnection(dbCp.get("dbhost"), dbCp.get("dbport"), dbCp.get("db_nav"), dbCp.get("script_"+scriptName), dbCp.get("userpw_"+dbCp.get("script_"+scriptName)))) {
			Log.e("INIT", "Could not connect to database!");
			return;
		}

		// Load config
		int loadDataInterval;
		try {
			loadDataInterval = Integer.parseInt(cp.get("loadDataInterval"));
		} catch (Exception e) {
			loadDataInterval = 30; // Default is every 30 minutes
		}
		loadDataInterval *= 60 * 1000; // Convert from minutes to in milliseconds

		// Hent data
		/*
		loadData();
		Timer loadDataTimer = new Timer();
		loadDataTimer.schedule(new LoadDataTask(), loadDataInterval, loadDataInterval);
		*/

		// Set up the plugin monitor
		Map dataClassMap = new HashMap();
		Map deviceClassMap = new HashMap();

		Timer pluginTimer = new Timer(true);
		PluginMonitorTask pmt = new PluginMonitorTask("data-plugins", dataClassMap, "device-plugins", deviceClassMap);
		// Load all plugins
		Log.d("INIT", "Loading plugins");
		pmt.run();
		// Check for new plugin every 5 seconds
		pluginTimer.schedule(pmt, 5 * 1000, 5 * 1000);

		// Start the query scheduler
		Log.d("INIT", "Starting query scheduler");
		QueryNetbox.init(NUM_THREADS, loadDataInterval, cp, dataClassMap, deviceClassMap, qNetbox);

	}

	/*
	private static String formatTime(long t)
	{
		long h = t / (60 * 60 * 1000);
		t %= 60 * 60 * 1000;

		long m = t / (60 * 1000);
		t %= 60 * 1000;

		long s = t / (1000);
		t %= 1000;

		long ms = t;

		return format(h,2)+":"+format(m,2)+":"+format(s,2)+"."+format(ms,3);
	}
	*/

	private static HashMap getHashFromResultSet(ResultSet rs, ResultSetMetaData md, boolean convertNull) throws SQLException {
		HashMap hm = new HashMap();
		for (int i=md.getColumnCount(); i > 0; i--) {
			String val = rs.getString(i);
			hm.put(md.getColumnName(i), (convertNull&&val==null)?"":val);
		}
		return hm;
	}

}












