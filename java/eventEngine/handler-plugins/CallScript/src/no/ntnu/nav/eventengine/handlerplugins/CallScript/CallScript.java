package no.ntnu.nav.eventengine.handlerplugins.CallScript;

import java.util.*;
import java.io.*;
import java.sql.*;

import no.ntnu.nav.Database.*;
import no.ntnu.nav.ConfigParser.*;
import no.ntnu.nav.logger.*;

import no.ntnu.nav.eventengine.*;
import no.ntnu.nav.eventengine.deviceplugins.Box.*;
import no.ntnu.nav.eventengine.deviceplugins.Netel.*;

/**
 * CallScript handler plugin; calls an external script in response to an event.
 */

public class CallScript implements EventHandler
{

	public String[] handleEventTypes()
	{
		return HANDLE_ALL_EVENTS;
	}

	public void handle(DeviceDB ddb, Event e, ConfigParser cp)
	{
		ConfigParser navCp = (ConfigParser) cp.getObject("navCp");
		String eventtype = e.getEventtypeid();
		char sep = File.separatorChar;
		String script = navCp.get("NAVROOT") + sep + "bin" + sep + "eventengine" + sep + "scripts" + sep + eventtype;

		try {
			File f = new File(script);
			if (!f.exists()) {
				return;
			}
		} catch (Exception exp) {
			exp.printStackTrace(System.err);
		}

		Log.setDefaultSubsystem("CALL_SCRIPT_EVENTHANDLER");
		//Log.d("HANDLE", "Event: " + e);

		Map vars = new HashMap();

		vars.put("source", "" + e.getSource());
		vars.put("deviceid", "" + e.getDeviceid());
		vars.put("netboxid", "" + e.getNetboxid());
		vars.put("subid", "" + e.getSubid());
		vars.put("netboxid", "" + e.getNetboxid());
		vars.put("time", "" + e.getTime());
		vars.put("eventtypeid", "" + e.getEventtypeid());
		vars.put("state", "" + e.getState());
		vars.put("value", "" + e.getValue());
		vars.put("severity", "" + e.getSeverity());

		vars.putAll(e.getVarMap());

		try {
			if (e.getDeviceid() > 0) {
				ResultSet rs = Database.query("SELECT * FROM device LEFT JOIN netbox USING (deviceid) LEFT JOIN type USING (typeid) LEFT JOIN room USING (roomid) LEFT JOIN location USING (locationid) LEFT JOIN module USING(deviceid) WHERE deviceid = " + e.getDeviceid());
				ResultSetMetaData rsmd = rs.getMetaData();
				if (rs.next()) {
					HashMap hm = Database.getHashFromResultSet(rs, rsmd);
					vars.putAll(hm);
				}
			}
			if (e.getNetboxid() > 0) {
				ResultSet rs = Database.query("SELECT * FROM netbox JOIN device USING (deviceid) LEFT JOIN type USING (typeid) LEFT JOIN room USING (roomid) LEFT JOIN location USING (locationid) WHERE netboxid = " + e.getNetboxid());
				ResultSetMetaData rsmd = rs.getMetaData();
				if (rs.next()) {
					HashMap hm = Database.getHashFromResultSet(rs, rsmd);
					vars.putAll(hm);
				}
			}
		} catch (SQLException exp) {
			exp.printStackTrace(System.err);
		}

		long beginTime = System.currentTimeMillis();
		if (!execScript(script, vars)) {
			Log.e("EXEC_SCRIPT", "Failed to execute script: " + script);
		} else {
			Log.e("EXEC_SCRIPT", "Script " + script + " executed in " + (System.currentTimeMillis() - beginTime) + " ms");
		}
		
	}

	public boolean execScript(String script, Map vars)
	{
		try {
			List cmd = new ArrayList();
			cmd.add(script);
			for (Iterator it = vars.entrySet().iterator(); it.hasNext();) {
				Map.Entry me = (Map.Entry)it.next();
				cmd.add(me.getKey() + "=" + me.getValue());
			}

			String[] hostCmd = new String[cmd.size()];
			for (int i=0; i < cmd.size(); i++) {
				hostCmd[i] = (String) cmd.get(i);
			};

			Runtime rt = Runtime.getRuntime();
			//Log.d("EXEC_SCRIPT", "Exec: " + cmd);
			Process p = rt.exec(hostCmd);

			try {
				p.waitFor();
			} catch (InterruptedException e) {
				Log.e("EXEC_SCRIPT", "InterruptedException: " + e.getMessage());
				e.printStackTrace(System.err);
				return false;
			}

		} catch (Exception e) {
			Log.e("EXEC_SCRIPT", "Exception: " + e.getMessage());
			e.printStackTrace(System.err);
		}
		return true;
	}

}
