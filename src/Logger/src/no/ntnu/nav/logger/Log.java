/*
 * Log
 * 
 * $LastChangedRevision$
 *
 * $LastChangedDate$
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

package no.ntnu.nav.logger;

import java.util.*;
import java.io.*;
import java.text.*;

import no.ntnu.nav.ConfigParser.*;
import no.ntnu.nav.Path;

/**
 * <p> Class for logging messages in NAV (variation on the Cisco
 * format) log format. </p>
 *
 * <p> An example log entry line: </p>
 *
 * <p> <pre> May 27 08:32:58 2002 bokser.pl DBBOX-3-ORG &lt;msg&gt; </pre>
 * </p>
 *
 * <p> First is the time, then name of the system, then a tripple with
 * name of the subsystem, priority and the type (system, subsystem and
 * type must be unique). Last is the log message. </p>
 *
 * @version $LastChangedRevision$ $LastChangedDate$
 * @author Kristian Eide &lt;kreide@online.no&gt;
 */

public class Log {

	private static File log;
	private static String system;
	private static Map subsystemMap = Collections.synchronizedMap(new HashMap());
	private static Map threadIdMap = Collections.synchronizedMap(new HashMap());
	private static Map netboxMap = Collections.synchronizedMap(new HashMap());

	public static final int MSG_EMERGENCY = 0;
	public static final int MSG_ALERT = 1;
	public static final int MSG_CRITICAL = 2;
	public static final int MSG_ERROR = 3;
	public static final int MSG_WARNING = 4;
	public static final int MSG_INFO = 5;
	public static final int MSG_DEBUG = 6;	

	private static final String navConfigFile = (Path.sysconfdir + "/nav.conf").replace('/', File.separatorChar);
	private static int DEBUG_LEVEL = MSG_DEBUG;


	/**
	 * Init the logger with the given filename; if the filename is null stdout is used.
	 */
	public static void init(String fn, String system) {
		File f = (fn != null) ? new File(fn) : null;
		init(f, system);
	}

	/**
	 * Init the logger with the given file; if the file is null stdout is used.
	 */
	public static void init(File f, String system) {
		if (f != null) log = f;
		Log.system = system;

		ConfigParser navCp;
		try {
			navCp = new ConfigParser(navConfigFile);
			Log.DEBUG_LEVEL = Integer.parseInt(navCp.get("DEBUG_LEVEL"));
			String ss = navCp.get("DEBUG_LEVEL_" + system.toUpperCase());
			if (ss != null) {
				Log.DEBUG_LEVEL = Integer.parseInt(ss);
			}
		} catch (Exception e) {
		}
	}

	/**
	 * Set the netbox name to use. If set, this will be included
	 * instead of the system name (which is redundant as it is given
	 * by the log filename).
	 */
	public static void setNetbox(String netbox) {
		if (netbox == null) netboxMap.remove(Thread.currentThread());
		else netboxMap.put(Thread.currentThread(), netbox);
	}

	/**
	 * Set the default subsystem name to use. This is stored per thread,
	 * and it is thus safe for multiple threads to use this method at
	 * the same time. The thread should call freeThread before exiting
	 * to enable probler garbage collection since this class keeps a
	 * reference to the thread context.
	 */
	public static void setDefaultSubsystem(String subsystem) {
		subsystemMap.put(Thread.currentThread(), subsystem);
	}

	/**
	 * Set a unique identifier for the thread. This identifier will be
	 * appended to the system-string in the log. The thread should call
	 * freeThread before exiting to enable probler garbage collection
	 * since this class keeps a reference to the thread context.
	 */
	public static void setThreadId(String id) {
		threadIdMap.put(Thread.currentThread(), id);
	}

	/**
	 * Remove all references to the calling thread.
	 */
	public static void freeThread() {
		subsystemMap.remove(Thread.currentThread());
		threadIdMap.remove(Thread.currentThread());
	}

	/**
	 * Log emergency
	 */
	public static void emergency(String type, String msg) {
		emergency(null, type, msg);
	}
	/**
	 * Log emergency
	 */
	public static void emergency(String subsystem, String type, String msg) {
		log(MSG_EMERGENCY, subsystem, type, msg);
	}

	/**
	 * Log alert
	 */
	public static void a(String type, String msg) {
		a(null, type, msg);
	}
	/**
	 * Log alert
	 */
	public static void a(String subsystem, String type, String msg) {
		log(MSG_ALERT, subsystem, type, msg);
	}

	/**
	 * Log critical
	 */
	public static void c(String type, String msg) {
		c(null, type, msg);
	}
	/**
	 * Log critical
	 */
	public static void c(String subsystem, String type, String msg) {
		log(MSG_CRITICAL, subsystem, type, msg);
	}

	/**
	 * Log error
	 */
	public static void e(String type, String msg) {
		e(null, type, msg);
	}
	/**
	 * Log error
	 */
	public static void e(String subsystem, String type, String msg) {
		log(MSG_ERROR, subsystem, type, msg);
	}

	/**
	 * Log warning
	 */
	public static void w(String type, String msg) {
		w(null, type, msg);
	}
	/**
	 * Log warning
	 */
	public static void w(String subsystem, String type, String msg) {
		log(MSG_WARNING, subsystem, type, msg);
	}

	/**
	 * Log info
	 */
	public static void i(String type, String msg) {
		i(null, type, msg);
	}
	/**
	 * Log info
	 */
	public static void i(String subsystem, String type, String msg) {
		log(MSG_INFO, subsystem, type, msg);
	}

	/**
	 * Log debug
	 */
	public static void d(String type, String msg) {
		d(null, type, msg);
	}
	/**
	 * Log debug
	 */
	public static void d(String subsystem, String type, String msg) {
		log(MSG_DEBUG, subsystem, type, msg);
	}

	/**
	 * Log message using the given priority
	 */	
	public static synchronized void log(int priority, String subsystem, String type, String msg) {
		if (priority > DEBUG_LEVEL) return;

		// May 27 08:32:58 2002 bokser.pl DBBOX-3-ORG <msg>
		SimpleDateFormat sdf = new SimpleDateFormat("MMM dd HH:mm:ss yyyy");

		String netbox = (String)netboxMap.get(Thread.currentThread());
		String sys = netbox != null ? netbox : system;

		// Get default
		if (subsystem == null) subsystem = (String)subsystemMap.get(Thread.currentThread());
		if (msg == null) msg = "";

		String id = "";
		if (threadIdMap.containsKey(Thread.currentThread())) id = "_" + threadIdMap.get(Thread.currentThread());

		try {
			PrintStream out;
			if (log == null) {
				out = System.out;
			} else {
				out = new PrintStream(new BufferedOutputStream(new FileOutputStream(log, true)));
			}

			String t = sdf.format(new GregorianCalendar().getTime()) + " " + sys + id + " " + subsystem+"-"+priority+"-"+type + " " + msg;

			// Capitalize first letter of log text (name of month)
			t = t.substring(0, 1).toUpperCase() + t.substring(1, t.length());
			
			out.println(t);
			if (log != null) out.close();
		} catch (IOException e) {
			System.err.println("Logger: IOException when logging to file " + log + ": " + e.getMessage());
		}
	}

}
