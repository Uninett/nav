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

/**
 * Loads plugins from disk.
 */

class PluginMonitorTask extends TimerTask
{
	DynamicURLClassLoader cl = new DynamicURLClassLoader();
	
	File dataDir, deviceDir;
	Map dataClassMap, deviceClassMap;

	Map dataFileMap = new HashMap();
	Map deviceFileMap = new HashMap();

	public PluginMonitorTask(String dataPath, Map dataClassMap, String devicePath, Map deviceClassMap)
	{
		dataDir = new File(dataPath);
		deviceDir = new File(devicePath);
		this.dataClassMap = dataClassMap;
		this.deviceClassMap = deviceClassMap;
	}

	public void run()
	{
		// Update data plugins
		update(dataDir, dataFileMap, dataClassMap, dataDir.listFiles() );

		// Update device plugins
		update(deviceDir, deviceFileMap, deviceClassMap, dataDir.listFiles() );

	}

	private boolean update(File pluginDir, Map fileMap, Map classMap, File[] dependFiles)
	{
		Log.setDefaultSubsystem("PLUGIN_MONITOR");

		// The cloneMap is used to remove plugins whose .jar file is deleted
		Map cloneMap;
		synchronized (classMap) {
			cloneMap = (Map) ((HashMap)classMap).clone();
		}

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
					Log.d("UPDATE", "New or modified jar, trying to load " + fileList[i].getName());

					if (cn == null) {
						Log.w("UPDATE", "Jar is missing Plugin-Class manifest, skipping...");
						continue;
					}

					Class c, dataInterface, deviceInterface;
					try {
						dataInterface = Class.forName("no.ntnu.nav.getDeviceData.dataplugins.DataHandler");
						deviceInterface = Class.forName("no.ntnu.nav.getDeviceData.deviceplugins.DeviceHandler");

						c = cl.loadClass(cn);
					} catch (ClassNotFoundException e) {
						Log.w("UPDATE", "Class " + cn + " not found in jar " + fileList[i].getName() + ", msg: " + e.getMessage());
						continue;
					} catch (NoClassDefFoundError e) {
						Log.w("UPDATE", "NoClassDefFoundError when loading class " + cn + " from jar " + fileList[i].getName() + ", msg: " + e.getMessage());
						continue;
					}

					if (dataInterface.isAssignableFrom(c) || deviceInterface.isAssignableFrom(c)) {
						// Found new Device, add to list
						synchronized (classMap) {
							classMap.put(fileList[i].getName(), c);
						}
						hasChanged = true;
						Log.d("UPDATE", "Plugin " + fileList[i].getName() + " loaded and added to classMap");
					} else {
						Log.w("UPDATE", "Failed to load plugin! Class " + cn + " is not a gDD plugin");
						Log.d("UPDATE", "Class failed to load is: " + c);						
					}
				}
			} catch (IOException e) {
				Log.w("UPDATE", "IOException when loading jar " + fileList[i].getName() + ", msg: " + e.getMessage());
			}
		}

		Iterator i = cloneMap.keySet().iterator();
		while (i.hasNext()) {
			String fn = (String)i.next();
			Log.d("UPDATE", "Removing jar " + fn + " from classMap");
			synchronized (classMap) {
				classMap.remove(fn);
			}
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












