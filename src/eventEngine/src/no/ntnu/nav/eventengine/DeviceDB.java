package no.ntnu.nav.eventengine;

import no.ntnu.nav.Database.*;

import java.util.*;
import java.sql.ResultSet;
import java.sql.SQLException;

public class DeviceDB
{
	private Timer timer;

	private HashMap deviceMap;
	private Set deviceidSet;
	private boolean updateMode;

	/**
	 *
	 */
	private Map downAlertMap = new HashMap();

	public DeviceDB(HashMap deviceMap, Timer timer)
	{
		this.deviceMap = deviceMap;
		this.timer = timer;

		// Fetch all unclosed alerthist records
		try {
			ResultSet rs = Database.query("SELECT * FROM alerthist NATURAL LEFT JOIN alerthistvar WHERE end_t='infinity'");
			while (rs.next()) {
				EventImpl e = eventImplFactory(rs, true);
				downAlertMap.put(e.getKey(), e);
				outld("DeviceDB: downAlertMap: " + e);
			}
		} catch (SQLException e) {
			System.err.println("DeviceDB.DeviceDB: Unable to read alerthist: " + e.getMessage());
		}
	}

	public static Event eventFactory(ResultSet rs) throws SQLException
	{
		return eventImplFactory(rs, false);
	}

	private static EventImpl eventImplFactory(ResultSet rs, boolean history) throws SQLException
	{
		String table = history?"alerthist":"eventq";
		String tableid = table+"id";
		String tablevar = table+"var";

		// Get fields
		int id = rs.getInt(tableid);
		String source = rs.getString("source");
		int deviceid = rs.getInt("deviceid");
		int boksid = rs.getInt("boksid");
		int subid = rs.getInt("subid");
		String time = rs.getString(history?"start_t":"time");
		String eventtypeid = rs.getString("eventtypeid");
		char state = history ? 's' : rs.getString("state").charAt(0);
		int value = rs.getInt("value");
		int severity = rs.getInt("severity");
		Map varMap = new HashMap();

		String var = rs.getString("var");
		if (var != null) {
			do {

				List l;
				if ( (l=(List)varMap.get(var)) == null) varMap.put(var, l=new ArrayList());
				l.add(rs.getString("val"));

			} while (rs.next() && rs.getInt(tableid) == id);
			rs.previous();
		}

		EventImpl e = new EventImpl(id, source, deviceid, boksid, subid, time, eventtypeid, state, value, severity, varMap);
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
		outld("devDB size: " + deviceMap.size());
		outld("Clone size: " + deviceidSet.size());
		updateMode = false;
	}

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


	public Alert alertFactory(Event e)
	{
		if (e == null) return new EventImpl();
		return new EventImpl((EventImpl)e);
	}

	/**
	 * Post and commit the given alert to the alertq, then delete
	 * the associated Events.
	 *
	 * If the state for this Alert is 'down', it will be added to the
	 * down alert list.
	 */
	public void postAlert(Alert a) throws PostAlertException
	{
		EventImpl e = (EventImpl)a;
		// Post the alert to alertq
		try {
			insertAlert(e, false);

			// Update alertqhist
			boolean removeDownAlert = false;
			if (e.getState() != Event.STATE_END) {
				// Insert new record
				int id = insertAlert(e, true);

				if (e.getState() == Event.STATE_START) {
					e.setEventqid(id);
					downAlertMap.put(e.getKey(), e);
				}
			} else {
				// End event, set end time for previous (start) alert
				EventImpl da = (EventImpl)getDownAlert(e);
				if (da == null) throw new PostAlertException("DeviceDB.postAlert: DownAlert not found!");
				int alerthistid = da.getEventqid();
				Database.update("UPDATE alerthist SET end_t = '"+e.getTimeSql()+"' WHERE alerthistid = "+alerthistid);
				removeDownAlert = true;
			}

			// Now delete releated events from eventq
			StringBuffer sb = new StringBuffer();
			for (Iterator i=e.getEventList().iterator(); i.hasNext();) {
				EventImpl de = (EventImpl)i.next();
				sb.append(",'"+de.getEventqid()+"'");
			}
			if (sb.length() > 0) {
				sb.deleteCharAt(0);
				Database.update("DELETE FROM eventq WHERE eventqid IN ("+sb+")");
			}

			// Everything went well, so it is safe to commit
			Database.commit();

			if (removeDownAlert) removeDownAlert(e);

		} catch (SQLException exp) {
			exp.printStackTrace(System.err);
			Database.rollback();
			throw new PostAlertException("Got SQLException: " + exp.getMessage());
		} catch (PostAlertException exp) {
			exp.printStackTrace(System.err);
			Database.rollback();
			throw exp;
		}

	}
	private int insertAlert(EventImpl e, boolean history) throws SQLException, PostAlertException
	{
		String table = history?"alerthist":"alertq";
		String tableid = table+"id";
		String tablevar = table+"var";
		String tableseq = table+"_"+table+"id_seq";

		// First get an id
		ResultSet rs = Database.query("SELECT nextval('"+tableseq+"')");
		if (!rs.next()) throw new PostAlertException("Error, could not get id from seq " + tableseq);
		int id = rs.getInt("nextval");

		String[] ins;
		if (!history) {
			String[] s = {
				tableid, String.valueOf(id),
				"source", e.getSourceSql(),
				"deviceid", e.getDeviceidSql(),
				"boksid", e.getBoksidSql(),
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
				tableid, String.valueOf(id),
				"source", e.getSourceSql(),
				"deviceid", e.getDeviceidSql(),
				"boksid", e.getBoksidSql(),
				"subid", e.getSubidSql(),
				"start_t", e.getTimeSql(),
				"end_t", (e.getState() == Event.STATE_NONE ? "null" : "infinity"),
				"eventtypeid", e.getEventtypeidSql(),
				"value", e.getValueSql(),
				"severity", e.getSeveritySql()
			};
			ins = s;
		}
		Database.insert(table, ins);

		Iterator i = e.getVarMap().entrySet().iterator();
		if (i.hasNext()) {
			while (i.hasNext()) {
				Map.Entry me = (Map.Entry)i.next();
				String var = (String)me.getKey();
				List l = (List)me.getValue();
				for (int j=0; j<l.size(); j++) {
					String val = (String)l.get(j);
					String[] insv = {
						tableid, String.valueOf(id),
						"var", var,
						"val", val
					};
					Database.insert(tablevar, insv);
				}
			}
		}
		return id;
	}

	private Map callbackMap = new IdentityHashMap();
	public void scheduleCallback(EventCallback ec, long delay)
	{
		scheduleCallback(ec, delay, 1);
	}
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
	public boolean isScheduledCallback(EventCallback ec)
	{
		return callbackMap.containsKey(ec);
	}
	// Return true if a callback was canceled
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
			ec.callback(DeviceDB.this, count);
		}
	}



	private static void outd(Object o) { System.out.print(o); }
	private static void outld(Object o) { System.out.println(o); }

	private static void err(Object o) { System.err.print(o); }
	private static void errl(Object o) { System.err.println(o); }
}