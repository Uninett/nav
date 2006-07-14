/*
 * autodiscovery
 * 
 * $LastChangedRevision: 2979 $
 *
 * $LastChangedDate: 2004-10-25 21:23:56 +0200 (Mon, 25 Oct 2004) $
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
import no.ntnu.nav.Path;

/**
 * autodiscovery detects SNMP capable devices on the network
 *
 * @version $LastChangedRevision: 2979 $ $LastChangedDate: 2004-10-25 21:23:56 +0200 (Mon, 25 Oct 2004) $
 * @author Kristian Eide &lt;kreide@online.no&gt;
 */

class autodiscovery
{
	public static final String navConfigFile = (Path.sysconfdir + "/nav.conf").replace('/', File.separatorChar);
	public static final String dbConfigFile = (Path.sysconfdir + "/db.conf").replace('/', File.separatorChar);
	public static final String configFile = (Path.sysconfdir + "/autodiscovery.conf").replace('/', File.separatorChar);
	public static final String scriptName = "getDeviceData";
	public static final String logFile = (Path.localstatedir + "/log/autodiscovery.log").replace('/', File.separatorChar);

	public static int NUM_THREADS = 16;

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
		Log.init(logFile, "autodiscovery");
		Log.setDefaultSubsystem("MAIN");

		Log.i("INIT", "============ autodiscovery starting ============");
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

		// Start the discovery scheduler
		Log.d("INIT", "Starting discovery scheduler");
		DiscoveryThread.init(NUM_THREADS, cp, navCp);

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












