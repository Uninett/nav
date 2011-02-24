/*
 * eventEngine
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

import java.io.*;
import java.util.*;
import java.util.jar.*;
import java.net.*;
import java.text.*;
import java.lang.reflect.Method;
import java.lang.reflect.InvocationTargetException;

import java.sql.*;

import no.ntnu.nav.ConfigParser.*;
import no.ntnu.nav.Database.*;
import no.ntnu.nav.logger.*;
import no.ntnu.nav.eventengine.*;
import no.ntnu.nav.Path;

/**
 * eventEngine processes events posted on the eventq via plugin modules.
 *
 * @version $LastChangedRevision$ $LastChangedDate$
 * @author Kristian Eide &lt;kreide@online.no&gt;
 */

class eventEngine
{
	public static final String navConfigFile = (Path.sysconfdir + "/nav.conf").replace('/', File.separatorChar);
	public static final String configFile = (Path.sysconfdir + "/eventEngine.conf").replace('/', File.separatorChar);
	public static final String alertmsgFile = (Path.sysconfdir + "/alertmsg.conf").replace('/', File.separatorChar);
	public static final String scriptName = "eventEngine";
	public static final String logFile = (Path.localstatedir + "/log/eventEngine.log").replace('/', File.separatorChar);

	public static final boolean ERROR_OUT = true;
	public static final boolean VERBOSE_OUT = true;
	public static final boolean DEBUG_OUT = true;

	public static final boolean DB_UPDATE = true;
	public static final boolean DB_COMMIT = true;

	// END USER CONFIG //

	// A timer
	static Thread[] threads;
	static Timer timer;
	static Stack idleThreads;

	//static HashSet safeCloseBoksid = new HashSet();
	static String qBoks;
	static ConfigParser navCp;

	public static void main(String[] args) throws Exception
	{
		String cf = null;
		// Check arguments
		if (args.length > 0) {
			// Assume this argument is the config file
			File f = new File(args[0]);
			if (f.exists() && !f.isDirectory()) cf = f.getAbsolutePath();
		}

		try {
			navCp = new ConfigParser(navConfigFile);
		} catch (IOException e) {
			Log.e("INIT", "Could not read config file: " + navConfigFile);
			return;
		}
		if (!Database.openConnection(scriptName, "nav")) {
			System.err.println("Error, could not connect to database!");
			return;
		}

		// Init logger
		Log.init(logFile, "eventEngine");

		// Deamon timer
		timer = new Timer(false);

		// Set up the config file monitor
		if (cf == null) cf = configFile;
		ConfigFileMonitorTask cfmt = new ConfigFileMonitorTask(cf, navCp);
		if (cfmt.cfNotFound()) {
			System.err.println("Error, could not read config file: " + cf);
			return;
		}
		cfmt.run(); // Load config first time
		timer.schedule(cfmt, 5 * 1000, 5 * 1000); // 5 second delay

		MessagePropagatorImpl mp = new MessagePropagatorImpl();

		HashMap handlerClassMap = new HashMap();
		HashMap deviceMap = new HashMap();

		DeviceDBImpl devDB;
		try {
			devDB = new DeviceDBImpl(mp, deviceMap, timer, alertmsgFile);
		} catch (ParseException e) {
			System.err.println("While reading " + alertmsgFile + ":");
			System.err.println("  " + e.getMessage());
			return;
		}

		// The eventq monitor
		EventqMonitorTask emt = new EventqMonitorTask(mp, handlerClassMap, devDB, cfmt);

		// Set up the plugin monitor
		PluginMonitorTask pmt = new PluginMonitorTask("device-plugins", new HashMap(), "handler-plugins", handlerClassMap, devDB, deviceMap, emt );
		mp.setPluginMonitorTask(pmt);
		pmt.run(); // Load all plugins

		timer.schedule(pmt, 5 * 1000, 5 * 1000); // Check for new plugin every 5 seconds
		timer.schedule(emt, 5 * 1000, 5 * 1000); // Check for new events every 5 seconds

	}

	static class MessagePropagatorImpl implements MessagePropagator {
		private PluginMonitorTask pmt;

		void setPluginMonitorTask(PluginMonitorTask pmt) {
			this.pmt = pmt;
		}

		public void updateFromDB() {
			pmt.updateFromDB();
		}
	}

	private static String format(long i, int n)
	{
		DecimalFormat nf = new DecimalFormat("#");
		nf.setMinimumIntegerDigits(n);
		return nf.format(i);
	}
	public static String formatTime(long t)
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
	private static HashMap getHashFromResultSet(ResultSet rs, ResultSetMetaData md, boolean convertNull) throws SQLException {
		HashMap hm = new HashMap();
		for (int i=md.getColumnCount(); i > 0; i--) {
			String val = rs.getString(i);
			hm.put(md.getColumnName(i), (convertNull&&val==null)?"":val);
		}
		return hm;
	}

}

class ConfigFileMonitorTask extends TimerTask
{
	private File cf;
	private ConfigParser cp;
	private boolean cfNotFound;
	private long lastMod;
	private ConfigParser navCp;

	public ConfigFileMonitorTask(String cfPath, ConfigParser navCp)
	{
		cf = new File(cfPath);
		if (!cf.isFile()) cfNotFound = true;
		this.navCp = navCp;
	}

	public void run()
	{
		if (cfNotFound) return;
		if (lastMod == cf.lastModified()) return;
		lastMod = cf.lastModified();

		try {
			cp = new ConfigParser(cf.getAbsolutePath());
			cp.setObject("navCp", navCp);
		} catch (IOException e) {
			Log.w("CONFIG_FILE_MONITOR_TASK", "RUN", "Could not read config file: " + cf);
			return;
		}
	}

	public ConfigParser getConfigParser() {
		return cp;
	}

	public boolean cfNotFound() { return cfNotFound; }

}

class PluginMonitorTask extends TimerTask
{
	private static final int UPDATE_INTERVAL = 60 * 60 * 1000;

  DynamicURLClassLoader cl = new DynamicURLClassLoader();

	File deviceDir, handlerDir;
	Map deviceClassMap, handlerClassMap;

	Map deviceFileMap = new HashMap();
	Map handlerFileMap = new HashMap();

	DeviceDBImpl devDB;
	Map deviceMap;
	EventqMonitorTask emt;

	private long lastDBUpdate = System.currentTimeMillis();

	public PluginMonitorTask(String devicePath, Map deviceClassMap, String handlerPath, Map handlerClassMap, DeviceDBImpl devDB, Map deviceMap, EventqMonitorTask emt)
	{
		deviceDir = new File(devicePath);
		this.deviceClassMap = deviceClassMap;
		handlerDir = new File(handlerPath);
		this.handlerClassMap = handlerClassMap;
		this.devDB = devDB;
		this.deviceMap = deviceMap;
		this.emt = emt;

		if (!deviceDir.isDirectory() || !handlerDir.isDirectory()) {
			Log.w("PLUGIN_MONITOR_TASK", "CONSTRUCTOR", "Plugins directory not found, exiting...");
			System.exit(0);
		}
	}

	public synchronized void run()
	{
		// Update Devices
		if (update(deviceDir, deviceFileMap, deviceClassMap, deviceDir.listFiles() ) ||
				(System.currentTimeMillis()-lastDBUpdate > UPDATE_INTERVAL)) {
			updateFromDB();
			lastDBUpdate = System.currentTimeMillis();
		}

		// Update EventHandlers
		if (update(handlerDir, handlerFileMap, handlerClassMap, deviceDir.listFiles() )) {
			emt.updateCache();
		}
	}

	public synchronized void updateFromDB() {
		devDB.startDBUpdate();
		Class[] ddbClass = new Class[1];
		Object[] o = new Object[] { devDB };
		try {
			ddbClass[0] = Class.forName("no.ntnu.nav.eventengine.DeviceDB");
		} catch (ClassNotFoundException e) {
			System.err.println("ClassNotFoundException when getting DeviceDB reference: " + e.getMessage());
			e.printStackTrace(System.err);
		}

		List deviceClassList = new ArrayList();
		for (Iterator i = deviceClassMap.values().iterator(); i.hasNext();) {
			Class c = (Class)i.next();
			deviceClassList.add(new DeviceClassEntry(findDepth(c), c));
		}

		Collections.sort(deviceClassList);

		for (Iterator i = deviceClassList.iterator(); i.hasNext();) {
			Class c = ((DeviceClassEntry)i.next()).deviceClass;
			try {
				Method m = c.getMethod("updateFromDB", ddbClass);
				m.invoke(null, o);
			} catch (NoSuchMethodException e) {
				Log.w("PLUGIN_MONITOR_TASK", "CONSTRUCTOR", "NoSuchMethodException when invoking updateFromDB in class " + c.getName() + ": " + e.getMessage());
				e.printStackTrace(System.err);
			} catch (IllegalAccessException e) {
				Log.w("PLUGIN_MONITOR_TASK", "CONSTRUCTOR", "IllegalAccessException when invoking updateFromDB in class " + c.getName() + ": " + e.getMessage());
				e.printStackTrace(System.err);
			} catch (InvocationTargetException e) {
				Log.w("PLUGIN_MONITOR_TASK", "CONSTRUCTOR", "InvocationTargetException when invoking updateFromDB in class " + c.getName() + ": " + e.getMessage());
				e.printStackTrace(System.err);
			}

		}

		devDB.endDBUpdate();
		classDepthCache.clear();

		// Now call 'init' for all devices
		for (Iterator i = deviceMap.values().iterator(); i.hasNext();) ((Device)i.next()).init(devDB);

		//Device d = (Device)devDB.getDevice(279);
		//errl("Found:\n"+d);
	}



	class DeviceClassEntry implements Comparable
	{
		int depth;
		Class deviceClass;
		public DeviceClassEntry(int depth, Class c)
		{
			this.depth = depth;
			this.deviceClass = c;
		}
		public int compareTo(Object o)
		{
			DeviceClassEntry dc = (DeviceClassEntry)o;
			return new Integer(depth).compareTo(new Integer(dc.depth)) * -1; // Sort in reverse order, biggest first
		}
	}

	HashMap classDepthCache = new HashMap();
	private int findDepth(Class c)
	{
		Integer depth;
		if ( (depth=(Integer)classDepthCache.get(c.getName())) != null) return depth.intValue();

		Class parent = c.getSuperclass();
		if (parent == null) return 0;

		classDepthCache.put(c.getName(), depth = new Integer(findDepth(parent)+1));
		Log.d("PLUGIN_MONITOR_TASK", "CONSTRUCTOR", "Class " + c.getName() + " has depth " + depth.intValue());

		return depth.intValue();
	}

	private boolean update(File pluginDir, Map fileMap, Map pluginMap, File[] dependFiles)
	{
		// The cloneMap is used to remove plugins whose .jar file is deleted
		Map cloneMap = (Map) ((HashMap)pluginMap).clone();

		boolean hasChanged = false;
		File[] fileList = pluginDir.listFiles();

		if (dependFiles != null) {
			for (int i=0; i < dependFiles.length; i++) {
				try {
						cl.appendURL(dependFiles[i].toURL());
				} catch (MalformedURLException e) {} // Should never happen
			}
		}

		for (int i=0; i < fileList.length; i++) {
			if (!fileList[i].getName().toLowerCase().endsWith(".jar")) continue;
			cloneMap.remove(fileList[i].getName());

			try {
				Long lastMod;
				// If new or modified JAR
				if ( (lastMod=(Long)fileMap.get(fileList[i].getName())) == null || 
						 !lastMod.equals(new Long(fileList[i].lastModified())) ) {
					fileMap.put(fileList[i].getName(), new Long(fileList[i].lastModified()));

					cl.appendURL(fileList[i].toURL());

					JarFile jf = new JarFile(fileList[i]);
					Manifest mf = jf.getManifest();
					Attributes attr = mf.getMainAttributes();
					String cn = attr.getValue("Plugin-Class");
					Log.d("PLUGIN_MONITOR_TASK", "UPDATE", "New or modified jar, trying to load " + fileList[i].getName());

					if (cn == null) {
						Log.d("PLUGIN_MONITOR_TASK", "UPDATE", "JAR is missing Plugin-Class manifest, skipping...");
						continue;
					}

					Class c, deviceClass, handlerInterface;
					try {
						deviceClass = Class.forName("no.ntnu.nav.eventengine.Device");
						handlerInterface = Class.forName("no.ntnu.nav.eventengine.EventHandler");

						c = cl.loadClass(cn);
					} catch (ClassNotFoundException e) {
						Log.w("PLUGIN_MONITOR_TASK", "UPDATE", "Class " + cn + " not found in jar " + fileList[i].getName() + ", msg: " + e.getMessage());
						continue;
					} catch (NoClassDefFoundError e) {
						Log.w("PLUGIN_MONITOR_TASK", "UPDATE", "NoClassDefFoundError when loading class " + cn + " from jar " + fileList[i].getName() + ", msg: " + e.getMessage());
						continue;
					}

					if (deviceClass.isAssignableFrom(c) || handlerInterface.isAssignableFrom(c)) {
						// Found new Device, add to list
						pluginMap.put(fileList[i].getName(), c);
						hasChanged = true;
						Log.d("PLUGIN_MONITOR_TASK", "UPDATE", "OK! JAR Loaded and added to pluginMap");
					} else {
						Log.w("PLUGIN_MONITOR_TASK", "UPDATE", "Failed! Class " + cn + " is not an event engine plugin");
					}
				}
			} catch (IOException e) {
				Log.e("PLUGIN_MONITOR_TASK", "UPDATE", "IOException when loading jar " + fileList[i].getName() + ", msg: " + e.getMessage());
			}
		}

		Iterator i = cloneMap.keySet().iterator();
		while (i.hasNext()) {
			String fn = (String)i.next();
			Log.d("PLUGIN_MONITOR_TASK", "UPDATE", "Removing jar " + fn + " from pluginMap");
			pluginMap.remove(fn);
			fileMap.remove(fn);
			hasChanged = true;
		}
		return hasChanged;
	}

	class DynamicURLClassLoader extends URLClassLoader {
		Set urlSet = new HashSet();

		DynamicURLClassLoader() {
			super(new URL[0]);
		}
		public void appendURL(URL u) {
			if (urlSet.add(u)) {
				addURL(u);
			}
		}
	}

}


class EventqMonitorTask extends TimerTask implements EventHandler
{
	MessagePropagator mp;
	Map handlerClassMap;
	DeviceDBImpl devDB;
	ConfigFileMonitorTask cfmt;

	Map handlerCache = new HashMap();
	int lastEventqid = 0;

	public EventqMonitorTask(MessagePropagator mp, Map handlerClassMap, DeviceDBImpl devDB, ConfigFileMonitorTask cfmt)
	{
		this.mp = mp;
		this.handlerClassMap = handlerClassMap;
		this.devDB = devDB;
		this.cfmt = cfmt;
	}

	public void updateCache()
	{
		//Map cloneMap = (Map) ((HashMap)handlerClassMap).clone();
		handlerCache.clear();
		handlerCache.put(handleEventTypes()[0], new ArrayList( Arrays.asList(new Object[] { this }) ));
		handlerCache.put("_all", new ArrayList());
		for (Iterator i=handlerClassMap.values().iterator(); i.hasNext();) {
			Class c = (Class)i.next();
			EventHandler eh;
			try {
				eh = (EventHandler)c.newInstance();
			} catch (InstantiationException e) {
				Log.w("EVENTQ_MONITOR_TASK", "UPDATE_CACHE", "Main EventHandler plugin class must have a public default (no args) constructor:" + e.getMessage());
				continue;
			} catch (IllegalAccessException e) {
				Log.w("EVENTQ_MONITOR_TASK", "UPDATE_CACHE", "Main EventHandler plugin class must have a public default (no args) constructor:" + e.getMessage());
				continue;
			}
			String[] s = eh.handleEventTypes();
			for (int j=0; j < s.length; j++) {
				List l;
				if ( (l=(List)handlerCache.get(s[j])) == null) handlerCache.put( s[j], l=new ArrayList());
				l.add(eh);
			}
		}

	}

	public String[] handleEventTypes() { return new String[] { "notification" }; }
	public void handle(DeviceDB ddb, Event e, ConfigParser cp) {
		// Event for me!
		String cmd = e.getVar("command");
		if ("updateFromDB".equals(cmd)) {
			mp.updateFromDB();
			e.dispose();
		} else
		if ("dumpDeviceList".equals(cmd)) {
			List devL = new ArrayList();
			for (Iterator it=devDB.getDeviceMap().keySet().iterator(); it.hasNext();) {
				devL.add(it.next());
			}
			Collections.sort(devL);
			Log.d("EVENTQ_MONITOR_TASK", "DUMP_DEVICE_LIST", "Devices known: " + devL);
			e.dispose();
		} else {
			Log.d("EVENTQ_MONITOR_TASK", "RUN", "Unknown notification command: " + cmd);
			e.defer("Unknown notification command: " + cmd);
		}
	}

	public void run()
	{
		try {
			ResultSet rs = Database.query("SELECT eventqid,source,deviceid,netboxid,subid,time,eventtypeid,state,value,severity,var,val FROM eventq LEFT JOIN eventqvar USING (eventqid) WHERE eventqid > "+lastEventqid + " AND target='eventEngine' AND severity >= 0 ORDER BY eventqid");

			List eventList = new ArrayList();
			while (rs.next()) {
				eventList.add(DeviceDBImpl.eventFactory(rs));
			}
			if (rs.last()) if (rs.getInt("eventqid") > lastEventqid) lastEventqid = rs.getInt("eventqid");
			
			if (!eventList.isEmpty()) {
				Log.d("EVENTQ_MONITOR_TASK", "RUN", "Fetched " + eventList.size() + " events from eventq");
			} else {
				return;
			}

			int eventCnt=0;
			for (Iterator it = eventList.iterator(); it.hasNext();) {
				Event e = (Event)it.next();
				eventCnt++;
				Log.d("EVENTQ_MONITOR_TASK", "RUN", "Got event: " + e);

				String eventtypeid = e.getEventtypeid();
				List eventHandlerList = new ArrayList( (List)handlerCache.get("_all")); // Handlers handling all events
				{
					List handlers = (List) handlerCache.get( (handlerCache.containsKey(eventtypeid) ? eventtypeid : "info") ) ;
					if (handlers != null) eventHandlerList.addAll(handlers);
				}
				if (eventHandlerList.isEmpty()) {
					Log.w("EVENTQ_MONITOR_TASK", "RUN", "No handler found for eventtype: " + eventtypeid);
					continue;
				}
				for (Iterator handlerIt = eventHandlerList.iterator(); handlerIt.hasNext();) {
					EventHandler eh = (EventHandler) handlerIt.next();
					Log.d("EVENTQ_MONITOR_TASK", "RUN", "Found handler: " + eh.getClass().getName());
					Database.beginTransaction();
					try {
						eh.handle(devDB, e, cfmt.getConfigParser() );

					} catch (Exception exp) {
						Log.e("EVENTQ_MONITOR_TASK", "RUN", "Got Exception from handler: " + eh.getClass().getName() + " Msg: " + exp.getMessage());
						exp.printStackTrace(System.err);

						// Rollback any database changes
						Database.rollback();
					}
					Database.commit();

				}
			}

			Log.d("EVENTQ_MONITOR_TASK", "RUN", "Processed " + eventCnt + " events in this session");

		} catch (SQLException e) {
			// Now we are in trouble
			Log.e("EVENTQ_MONITOR_TASK", "RUN", "SQLException when fetching from eventq: " + e.getMessage());
			e.printStackTrace(System.err);
		}
	}



/*

1673

BEGIN;
INSERT INTO eventq (source,target,netboxid,eventtypeid,state,severity) VALUES ('pping','getDeviceData',1022,'notification','x',0);
INSERT INTO eventqvar (eventqid,var,val) VALUES ((SELECT eventqid FROM eventq WHERE target='getDeviceData' AND netboxid=1022),'command','runNetbox');
COMMIT;

BEGIN;
INSERT INTO eventq (source,target,eventtypeid,state,severity) VALUES ('pping','getDeviceData','notification','x',0);
INSERT INTO eventqvar (eventqid,var,val) VALUES ((SELECT eventqid FROM eventq WHERE target='getDeviceData'),'command','updateFromDB');
COMMIT;

BEGIN;
INSERT INTO eventq (source,target,subid,eventtypeid,state,severity) VALUES ('eventEngine','eventEngine',65432,'notification','x',0);
INSERT INTO eventqvar (eventqid,var,val) VALUES ((SELECT eventqid FROM eventq WHERE subid=65432),'command','updateFromDB');
COMMIT;

BEGIN;
INSERT INTO eventq (source,target,subid,eventtypeid,state,severity) VALUES ('eventEngine','eventEngine',76543,'notification','x',0);
INSERT INTO eventqvar (eventqid,var,val) VALUES ((SELECT eventqid FROM eventq WHERE subid=76543),'command','dumpDeviceList');
COMMIT;


// Down
sit-sby6-936-h.ntnu.no
sit-sby6-936-h2.ntnu.no (shadow)
BEGIN;
INSERT INTO eventq (source,target,deviceid,netboxid,eventtypeid,state,severity) VALUES ('pping','eventEngine',(SELECT deviceid FROM netbox WHERE sysname LIKE 'sit-sby6-936-h.ntnu.no'),(SELECT netboxid FROM netbox WHERE sysname LIKE 'sit-sby6-936-h.ntnu.no'),'boxState','s',100);
INSERT INTO eventq (source,target,deviceid,netboxid,eventtypeid,state,severity) VALUES ('pping','eventEngine',(SELECT deviceid FROM netbox WHERE sysname LIKE 'sit-sby6-936-h2.ntnu.no'),(SELECT netboxid FROM netbox WHERE sysname LIKE 'sit-sby6-936-h2.ntnu.no'),'boxState','s',100);
COMMIT;

BEGIN;
INSERT INTO eventq (source,target,deviceid,netboxid,eventtypeid,state,severity) VALUES ('pping','eventEngine',(SELECT deviceid FROM netbox WHERE sysname LIKE 'sit-sby6-936-h.ntnu.no'),(SELECT netboxid FROM netbox WHERE sysname LIKE 'sit-sby6-936-h.ntnu.no'),'boxState','e',100);
INSERT INTO eventq (source,target,deviceid,netboxid,eventtypeid,state,severity) VALUES ('pping','eventEngine',(SELECT deviceid FROM netbox WHERE sysname LIKE 'sit-sby6-936-h2.ntnu.no'),(SELECT netboxid FROM netbox WHERE sysname LIKE 'sit-sby6-936-h2.ntnu.no'),'boxState','e',100);
COMMIT;

-- kjemi-369-sw.ntnu.no + wlan-s63-369-ap.wlan.ntnu.no
BEGIN;
INSERT INTO eventq (source,target,deviceid,netboxid,eventtypeid,state,severity) VALUES ('pping','eventEngine',(SELECT deviceid FROM netbox WHERE sysname LIKE 'kjemi-369-sw.ntnu.no'),(SELECT netboxid FROM netbox WHERE sysname LIKE 'kjemi-369-sw.ntnu.no'),'boxState','s',100);
INSERT INTO eventq (source,target,deviceid,netboxid,eventtypeid,state,severity) VALUES ('pping','eventEngine',(SELECT deviceid FROM netbox WHERE sysname LIKE 'bygg-stud-369-h.ntnu.no'),(SELECT netboxid FROM netbox WHERE sysname LIKE 'bygg-stud-369-h.ntnu.no'),'boxState','s',100);
INSERT INTO eventq (source,target,deviceid,netboxid,eventtypeid,state,severity) VALUES ('pping','eventEngine',(SELECT deviceid FROM netbox WHERE sysname LIKE 'wlan-s63-369-ap.wlan.ntnu.no'),(SELECT netboxid FROM netbox WHERE sysname LIKE 'wlan-s63-369-ap.wlan.ntnu.no'),'boxState','s',100);
COMMIT;

BEGIN;
INSERT INTO eventq (source,target,deviceid,netboxid,eventtypeid,state,severity) VALUES ('pping','eventEngine',(SELECT deviceid FROM netbox WHERE sysname LIKE 'kjemi-369-sw.ntnu.no'),(SELECT netboxid FROM netbox WHERE sysname LIKE 'kjemi-369-sw.ntnu.no'),'boxState','e',100);
INSERT INTO eventq (source,target,deviceid,netboxid,eventtypeid,state,severity) VALUES ('pping','eventEngine',(SELECT deviceid FROM netbox WHERE sysname LIKE 'bygg-stud-369-h.ntnu.no'),(SELECT netboxid FROM netbox WHERE sysname LIKE 'bygg-stud-369-h.ntnu.no'),'boxState','e',100);
INSERT INTO eventq (source,target,deviceid,netboxid,eventtypeid,state,severity) VALUES ('pping','eventEngine',(SELECT deviceid FROM netbox WHERE sysname LIKE 'wlan-s63-369-ap.wlan.ntnu.no'),(SELECT netboxid FROM netbox WHERE sysname LIKE 'wlan-s63-369-ap.wlan.ntnu.no'),'boxState','e',100);
COMMIT;

--voll-sby-980-h
BEGIN;
INSERT INTO eventq (source,target,deviceid,eventtypeid,state,severity) VALUES ('pping','eventEngine',(SELECT deviceid FROM netbox WHERE sysname LIKE 'voll-sby-980-h.%'),'boxState','s',100);
COMMIT;

BEGIN;
INSERT INTO eventq (source,target,deviceid,eventtypeid,state,severity) VALUES ('pping','eventEngine',(SELECT deviceid FROM netbox WHERE sysname LIKE 'voll-sby-980-h.%'),'boxState','e',100);
COMMIT;

BEGIN;
INSERT INTO eventq (source,target,deviceid,eventtypeid,state,severity) VALUES ('pping','eventEngine',(SELECT deviceid FROM netbox WHERE sysname LIKE 't971-6.itea.ntnu.no'),'boxState','s',100);
COMMIT;

BEGIN;
INSERT INTO eventq (source,target,deviceid,eventtypeid,state,severity) VALUES ('pping','eventEngine',(SELECT deviceid FROM netbox WHERE sysname LIKE 't971-6.itea.ntnu.no'),'boxState','e',100);
COMMIT;


--test modul
BEGIN;
INSERT INTO eventq (source,target,deviceid,netboxid,eventtypeid,state,severity) VALUES ('pping','eventEngine',(SELECT deviceid FROM netbox WHERE sysname='bib-stud-407-h.ntnu.no'),(SELECT netboxid FROM netbox WHERE sysname='bib-stud-407-h.ntnu.no'),'boxState','s',100);

INSERT INTO eventq (source,target,deviceid,netboxid,subid,eventtypeid,state,severity) VALUES ('moduleMon','eventEngine',(SELECT deviceid FROM module WHERE netboxid=(SELECT netboxid FROM netbox WHERE sysname LIKE 'bib-stud-407-h.ntnu.no') ORDER BY module DESC LIMIT 1),(SELECT netboxid FROM netbox WHERE sysname LIKE 'bib-stud-407-h.ntnu.no'),(SELECT moduleid FROM module WHERE netboxid=(SELECT netboxid FROM netbox WHERE sysname LIKE 'bib-stud-407-h.ntnu.no') ORDER BY module ASC LIMIT 1),'moduleState','s',100);


COMMIT;

BEGIN;
INSERT INTO eventq (source,target,deviceid,netboxid,subid,eventtypeid,state,severity) VALUES ('moduleMon','eventEngine',(SELECT deviceid FROM module WHERE netboxid=(SELECT netboxid FROM netbox WHERE sysname LIKE 'bib-stud-407-h.ntnu.no') ORDER BY module DESC LIMIT 1),(SELECT netboxid FROM netbox WHERE sysname LIKE 'bib-stud-407-h.ntnu.no'),(SELECT moduleid FROM module WHERE netboxid=(SELECT netboxid FROM netbox WHERE sysname LIKE 'bib-stud-407-h.ntnu.no') ORDER BY module ASC LIMIT 1),'moduleState','e',100);

INSERT INTO eventq (source,target,deviceid,netboxid,eventtypeid,state,severity) VALUES ('pping','eventEngine',(SELECT deviceid FROM netbox WHERE sysname='bib-stud-407-h.ntnu.no'),(SELECT netboxid FROM netbox WHERE sysname='bib-stud-407-h.ntnu.no'),'boxState','e',100);

COMMIT;

--kjemi-384-sw
BEGIN;
INSERT INTO eventq (source,target,deviceid,netboxid,eventtypeid,state,severity) VALUES ('pping','eventEngine',75,75,'boxState','e',100);
INSERT INTO eventq (source,target,deviceid,netboxid,eventtypeid,state,severity) VALUES ('pping','eventEngine',724,394,'boxState','e',100);
INSERT INTO eventq (source,target,deviceid,netboxid,eventtypeid,state,severity) VALUES ('pping','eventEngine',725,395,'boxState','e',100);
INSERT INTO eventq (source,target,deviceid,netboxid,eventtypeid,state,severity) VALUES ('pping','eventEngine',761,396,'boxState','e',100);
COMMIT;

BEGIN;
INSERT INTO eventq (source,target,deviceid,netboxid,eventtypeid,state,severity) VALUES ('pping','eventEngine',75,75,'boxState','s',100);
INSERT INTO eventq (source,target,deviceid,netboxid,eventtypeid,state,severity) VALUES ('pping','eventEngine',724,394,'boxState','s',100);
INSERT INTO eventq (source,target,deviceid,netboxid,eventtypeid,state,severity) VALUES ('pping','eventEngine',725,395,'boxState','s',100);
INSERT INTO eventq (source,target,deviceid,netboxid,eventtypeid,state,severity) VALUES ('pping','eventEngine',761,396,'boxState','s',100);
COMMIT;


--tekno-sw
BEGIN;
INSERT INTO eventq (source,target,deviceid,netboxid,eventtypeid,state,severity) VALUES ('pping','eventEngine',1643,627,'boxState','e',100);
INSERT INTO eventq (source,target,deviceid,netboxid,eventtypeid,state,severity) VALUES ('pping','eventEngine',9953,827,'boxState','e',100);
INSERT INTO eventq (source,target,deviceid,netboxid,eventtypeid,state,severity) VALUES ('pping','eventEngine',9956,829,'boxState','e',100);
COMMIT;

BEGIN;
INSERT INTO eventq (source,target,deviceid,netboxid,eventtypeid,state,severity) VALUES ('pping','eventEngine',1643,627,'boxState','s',100);
INSERT INTO eventq (source,target,deviceid,netboxid,eventtypeid,state,severity) VALUES ('pping','eventEngine',9953,827,'boxState','s',100);
INSERT INTO eventq (source,target,deviceid,netboxid,eventtypeid,state,severity) VALUES ('pping','eventEngine',9956,829,'boxState','s',100);
COMMIT;

BEGIN;
INSERT INTO eventq (source,target,deviceid,netboxid,eventtypeid,state,severity) VALUES ('pping','eventEngine',348,347,'boxState','s',100);
INSERT INTO eventq (source,target,deviceid,netboxid,eventtypeid,state,severity) VALUES ('pping','eventEngine',48977,1912,'boxState','s',100);
COMMIT;

BEGIN;
INSERT INTO eventq (source,target,deviceid,netboxid,eventtypeid,state,severity) VALUES ('pping','eventEngine',348,347,'boxState','e',100);
INSERT INTO eventq (source,target,deviceid,netboxid,eventtypeid,state,severity) VALUES ('pping','eventEngine',48977,1912,'boxState','e',100);
COMMIT;




BEGIN;
INSERT INTO eventq (source,target,deviceid,boksid,eventtypeid,state,severity) VALUES ('pping','eventEngine',1,1,'boxState','t',100);
INSERT INTO eventqvar (eventqid,var,val) VALUES ((SELECT eventq_eventqid_seq.last_value),'pl','100');
COMMIT;

BEGIN;
INSERT INTO eventq (source,target,deviceid,boksid,eventtypeid,state,severity) VALUES ('pping','eventEngine',1,1,'boxState','f',100);
COMMIT;

- tekno-sw is going down...

BEGIN;
INSERT INTO eventq (source,target,deviceid,netboxid,eventtypeid,state,severity) VALUES ('pping','eventEngine',534,533,'boxState','s',100);
COMMIT;

BEGIN;
INSERT INTO eventq (source,target,deviceid,netboxid,eventtypeid,state,severity) VALUES ('pping','eventEngine',534,533,'boxState','e',100);
COMMIT;

- mask-stud-368-h2 is going down...

BEGIN;
INSERT INTO eventq (source,target,deviceid,boksid,eventtypeid,state,severity) VALUES ('pping','eventEngine',1253,1253,'boxState','s',100);
COMMIT;

BEGIN;
INSERT INTO eventq (source,target,deviceid,boksid,eventtypeid,state,severity) VALUES ('pping','eventEngine',1253,1253,'boxState','e',100);
COMMIT;

- Prøv noe enkelt, voll-sby-980-h (238) står i skygge for voll-sw (237)

BEGIN;
INSERT INTO eventq (source,target,deviceid,boksid,eventtypeid,state,severity) VALUES ('pping','eventEngine',238,238,'boxState','s',100);
COMMIT;
BEGIN;
INSERT INTO eventq (source,target,deviceid,boksid,eventtypeid,state,severity) VALUES ('pping','eventEngine',237,237,'boxState','s',100);
COMMIT;

BEGIN;
INSERT INTO eventq (source,target,deviceid,boksid,eventtypeid,state,severity) VALUES ('pping','eventEngine',238,238,'boxState','e',100);
COMMIT;
BEGIN;
INSERT INTO eventq (source,target,deviceid,boksid,eventtypeid,state,severity) VALUES ('pping','eventEngine',237,237,'boxState','e',100);
COMMIT;



- sb-351-sw


- Hva gjøres i tilfellet der man har f.eks to like etterfølgende info-events, skal event engine ignorere den siste?
- Hva gjøres for tilstandsfulle events som aldri oppheves (f.eks en linkDown event der kabelen kobles over på annen port)?
- Skal transienter rapporteres, dvs. boxDown og boxUp i rask rekkefølge?
- Hvordan skal coldStart og warmStart behandles?
- linkState events går ikke til alertq/alerthist
- Dersom en boks går ned, skal moduleDown rapporteres til alertq, evt. med skygge?

---
Algoritmen for down|shadow sjekker ikke om en ruter er nåbar hvis alt er oppe, dvs.
har ikke topologiavlederen funnet all info så vil boksen alltid være i skygge uansett.
---

BEGIN;
INSERT INTO eventq (source,target,deviceid,boksid,eventtypeid,state,severity) VALUES ('pping','eventEngine',1,1,'info','t',100);
INSERT INTO eventqvar (eventqid,var,val) VALUES ((SELECT eventq_eventqid_seq.last_value),'pl','100');
COMMIT;

BEGIN;
INSERT INTO eventq (source,target,deviceid,boksid,eventtypeid,state,severity) VALUES ('pping','eventEngine',1,1,'info','f',100);
COMMIT;

BEGIN;
INSERT INTO eventq (source,target,deviceid,boksid,eventtypeid,state,severity) VALUES ('pping','eventEngine',1,1,'info','x',100);
INSERT INTO eventqvar (eventqid,var,val) VALUES ((SELECT eventq_eventqid_seq.last_value),'pl','100');
COMMIT;








*/

}



/*
DeviceDB:
	Device findBySysname(String s)
	Device findByDeviceid(int deviceid)

Device:
	down()
	up()
	isUp()

Box extends Device

Nettel extends Box
	linkDown(String mp)
	linkUp(String mp)
	warmStart()
	coldStart()

Gw extends Nettel
	cpuThresholdExceeded()
	memThresholdExceeded()

Sw extends Nettel
	backplaneThresholdExceeded()

Server extends Device
	serviceDown(String serviceid)
	serviceUp(String serviceid)

WWWServer extends Server
*/
