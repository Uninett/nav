import java.util.*;
import java.sql.ResultSet;
import java.sql.SQLException;

import no.ntnu.nav.Database.*;
import no.ntnu.nav.logger.*;
import no.ntnu.nav.eventengine.*;

/**
 * Implementation of DeviceDB interface.
 *
 */

class DeviceDBImpl implements DeviceDB
{
	private Timer timer;

	private HashMap deviceMap;
	private Set deviceidSet;
	private boolean updateMode;
	
	// Contains the down alerts from alert hist so we know can look the
	// start event up when the end alert arrives
	private Map downAlertMap = new HashMap();

	DeviceDBImpl(HashMap deviceMap, Timer timer, String alertmsgFile) throws java.text.ParseException
	{
		this.deviceMap = deviceMap;
		this.timer = timer;

		EventImpl.setAlertmsgFile(alertmsgFile);

		// Fetch all unclosed alerthist records
		try {
			ResultSet rs = Database.query("SELECT * FROM alerthist WHERE end_time='infinity'");
			while (rs.next()) {
				EventImpl e = eventImplFactory(rs, true);
				downAlertMap.put(e.getKey(), e);
				Log.d("DEVICEDB_IMPL", "CONSTRUCTOR", "Added to downAlertMap: " + e);
			}
		} catch (SQLException e) {
			Log.e("DeviceDBImpl", "CONSTRUCTOR", "Unable to read alerthist: " + e.getMessage());
			e.printStackTrace(System.err);
		}
	}

	static Event eventFactory(ResultSet rs) throws SQLException
	{
		return eventImplFactory(rs, false);
	}

	private static EventImpl eventImplFactory(ResultSet rs, boolean history) throws SQLException
	{
		String table = history?"alerthist":"eventq";
		String tableid = table+"id";

		// Get fields
		String id = rs.getString(tableid);
		String source = rs.getString("source");
		int deviceid = rs.getInt("deviceid");
		int boxid = rs.getInt("netboxid");
		int subid = rs.getInt("subid");
		String time = rs.getString(history?"start_time":"time");
		String eventtypeid = rs.getString("eventtypeid");
		char state = history ? 's' : rs.getString("state").charAt(0);
		int value = rs.getInt("value");
		int severity = rs.getInt("severity");
		Map varMap = new HashMap();

		if (!history && rs.getString("var") != null) {
			// Get any variables the event may have
			do {
				varMap.put(rs.getString("var"), rs.getString("val"));
				
			} while (rs.next() && rs.getString(tableid).equals(id));
			rs.previous();
		}

		EventImpl e = new EventImpl(id, source, deviceid, boxid, subid, time, eventtypeid, state, value, severity, varMap);
		return e;
	}

	public static boolean isDisposed(Event e)
	{
		return ((EventImpl)e).isDisposed();
	}

	public Device getDevice(int deviceid)
	{
		return (Device)deviceMap.get(new Integer(deviceid));
	}

	public void putDevice(Device d)
	{
		if (!updateMode) return;
		deviceMap.put(d.getDeviceidI(), d);
		touchDevice(d);
	}
	public void touchDevice(Device d) {
		if (!updateMode) return;
		deviceidSet.remove(d.getDeviceidI());
	}
	public boolean isTouchedDevice(Device d) {
		if (!updateMode) return false;
		return deviceMap.containsKey(d.getDeviceidI()) && !deviceidSet.contains(d.getDeviceidI());
	}

	public void startDBUpdate() {
		deviceidSet = ((HashMap)deviceMap.clone()).keySet();
		updateMode = true;
	}

	public void endDBUpdate()
	{
		if (!updateMode) return;
		Log.d("DEVICEDB_IMPL", "END_DB_UPDATE", "devDB size: " + deviceMap.size());
		Log.d("DEVICEDB_IMPL", "END_DB_UPDATE", "Clone size: " + deviceidSet.size());
		updateMode = false;
	}

	// Doc in interface
	public Alert getDownAlert(Event e)
	{
		if (e.getState() == Event.STATE_END && e instanceof EventImpl) {
			return (Alert)downAlertMap.get(getDownAlertKey(e));
		}
		return null;
	}

	private void removeDownAlert(Event e)
	{
		if (e.getState() == Event.STATE_END && e instanceof EventImpl) {
			downAlertMap.remove(getDownAlertKey(e));
		}
	}

	private String getDownAlertKey(Event e)
	{
		EventImpl ei = (EventImpl)e;
		ei.setState(Event.STATE_START);
		String key = e.getKey();
		ei.setState(Event.STATE_END);
		return key;
	}

	// Doc in interface
	public Alert alertFactory(Event e)
	{
		return alertFactory(e, null);
	}

	// Doc in interface
	public Alert alertFactory(Event e, String alerttype)
	{
		EventImpl ei;
		if (e == null) ei = new EventImpl();
		else ei = new EventImpl((EventImpl)e);
		if (alerttype != null) ei.setAlerttype(alerttype);
		return ei;
	}
	
	// Doc in interface
	public void postAlert(Alert a) throws PostAlertException
	{
		EventImpl e = (EventImpl)a;
		
		Log.d("DEV_DB", "POSTALERT", "Posting alert: " + e);

		// Post the alert to alertq
		try {
			Database.beginTransaction();

			// Insert into alertq
			if (e.getPostAlertq()) {
				insertAlert(e, false, null);
			}

			// Update alertqhist
			boolean removeDownAlert = false;
			boolean noDownAlertExp = false;
			if (e.getState() != Event.STATE_END) {
				// Insert into alerthist
				String id = insertAlert(e, true, null);

				if (e.getState() == Event.STATE_START) {
					e.setEventqid(id);
					downAlertMap.put(e.getKey(), e);
				}
			} else {
				// End event, set end time for previous (start) alert
				EventImpl da = (EventImpl)getDownAlert(e);
				if (da == null) {
					noDownAlertExp = true;
				} else {
					String alerthistid = da.getEventqid();
					Database.update("UPDATE alerthist SET end_time = '"+e.getTimeSql()+"' WHERE alerthistid = "+alerthistid);
					removeDownAlert = true;

					// Insert into alerthistmsg
					insertAlert(e, true, alerthistid);
				}
			}

			// Now delete releated events from eventq
			StringBuffer sb = new StringBuffer();
			for (Iterator i=e.getEventList().iterator(); i.hasNext();) {
				EventImpl de = (EventImpl)i.next();
				sb.append(",'"+de.getEventqid()+"'");
			}
			Log.d("DEV_DB", "POSTALERT", "Removing events from eventq: " + sb);
			if (sb.length() > 0) {
				sb.deleteCharAt(0);
				Database.update("DELETE FROM eventq WHERE eventqid IN ("+sb+")");
			}

			// Everything went well, so it is safe to commit
			Database.commit();

			if (noDownAlertExp) {
				throw new PostAlertException("DeviceDB.postAlert: DownAlert not found!");
			}

			if (removeDownAlert) removeDownAlert(e);

		} catch (SQLException exp) {
			Log.d("DEV_DB", "POSTALERT", "SQLException while posting alert: " + exp);
			exp.printStackTrace(System.err);
			Database.rollback();
			throw new PostAlertException("Got SQLException: " + exp.getMessage());
		} catch (PostAlertException exp) {
			Log.d("DEV_DB", "POSTALERT", "PostAlertException while posting alert: " + exp);
			exp.printStackTrace(System.err);
			Database.rollback();
			throw exp;
		}

	}

	private String insertAlert(EventImpl e, boolean history, String alerthistid) throws SQLException, PostAlertException
	{
		String table = history?"alerthist":"alertq";
		String tableid = table+"id";
		String tablemsg = table+"msg";
		//String tableseq = table+"_"+table+"id_seq";

		/*
		// First get an id
		ResultSet rs = Database.query("SELECT nextval('"+tableseq+"')");
		if (!rs.next()) throw new PostAlertException("Error, could not get id from seq " + tableseq);
		int id = rs.getInt("nextval");
		*/
		String id;

		// Don't insert into alerthist of this is an end-alert
		if (alerthistid == null) {
			String[] ins;
			if (!history) {
				String[] s = {
					tableid, "",
					"source", e.getSourceSql(),
					"deviceid", e.getDeviceidSql(),
					"netboxid", e.getNetboxidSql(),
					"subid", e.getSubidSql(),
					"time", e.getTimeSql(),
					"eventtypeid", e.getEventtypeidSql(),
					"state", e.getStateSql(),
					"value", e.getValueSql(),
					"severity", e.getSeveritySql()
				};
				ins = s;
			} else {
				String[] s = {
					tableid, "",
					"source", e.getSourceSql(),
					"deviceid", e.getDeviceidSql(),
					"netboxid", e.getNetboxidSql(),
					"subid", e.getSubidSql(),
					"start_time", e.getTimeSql(),
					"end_time", (e.getState() == Event.STATE_NONE ? "null" : "infinity"),
					"eventtypeid", e.getEventtypeidSql(),
					"value", e.getValueSql(),
					"severity", e.getSeveritySql()
				};
				ins = s;
			}
			id = Database.insert(table, ins, null);
		} else {
			id = alerthistid;
		}

		// Insert messages
		for (Iterator it = e.getMsgs(); it.hasNext();) {
			String[] s = (String[])it.next();
			String media = s[0];
			String lang = s[1];
			String msg = s[2];

			String[] insv;
			if (!history) {
				String[] v = {
					tableid, id,
					"msgtype", media,
					"language", lang,
					"msg", msg
				};
				insv = v;
			} else {
				String[] v = {
					tableid, id,
					"state", e.getStateSql(),
					"msgtype", media,
					"language", lang,
					"msg", msg
				};
				insv = v;
			}
			Database.insert(tablemsg, insv);
		}

		// Additionally, if we are posting to alerthist, insert any historyVars into alerthistvar
		if (history) {
			for (Iterator it = e.historyVarIterator(); it.hasNext();) {
				Map.Entry me = (Map.Entry)it.next();

				String[] ins = {
					tableid, id,
					"state", e.getStateSql(),
					"var", (String)me.getKey(),
					"val", (String)me.getValue()
				};
				Database.insert("alerthistvar", ins);
			}
		}

		return id;
	}

	private Map callbackMap = new IdentityHashMap();

	// Doc in interface
	public void scheduleCallback(EventCallback ec, long delay)
	{
		scheduleCallback(ec, delay, 1);
	}

	// Doc in interface
	public void scheduleCallback(EventCallback ec, long delay, int invocationCount)
	{
		CallbackTask ct;
		if ( (ct=(CallbackTask)callbackMap.remove(ec)) != null) ct.cancel();

		if (invocationCount > 0) {
			ct = new CallbackTask(ec, invocationCount);
			callbackMap.put(ec, ct);
			timer.scheduleAtFixedRate(ct, delay, delay);
		}
	}

	// Doc in interface
	public boolean isScheduledCallback(EventCallback ec)
	{
		return callbackMap.containsKey(ec);
	}

	// Doc in interface
	public boolean cancelCallback(EventCallback ec)
	{
		CallbackTask ct;
		if ( (ct=(CallbackTask)callbackMap.remove(ec)) != null) ct.cancel();
		return ct != null;
	}

	private class CallbackTask extends TimerTask
	{
		EventCallback ec;
		int count;

		public CallbackTask(EventCallback ec, int count)
		{
			this.ec = ec;
			this.count = count;
		}

		public void run()
		{
			if (--count == 0) {
				callbackMap.remove(ec);
				cancel();
			}
			ec.callback(DeviceDBImpl.this, count);
		}
	}

}
