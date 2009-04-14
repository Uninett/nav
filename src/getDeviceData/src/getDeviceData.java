/*
 * getDeviceData
 * 
 * $LastChangedRevision: 3500 $
 *
 * $LastChangedDate: 2006-07-05 14:23:14 +0200 (ons, 05 jul 2006) $
 *
 * Copyright 2002-2004 Norwegian University of Science and Technology
 * 
 * This file is part of Network Administration Visualized (NAV)
 * 
 * NAV is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 * 
 * NAV is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with NAV; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 */

import java.io.File;
import java.io.IOException;
import java.sql.ResultSet;
import java.sql.ResultSetMetaData;
import java.sql.SQLException;
import java.util.HashMap;
import java.util.Map;
import java.util.Timer;

import no.ntnu.nav.Path;
import no.ntnu.nav.ConfigParser.ConfigParser;
import no.ntnu.nav.Database.Database;
import no.ntnu.nav.logger.Log;

/**
 * getDeviceData is the central SNMP data collection daemon in NAV.
 *
 * @version $LastChangedRevision: 3500 $ $LastChangedDate: 2006-07-05 14:23:14 +0200 (ons, 05 jul 2006) $
 * @author Kristian Eide &lt;kreide@online.no&gt;
 */

// select swportid,boksid,sysname,typeid,ifindex,modul,port,status,speed,duplex,media,trunk from swport join boks using (boksid) join type using (typeid) where typegruppe like '3%' and swport.static='f' order by boksid,modul,port;
// select count(*) from swport join boks using (boksid) join type using (typeid) where typegruppe like '3%' and swport.static='f';
// SELECT DISTINCT typeid FROM swport JOIN boks USING(boksid) WHERE swport.static='t';


// For � slette alle swportvlan records dette scriptet fyller inn
// DELETE FROM swportvlan WHERE swportid IN (SELECT swportid FROM swport JOIN boks USING(boksid) NATURAL JOIN type WHERE watch='f' AND (typegruppe LIKE '3%' OR typegruppe IN ('catmeny-sw', 'cat1900-sw')))

class getDeviceData
{
	public static final String navConfigFile = (Path.sysconfdir + "/nav.conf").replace('/', File.separatorChar);
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

		ConfigParser cp, navCp, dbCp;
		try {
			if (cf == null) cf = configFile;
			cp = new ConfigParser(cf);
		} catch (IOException e) {
			Log.e("INIT", "Could not read config file: " + cf);
			return;
		}
		try {
			navCp = new ConfigParser(navConfigFile);
		} catch (IOException e) {
			Log.e("INIT", "Could not read config file: " + navConfigFile);
			return;
		}
		if (!Database.openConnection(scriptName, "nav")) {
			Log.e("INIT", "Could not connect to database!");
			return;
		}

		// Set default OID freq
		int defaultOidFrequency;
		try {
			defaultOidFrequency = Integer.parseInt(cp.get("defaultOidFrequency"));
			if (defaultOidFrequency > 0) {
				defaultOidFrequency *= 60;
				OidTester.DEFAULT_FREQ = defaultOidFrequency;
			}
		} catch (Exception e) {
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
		QueryNetbox.init(NUM_THREADS, loadDataInterval, cp, navCp, dataClassMap, deviceClassMap, qNetbox);

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












