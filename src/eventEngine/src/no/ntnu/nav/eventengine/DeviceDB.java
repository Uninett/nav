package no.ntnu.nav.eventengine;

import no.ntnu.nav.Database.*;

import java.util.*;
import java.sql.ResultSet;
import java.sql.SQLException;

public class DeviceDB
{
	HashMap deviceMap = new HashMap();
	Set deviceidSet;
	boolean updateMode;

	/**
	 *
	 */
	Map downAlertMap = new HashMap();

	public DeviceDB()
	{

		// Fetch all unclosed alerthist records
		try {
			ResultSet rs = Database.query("SELECT * FROM alerthist LEFT NATURAL JOIN alerthistvar WHERE closed='f'");
			while (rs.next()) {
				EventImpl e = eventImplFactory(rs, true);
				downAlertMap.put(e.getKey(), e);
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
		char state = history ? 'x' : rs.getString("state").charAt(0);
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
		return (Alert)downAlertMap.get(e.getKey());
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
			insertAlert(e, false, false);

			// Update alertqhist
			System.err.println("Alert state: " + e.getState());
			if (e.getState() != Event.STATE_END) {
				// Insert new record
				int id = insertAlert(e, true, true);
				e.setEventqid(id);

				if (e.getState() == Event.STATE_START) {
					downAlertMap.put(e.getKey(), e);
				}
			} else {
				// End event, so set end time for previous alert
				e.setState(Event.STATE_START);
				EventImpl da = (EventImpl)getDownAlert(e);
				if (da == null) throw new PostAlertException("DeviceDB.postAlert: DownAlert not found!");
				int alerthistid = da.getEventqid();
				Database.update("UPDATE alerthist SET end_t = '"+da.getTimeSql()+"', closed = 't' WHERE alerthistid = "+alerthistid);
				//((System.err.println("debug: " + ("UPDATE alerthist SET end = '"+da.getTimeSql()+"' WHERE alerthistid = "+alerthistid));
				Database.commit();
			}
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
	private int insertAlert(EventImpl e, boolean history, boolean needId) throws SQLException, PostAlertException
	{
		String[] ins;
		if (!history) {
			String[] s = {
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
				"source", e.getSourceSql(),
				"deviceid", e.getDeviceidSql(),
				"boksid", e.getBoksidSql(),
				"subid", e.getSubidSql(),
				"start_t", e.getTimeSql(),
				"eventtypeid", e.getEventtypeidSql(),
				"closed", (e.getState() == Event.STATE_NONE ? "t" : "f"),
				"value", e.getValueSql(),
				"severity", e.getSeveritySql()
			};
			ins = s;
		}

		String table = history?"alerthist":"alertq";
		String tableid = table+"id";
		String tablevar = table+"var";

		Database.insert(table, ins);

		int id = -1;
		Iterator i = e.getVarMap().entrySet().iterator();
		if (i.hasNext() || needId) {
			// We need the alertqid value
			String ss = "SELECT "+tableid+" FROM "+table+" WHERE deviceid"+e.getDeviceidSqlE()+
										" AND boksid"+e.getBoksidSqlE()+" AND subid"+e.getSubidSqlE()+
										" AND eventtypeid='"+e.getEventtypeid()+"'"+(history?"":" AND state='"+e.getStateSql()+"'");
			ResultSet rs = Database.query("SELECT "+tableid+" FROM "+table+" WHERE deviceid"+e.getDeviceidSqlE()+
										" AND boksid"+e.getBoksidSqlE()+" AND subid"+e.getSubidSqlE()+
										" AND eventtypeid='"+e.getEventtypeid()+"'"+(history?"":" AND state='"+e.getStateSql()+"'"));
			if (!rs.next() || rs.getFetchSize() > 1) throw new PostAlertException(tableid+" not found or more than one ("+rs.getFetchSize()+") for tuple just inserted, should not happen"+ss);
			id = rs.getInt(tableid);
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
		Database.commit();
		return id;
	}


	private static void outd(Object o) { System.out.print(o); }
	private static void outld(Object o) { System.out.println(o); }

	private static void err(Object o) { System.err.print(o); }
	private static void errl(Object o) { System.err.println(o); }
}