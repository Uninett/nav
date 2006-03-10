/*
 * Event
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

package no.ntnu.nav.event;

import java.util.*;
import java.text.*;
import java.sql.ResultSet;
import java.sql.SQLException;

import no.ntnu.nav.Database.*;
import no.ntnu.nav.logger.*;

/**
 * An Event; contains all data about the event.
 *
 * @version $LastChangedRevision$ $LastChangedDate$
 * @author Kristian Eide &lt;kreide@online.no&gt;
 */

public class Event
{
	/**
	 * A stateless event, which is not assosiated with any other events.
	 */
	public static final int STATE_NONE = 0;

	/**
	 * The start-event of a stateful event. Start-events needs to be followed by
	 * an end-event.
	 */
	public static final int STATE_START = 10;

	/**
	 * The end-event of a stateful event. Cancels the state set by the
	 * start-event. Note that the "key" (see {@link #getKey getKey}
	 * below) of the end-event must be equal to that of the start-event
	 * except for the state.
	 *
	 * @see #getKey
	 */
	public static final int STATE_END = 20;

	// Event
	public String getSource() { return source; }
	public String getTarget() { return target; }
	public int getDeviceid() { return deviceid; }
	public Integer getDeviceidI() { return new Integer(deviceid); }
	public int getNetboxid() { return netboxid; }
	public int getSubid() { return subid; }
	public Date getTime() { return time; }
	public String getTimeS() { return dateToString(time); }
	public String getEventtypeid() { return eventtypeid; }
	public int getState() { return state; }
	public int getValue() { return value; }
	public int getSeverity() { return severity; }

	/**
	 * Get the value assosiated with the given variable. The variables
	 * are those posted to eventqvar togheter with the event.
	 *
	 * @return the value assosiated with the given key
	 */
	public String getVar(String var) { return (String)varMap.get(var); }

	/**
	 * Returns an iterator over all variables in this Event. Each element is a {@link java.util.Map.Entry Map.Entry} object.
	 *
	 * @return iterator over all variables in this Event
	 */
	public Iterator getVarIterator() { return varMap.entrySet().iterator(); }

	/**
	 * <p> Get the key which identifies this Event. It is composed of:
	 * </p>
	 *
	 * <p>
	 * <ul>
	 *  <li>deviceid</li>
	 *  <li>netboxid</li>
	 *  <li>sbuid</li>
	 *  <li>eventtypeid</li>
	 *  <li>state</li>
	 * </ul>
	 * </p>
	 *
	 * <p> These fields are required to uniquely identify the Event; if
	 * a second Event arrives with these fields equal to any previous
	 * Event not yet processed and posted to the alertq it should be
	 * consitered a duplicate by eventengine plugins.  </p>
	 *
	 * @return the key which uniquely identifies this Event
	 */
	public String getKey()
	{
		StringBuffer sb = new StringBuffer();
		if (deviceid > 0) sb.append(deviceid+":");
		if (netboxid > 0) sb.append(netboxid+":");
		if (subid > 0) sb.append(subid+":");
		sb.append(eventtypeid+":");
		sb.append(state);
		return sb.toString();
	}

	/**
	 * <p> Dispose of the event. Normally this happens automatically
	 * when an alert created from this event is posted, but in the case
	 * no alert is to be posted this method can be used.  </p>
	 *
	 * <p> <b>Note:</b> Events not disposed of, either automatically or
	 * through this method will <b>not</b> be deleted from the eventq.
	 * </p>
	 */
	public void dispose()
	{
		if (disposed) return;
		try {
			Database.update("DELETE FROM eventq WHERE eventqid = '"+eventqid+"'");
		} catch (SQLException e) {
			Log.e("EVENT", "DISPOSE", "Cannot dispose of self: " + e.getMessage());
			return;
		}
		disposed = true;
	}

	public static Event eventFactory(ResultSet rs) throws SQLException
	{
		String tableid = "eventqid";

		// Get fields
		String id = rs.getString(tableid);
		String source = rs.getString("source");
		String target = rs.getString("target");
		int deviceid = rs.getInt("deviceid");
		int netboxid = rs.getInt("netboxid");
		int subid = rs.getInt("subid");
		String time = rs.getString("time");
		String eventtypeid = rs.getString("eventtypeid");
		int state = charToState(rs.getString("state").charAt(0));
		int value = rs.getInt("value");
		int severity = rs.getInt("severity");
		Map varMap = new HashMap();

		if (rs.getString("var") != null) {
			// Get any variables the event may have
			do {
				varMap.put(rs.getString("var"), rs.getString("val"));
				
			} while (rs.next() && rs.getString(tableid).equals(id));
			rs.previous();
		}

		Event e = new Event(id, source, target, deviceid, netboxid, subid, time, eventtypeid, state, value, severity, varMap);
		return e;
	}

	public String toString() {
		String s = "eventqid="+eventqid+" deviceid="+deviceid+" netboxid="+netboxid+" time=[] eventtypeid="+eventtypeid+" state="+getStateSql()+" varMap="+varMap;
		return s;
	}

	// Package
	Event(String eventqid, String source, String target, int deviceid, int netboxid, int subid, String time, String eventtypeid, int state, int value, int severity, Map varMap)
	{
		this.eventqid = eventqid;
		this.source = source;
		this.target = target;
		this.deviceid = deviceid;
		this.netboxid = netboxid;
		this.subid = subid;

		if (time != null) {
			try {
				this.time = stringToDate(time);
			} catch (ParseException e) {
				Log.c("EVENT", "CONSTRUCTOR", "Error in date '" + time + "' from Postgres, should not happen: " + e.getMessage());
			}
		}

		this.eventtypeid = eventtypeid;
		this.state = state;
		this.value = value;
		this.severity = severity;
		this.varMap = (varMap == null ? new HashMap() : varMap);
	}

	String getSourceSql() { return source; }
	String getTargetSql() { return target; }
	String getDeviceidSql() { return deviceid > 0 ? String.valueOf(deviceid) : null; }
	String getNetboxidSql() { return netboxid > 0 ? String.valueOf(netboxid) : null; }
	String getSubidSql() { return subid > 0 ? String.valueOf(subid) : null; }
	String getTimeSql() { return dateToString(time); }
	String getEventtypeidSql() { return eventtypeid; }
	String getStateSql() { return String.valueOf(stateToChar(state)); }
	String getValueSql() { return value >= 0 ? String.valueOf(value) : null; }
	String getSeveritySql() { return severity >= 0 ? String.valueOf(severity) : null; }

	// Private
	private String eventqid;
	private String source;
	private String target;
	private int deviceid;
	private int netboxid;
	private int subid;
	private Date time;
	private String eventtypeid;
	private int state;
	private int value;
	private int severity;
	private Map varMap;
	private Map historyVarMap = new HashMap();

	private String alerttype;

	private List eventList = new ArrayList();

	private boolean disposed;

	private static Date stringToDate(String d) throws ParseException {
		SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
		return sdf.parse(d);
	}
	private static String dateToString(Date d) {
		SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
		return sdf.format(d);
	}

	private static int charToState(char state) {
		switch (state) {
			case 'x': return STATE_NONE;
			case 's': return STATE_START;
			case 'e': return STATE_END;
		}
		return STATE_NONE;
	}
	private static char stateToChar(int state) {
		switch (state) {
			case STATE_NONE: return 'x';
			case STATE_START: return 's';
			case STATE_END: return 'e';
		}
		return 'x';
	}




}
