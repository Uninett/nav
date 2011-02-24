/*
 * EventQ
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

import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.HashMap;
import java.util.IdentityHashMap;
import java.util.Iterator;
import java.util.Map;
import java.util.Timer;
import java.util.TimerTask;

import no.ntnu.nav.Database.Database;
import no.ntnu.nav.logger.Log;

/**
 * <p> Class for working with the event queue. </p>
 *
 * @version $LastChangedRevision$ $LastChangedDate$
 * @author Kristian Eide &lt;kreide@online.no&gt;
 */

public class EventQ {
	private static Timer timer;
	private static EventQMonitorTask emt;
	private static Map listenerMap = new HashMap();

	private EventQ() {
	}

	/**
	 * <p> Init the EventQ monitor thread. You must call init() before
	 * any events will be processed.  </p>
	 *
	 * <p> The monitor thread will be a demon thread, e.g. it will not
	 * stop the application from exiting if all other non-deamon threads
	 * are finished.  </p>
	 *
	 * @param checkFrequency The eventq check frequency, in milliseconds.
	 */
	public static void init(int checkFrequency) {
		init(checkFrequency, true);
	}

	/**
	 * <p> Init the EventQ monitor thread. You must call init() before
	 * any events will be processed.  </p>
	 *
	 * <p> If the deamon paramter is true the monitor thread will be a
	 * demon thread, e.g. it will not stop the application from exiting
	 * if all other non-deamon threads are finished.  </p>
	 *
	 * @param checkFrequency The eventq check frequency, in milliseconds.
	 * @param deamon Set if the monitor thread should be a deamon thread or not
	 */
	public static void init(int checkFrequency, boolean deamon) {
		if (checkFrequency < 100) throw new RuntimeException("checkFrequency < 100 ms not supported!");
		if (emt != null) emt.cancel();
		if (timer != null) timer.cancel();

		timer = new Timer(deamon);
		emt = new EventQMonitorTask(listenerMap, emt);
		timer.schedule(emt, 0, checkFrequency);
	}

	/**
	 * Add an EventQListener which will receive events from the eventq;
	 * there is no filtering on source.
	 *
	 * @param target The target the EventQListener should process events for
	 * @param eql The object which should receive the events
	 */
	public static void addEventQListener(String target, EventQListener eql) {
		addEventQListener(null, target, eql);
	}

	/**
	 * Add an EventQListener which will receive events from the eventq.
	 *
	 * @param source The source the EventQListener should process events for
	 * @param target The target the EventQListener should process events for
	 * @param eql The object which should receive the events
	 */
	public static void addEventQListener(String source, String target, EventQListener eql) {
		synchronized (listenerMap) {
			IdentityHashMap m;
			if ( (m=(IdentityHashMap)listenerMap.get(target)) == null) listenerMap.put(target, m = new IdentityHashMap());
			m.put(eql, source);
			if (emt != null) emt.updateTargets();
		}
	}

	/**
	 * <p>
	 * Convenience method. Same as calling:
	 * </p>
	 *
	 * <code>
	 * postEvent(eventFactory(...))
	 * </code>
	 */
	public static boolean createAndPostEvent(String source, String target, int deviceid, int netboxid, int subid, String eventtypeid, int state, int value, int severity, Map varMap) {
		return postEvent(eventFactory(source, target, deviceid, netboxid, subid, eventtypeid, state, value, severity, varMap));
	}

	/**
	 * <p> Create a new Event ready for posting to the eventq.  </p>
	 *
	 * <p> If any of deviceid, netboxid or subid are &lt;= 0 default
	 * (null) values will be used for the eventq. If any of value and
	 * severity are &lt; 0 default values will be used.  </p>
	 *
	 * @param varMap variable/value mappings; use null for no mappings
	 * @return the Event
	 */
	public static Event eventFactory(String source, String target, int deviceid, int netboxid, int subid, String eventtypeid, int state, int value, int severity, Map varMap) {
		return new Event(null, source, target, deviceid, netboxid, subid, null, eventtypeid, state, value, severity, varMap);
	}

	/**
	 * Post the given Event to the eventq.
	 *
	 * @return true if the event was sucessfully posted to the eventq; false otherwise
	 */
	public static boolean postEvent(Event e) {
		try {
			Database.beginTransaction();

			String[] ins = {
				"eventqid", "",
				"source", e.getSourceSql(),
				"target", e.getTargetSql(),
				"deviceid", e.getDeviceidSql(),
				"netboxid", e.getNetboxidSql(),
				"subid", e.getSubidSql(),
				"eventtypeid", e.getEventtypeidSql(),
				"state", e.getStateSql(),
				"value", e.getValueSql(),
				"severity", e.getSeveritySql()
			};
			String eventqid = Database.insert("eventq", ins, null);

			// Insert any variables
			for (Iterator it = e.getVarIterator(); it.hasNext();) {
				Map.Entry me = (Map.Entry)it.next();
				String var = (String)me.getKey();
				String val = (String)me.getValue();
				if (var == null || "null".equals(var)) {
					Log.w("EVENTQ", "POST_EVENT", "Cannot insert null var into eventqvar");
					continue;
				}
				if (val == null || "null".equals(val)) {
					Log.d("EVENTQ", "POST_EVENT", "Inserting null val into eventqvar [" + var + "]");
					val = "(null)";
				}
				String[] insv = {
					"eventqid", eventqid,
					"var", var,
					"val", val
				};
				Database.insert("eventqvar", insv);
			}
			Database.commit();
			Log.d("EVENTQ", "POST_EVENT", "Posted event from " + e.getSourceSql() + " to " + e.getTargetSql() + " (" + e.getEventtypeidSql() + ", " + e.getDeviceidSql() + ") on eventq");
			return true;

		} catch (SQLException exp) {
			Log.e("EVENTQ", "POST_EVENT", "SQLException when posting to eventq: " + exp.getMessage());
			try {
				Database.rollback();
			} catch (SQLException expr) {
				Log.e("EVENTQ", "POST_EVENT", "SQLException when rolling back: " + expr.getMessage());
			}
			exp.printStackTrace(System.err);
		}
		return false;
	}


}

class EventQMonitorTask extends TimerTask {
	private Map listenerMap;
	private EventQMonitorTask prevEmt;
	private long lastEventqid;
	private String targets;

	EventQMonitorTask(Map listenerMap, EventQMonitorTask prevEmt) {
		this.listenerMap = listenerMap;
		this.prevEmt = prevEmt;
		updateTargets();
	}

	private long getLastEventqid() {
		return lastEventqid;
	}

	public void updateTargets() {
		StringBuffer sb = new StringBuffer();
		synchronized (listenerMap) {
			if (listenerMap.isEmpty()) {
				targets = null;
				return;
			}
			for (Iterator it = listenerMap.keySet().iterator(); it.hasNext();) {
				String t = (String)it.next();
				sb.append("'" + Database.addSlashes(t) + "',");
			}
		}
		sb.deleteCharAt(sb.length()-1);
		targets = sb.toString();
	}

	public synchronized void run() {
		if (prevEmt != null) {
			lastEventqid = prevEmt.getLastEventqid();
			prevEmt = null;
		}

		String targets;
		synchronized (listenerMap) {
			if (this.targets == null) return;
			targets = this.targets;
		}

		try {
			ResultSet rs = Database.query("SELECT eventqid,source,target,deviceid,netboxid,subid,time,eventtypeid,state,value,severity,var,val FROM eventq LEFT JOIN eventqvar USING (eventqid) WHERE eventqid > "+lastEventqid + " AND target IN (" + targets + ") ORDER BY eventqid");
			if (rs.next()) {
				Log.d("EVENTQ_MONITOR_TASK", "RUN", "Fetched rows from eventq");
			} else {
				return;
			}

			int eventCnt=0;
			do {
				String target = rs.getString("target");
				Event e = Event.eventFactory(rs);
				eventCnt++;
				Log.d("EVENTQ_MONITOR_TASK", "RUN", "Got event: " + e);

				synchronized (listenerMap) {
					IdentityHashMap m = (IdentityHashMap)listenerMap.get(target);
					if (m != null) {
						for (Iterator it=m.entrySet().iterator();it.hasNext();) {
							Map.Entry me = (Map.Entry)it.next();
							EventQListener eql = (EventQListener)me.getKey();
							String source = (String)me.getValue();
							if (source != null && !source.equals(e.getSource())) continue;
							try {
								eql.handleEvent(e);
							} catch (Exception exp) {
								Log.w("EVENTQ_MONITOR_TASK", "RUN", "Got exception from EventQListener " + eql + ": " + exp.getMessage());
								exp.printStackTrace(System.err);
							}								
						}
					}
				}

				Log.d("EVENTQ_MONITOR_TASK", "RUN", "Processed " + eventCnt + " events in this session");
				if (rs.last()) if (rs.getInt("eventqid") > lastEventqid) lastEventqid = rs.getLong("eventqid");
			} while (rs.next());

		} catch (SQLException exp) {
			// Now we are in trouble
			Log.e("EVENTQ_MONITOR_TASK", "RUN", "SQLException when fetching from eventq: " + exp.getMessage());
			exp.printStackTrace(System.err);
		}
		
	}
}

