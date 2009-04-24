import java.util.*;
import java.io.*;
import java.text.*;
import java.sql.ResultSet;
import java.sql.ResultSetMetaData;
import java.sql.SQLException;

import no.ntnu.nav.Database.*;
import no.ntnu.nav.logger.*;
import no.ntnu.nav.eventengine.*;

/**
 * Implementation of Event and Alert interfaces.
 *
 */

class EventImpl implements Event, Alert
{
	private String eventqid;
	private String source;
	private int deviceid;
	private int netboxid;
	private String subid;
	private Date time;
	private String eventtypeid;
	private int state;
	private int value;
	private int severity;
	private Map varMap;
	private Map historyVarMap = new HashMap();

	private String alerttype;
	private boolean postAlertq = true;

	private List eventList = new ArrayList();

	private boolean disposed;
	private boolean deferred;

	public EventImpl(String eventqid, String source, int deviceid, int netboxid, String subid, String time, String eventtypeid, char state, int value, int severity, Map varMap)
	{
		this.eventqid = eventqid;
		this.source = source;
		this.deviceid = deviceid;
		this.netboxid = netboxid;
		this.subid = subid;

		try {
			this.time = stringToDate(time);
		} catch (ParseException e) {
			Log.c("EVENT_IMPL", "CONSTRUCTOR", "Error in date '" + time + "' from Postgres, should not happen: " + e.getMessage());
		}

		this.eventtypeid = eventtypeid;

		switch (state) {
			case 'x': this.state = STATE_NONE; break;
			case 's': this.state = STATE_START; break;
			case 'e': this.state = STATE_END; break;
		}

		this.value = value;
		this.severity = severity;
		this.varMap = varMap;
	}

	public EventImpl(EventImpl e)
	{
		eventqid = e.eventqid;
		source = e.source;
		deviceid = e.deviceid;
		netboxid = e.netboxid;
		subid = e.subid;
		time = e.time;
		eventtypeid = e.eventtypeid;
		state = e.state;
		value = e.value;
		severity = e.severity;
		varMap = (Map) ((HashMap)e.varMap).clone();
	}
	public EventImpl()
	{
		source = "";
		eventtypeid = "";
		varMap = new HashMap();
	}

	public String getEventqid() { return eventqid; }
	public void setEventqid(String s) { eventqid = s; }

	// Event
	public String getSource() { return source; }
	public int getDeviceid() { return deviceid; }
	public Integer getDeviceidI() { return new Integer(deviceid); }
	public int getNetboxid() { return netboxid; }
	public String getSubid() { return subid; }
	public Date getTime() { return time; }
	public String getTimeS() { return dateToString(time); }
	public String getEventtypeid() { return eventtypeid; }
	public int getState() { return state; }
	public int getValue() { return value; }
	public int getSeverity() { return severity; }
	//public Set getVar(String var) { return (Set)varMap.get(var); }
	public String getVar(String var) { return (String)varMap.get(var); }
	public Iterator getVarIterator() { return varMap.entrySet().iterator(); }
	public Map getVarMap() { return new HashMap(varMap); }
	public void dispose()
	{
		if (disposed) return;
		try {
			Database.update("DELETE FROM eventq WHERE eventqid = '"+eventqid+"'");
		} catch (SQLException e) {
			Log.e("EVENT_IMPL", "DISPOSE", "EventImpl: Cannot dispose of self: " + e.getMessage());
			return;
		}
		disposed = true;
	}
	public void defer(String reason) {
		if (disposed || deferred) return;
		try {
			String sev = getSeverity() == 0 ? "-1" : "(-severity)";
			Database.update("UPDATE eventq SET severity = " + sev + " WHERE eventqid = '"+eventqid+"'");
		} catch (SQLException e) {
			Log.e("EVENT_IMPL", "DEFER", "Cannot update severity: " + e.getMessage());
			return;
		}
		postEventqvar("deferred", "yes");
		if (reason != null) postEventqvar("deferred_reason", reason);
		deferred = true;		
	}

	private void postEventqvar(String var, String val) {
		try {
			String[] ins = {
				"eventqid", eventqid,
				"var", var,
				"val", val,
			};
			Database.insert("eventqvar", ins);
		} catch (SQLException e) {
			Log.e("EVENT_IMPL", "POST_EVENTQVAR", "Cannot post to eventqvar: " + e.getMessage());
		}
	}

	// Alert
	public void setDeviceid(int deviceid) { this.deviceid = deviceid; }
	public void setNetboxid(int netboxid) { this.netboxid = netboxid; }
	public void setSubid(String subid) { this.subid = subid; }
	public void setEventtypeid(String eventtypeid) { this.eventtypeid = eventtypeid; }
	public void setState(int state) { this.state = state; }
	public void setValue(int value) { this.value = value; }
	public void setSeverity(int severity) { this.severity = severity; }

	// Doc in interface
	public void setPostAlertq(boolean postAlertq) {
		this.postAlertq = postAlertq;
	}

	// Doc in interface
	public void addVar(String key, String val) {
		varMap.put(key, val);
	}

	// Doc in interface
	public void addVars(Map vm) {
		varMap.putAll(vm);
	}

	// Doc in interface
	public void addHistoryVar(String key, String val) {
		historyVarMap.put(key, val);
	}

	// Doc in interface
	public void addHistoryVars(Map vm) {
		historyVarMap.putAll(vm);
	}

	// Doc in interface
	public void copyHistoryVar(Event e, String key) {
		String s = e.getVar(key);
		if (s != null) addHistoryVar(key, s);
	}

	// Doc in interface
	public void copyHistoryVars(Event e, String[] keys) {
		for (Iterator it = Arrays.asList(keys).iterator(); it.hasNext();) {
			String key = (String)it.next();
			String s = e.getVar(key);
			if (s != null) addHistoryVar(key, s);
		}
	}

	Iterator historyVarIterator() {
		return historyVarMap.entrySet().iterator();
	}

	public void setAlerttype(String alerttype) { this.alerttype = alerttype; }
	String getAlerttype() { return alerttype; }

	public Iterator getMsgs() {
		// Update varMap from database
		try {
			ResultSet rs = Database.query("SELECT * FROM device LEFT JOIN netbox USING (deviceid) LEFT JOIN type USING (typeid) LEFT JOIN room USING (roomid) LEFT JOIN location USING (locationid) LEFT JOIN module USING(deviceid) WHERE deviceid = " + deviceid);
			ResultSetMetaData rsmd = rs.getMetaData();
			if (rs.next()) {
				HashMap hm = Database.getHashFromResultSet(rs, rsmd);
				varMap.putAll(hm);
			}
			rs = Database.query("SELECT * FROM netbox JOIN device USING (deviceid) LEFT JOIN type USING (typeid) LEFT JOIN room USING (roomid) LEFT JOIN location USING (locationid) WHERE netboxid = " + netboxid);
			rsmd = rs.getMetaData();
			if (rs.next()) {
				HashMap hm = Database.getHashFromResultSet(rs, rsmd);
				varMap.putAll(hm);
			}
		} catch (SQLException e) {
			Log.e("EVENT_IMPL", "GET_MSGS", "SQLException when fetching data from deviceid("+deviceid+"): " + e.getMessage());
			e.printStackTrace(System.err);
		}

		// Add time
		addVar("time", getTimeS());

		Iterator msgList = AlertmsgParser.formatMsgs(eventtypeid, alerttype, state, varMap);
		if (!msgList.hasNext()) {
			// No appropriate templates found in alertmsg file, just dump alert data as alert message text
			Log.i("EVENT_IMPL", "GET_MSGS", "Creating crude detail dump as messages for this alert");
			msgList = AlertmsgParser.dumpMsgs(eventtypeid, alerttype, state, varMap);
		}
		return msgList;
	}

	public void addEvent (Event e) { eventList.add(e); }

	public List getEventList() { return eventList; }

	public boolean getPostAlertq() { return postAlertq; }

	public String getSourceSql() { return source; }
	public String getDeviceidSql() { return deviceid>0 ? String.valueOf(deviceid) : "null"; }
	public String getNetboxidSql() { return netboxid>0 ? String.valueOf(netboxid) : "null"; }
	public String getSubidSql() { return subid; }
	public String getTimeSql() { return dateToString(time); }
	public String getEventtypeidSql() { return eventtypeid; }
	public String getStateSql()
	{
		switch (state) {
			case STATE_NONE: return "x";
			case STATE_START: return "s";
			case STATE_END: return "e";
		}
		return null;
	}
	public String getValueSql() { return String.valueOf(value); }
	public String getSeveritySql() { return String.valueOf(severity); }

	public String getKey()
	{
		StringBuffer sb = new StringBuffer();
		if (deviceid > 0) sb.append(deviceid+":");
		if (netboxid > 0) sb.append(netboxid+":");
		if (subid != null) sb.append(subid+":");
		sb.append(eventtypeid+":");
		sb.append(state);
		return sb.toString();
	}

	public boolean isDisposed() { return disposed; }

	public static boolean setAlertmsgFile(String s) throws ParseException
	{
		return AlertmsgParser.setAlertmsgFile(s);
	}

	private Date stringToDate(String d) throws ParseException
	{
		SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
		return sdf.parse(d);
	}
	private String dateToString(Date d)
	{
		SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
		return sdf.format(d);
	}


	public String toString()
	{
		String s = "e="+eventqid+" d="+deviceid+" n="+netboxid+" sub=" + subid + " t="+eventtypeid+" s="+getStateSql();
		boolean first=true;
		for (Iterator i = varMap.entrySet().iterator(); i.hasNext();) {
			Map.Entry me = (Map.Entry)i.next();
			String var = (String)me.getKey();
			String val = (String)me.getValue();
			//if (first) { first = false; s += "\n"; }
			s += " ["+var+"="+val+"]";
		}
		return s;
	}

}

class AlertmsgParser
{
	private static File alertmsgFile;
	private static long alertmsgLastModified;
	private static Map eventtypeidMap;

	public static boolean setAlertmsgFile(String s) throws ParseException
	{
		File f = new File(s);
		if (!f.exists()) {
			Log.w("ALERTMSG_PARSER", "SET_ALERTMSG_FILE", "File " + f + " does not exist!");
			return false;
		}
		if (alertmsgFile != null && alertmsgFile.equals(f)) return true;

		alertmsgFile = f;
		alertmsgLastModified = 0;

		try {
			parseAlertmsg();
		} catch (IOException e) {
			Log.w("ALERTMSG_PARSER", "SET_ALERTMSG_FILE", "IOException when parsing alertmsg file: " + e.getMessage());
		}
		return true;
	}

	/**
	 * <p>Dump alert details as alert messages.</p>
	 * 
	 * <p>When an alert template is missing, this method can be used to
	 * create messages with crude alert details.  Messages are generated
	 * for the languages Norwegian and English for the medias email, sms
	 * and jabber.  Note that the message text will be in English even
	 * though the language is specified as Norwegian.</p>
	 * 
	 * @see #formatMsgs(String, String, int, Map)
	 * @param eventtypeid The event type id of the alert.
	 * @param alerttype The alert type of the alert.
	 * @param state The alert state (STATE_NONE, STATE_START or STATE_END)
	 * @param varMap An alert variable map.
	 * @return A message iterator.
	 */
	public static Iterator dumpMsgs(String eventtypeid, String alerttype, int state, Map varMap)
	{
		List msgDumps = new ArrayList();
		StringBuffer msg = new StringBuffer("");
		String sysname = (String) (varMap.containsKey("sysname") ? varMap.get("sysname") : "device# " + varMap.get("deviceid"));
		String stateString = "none";
		switch (state) {
			case EventImpl.STATE_START: stateString = "start"; break;
			case EventImpl.STATE_END: stateString = "end"; break;
		}

		msg.append(eventtypeid + " (" + alerttype + "/" + stateString + ") ");
		msg.append("for " + sysname + "\n");

		msgDumps.add(new String[] { "sms", "en", msg.toString() + "(missing template)" });
		msgDumps.add(new String[] { "sms", "no", msg.toString() + "(missing template)" });

		msg.append("Missing message template for event type=" + eventtypeid + ", ");
		msg.append("alert type=" + alerttype + ", state=" + stateString + "\n");
		msg.append("Alert dump follows:\n\n");
		
		for (Iterator it=varMap.entrySet().iterator(); it.hasNext();) {
			Map.Entry entry = (Map.Entry) it.next();
			msg.append(entry.getKey().toString() + "=" + entry.getValue().toString() + "\n");
		}

		msgDumps.add(new String[] { "jabber", "en", msg.toString() });
		msgDumps.add(new String[] { "jabber", "no", msg.toString() });

		// First line is used as email subject:
		msg.insert(0, "Subject: ");
		msgDumps.add(new String[] { "email", "en", msg.toString() });
		msgDumps.add(new String[] { "email", "no", msg.toString() });

		return msgDumps.iterator();
	}
	
	public static Iterator formatMsgs(String eventtypeid, String alerttype, int state, Map varMap)
	{
		Log.setDefaultSubsystem("ALTERTMSG_PARSER");
		List l = new ArrayList();

		try {
			parseAlertmsg();
			if (eventtypeidMap == null) {
				// This happens when alertmsgFile does not exist
				return l.iterator();
			}
		} catch (ParseException e) {
			Log.w("FORMAT_MSGS", "ParseException when parsing alertmsg file: " + e.getMessage());
			return l.iterator();
		} catch (IOException e) {
			Log.w("FORMAT_MSGS", "IOException when parsing alertmsg file: " + e.getMessage());
			return l.iterator();
		}

		Map m = (Map)eventtypeidMap.get(eventtypeid);
		if (m == null) {
			Log.w("FORMAT_MSGS", "Eventtypeid: " + eventtypeid + " not found in alertmsg file!");
			return l.iterator();
		}

		if (alerttype == null) alerttype = "";
		List msgList = (List)m.get(alerttype);
		if (msgList == null) {
			String s = state==Event.STATE_NONE?"":state==Event.STATE_START?"Start":"End";
			Log.w("FORMAT_MSGS", "Alerttype: " + alerttype + " not found in alertmsg file! Trying default"+s);

			msgList = (List)m.get("default"+s);
			if (msgList == null) {
				Log.w("FORMAT_MSGS", "Alerttype: default"+s+" not found in alertmsg file! Giving up. " + m);
				return l.iterator();
			}
		}

		for (Iterator it=msgList.iterator(); it.hasNext();) {
			String[] s = (String[])it.next();

			StringBuffer msg = new StringBuffer(s[2]);

			int i = 0;
			while ( (i=msg.indexOf("$", i)) != -1) {
				if (++i == msg.length()) break;
				int e = i;
				while (e < msg.length() && (Character.isLetterOrDigit(msg.charAt(e)) || msg.charAt(e) == ';' || msg.charAt(e) == '_')  ) e++;
				String var = msg.substring(i, e).trim();
				if (var.length() == 0) continue;
				if (varMap.containsKey(var) || varMap.containsKey(var.toLowerCase())) {
					String val = (String)varMap.get(var);
					if (val == null) val = (String)varMap.get(var.toLowerCase());
					if (val == null) val = "[empty]";
					msg.replace(i-1, e, val);
				} else {
					System.err.println("Could not expand " + var + ", vars: " + varMap + ", msg: " + msg);
				}
			}
			l.add(new String[] { s[0], s[1], msg.toString() });
		}
		return l.iterator();
	}

	private static final int EXP_EVENTTYPEID = 0;
	private static final int EXP_ALERTTYPE = 1;
	private static final int EXP_MEDIA = 2;
	private static final int EXP_LANG = 3;
	private static final int EXP_MSG = 4;

	private static void parseAlertmsg() throws ParseException, IOException
	{
		if (alertmsgFile == null || alertmsgFile.lastModified() == alertmsgLastModified) return;
		alertmsgLastModified = alertmsgFile.lastModified();

		BufferedReader in = new BufferedReader(new InputStreamReader(new FileInputStream(alertmsgFile), "UTF-8"));

		int lineno = 0;
		int state = EXP_EVENTTYPEID;
		boolean exp_begin_block = false;
		boolean allow_colon_block = false;
		boolean is_colon_block = false;

		Map etMap = new HashMap();
		Map atMap = null;
		List msgList = null;
		String eventtypeid = null;
		String alerttype = null;
		String media = null;
		String lang = null;

		while (in.ready()) {
			lineno++;
			String line = in.readLine();
			String lineT = line.trim();
			if (lineT.length() == 0) continue;

			switch (lineT.charAt(0)) {
				case ';':
				case '#':
				break;

				default:
				StringTokenizer st = new StringTokenizer(line);
				while (st.hasMoreTokens()) {
					String t = (state == EXP_MSG ? st.nextToken("") : st.nextToken());
					if (exp_begin_block) {
						if (allow_colon_block) {
							allow_colon_block = false;
							if (t.equals(":")) is_colon_block = true;
						}
						if (!is_colon_block && !t.equals("{")) {
							throw new ParseException("Parse error on line " + lineno + ": Expected {, got " + t, 0);
						}
						exp_begin_block = false;
						state++;
						continue;
					}

					if (t.equals("}")) {
						state--;
						continue;
					}

					switch (state) {
						case EXP_EVENTTYPEID:
						eventtypeid = t;
						if ( (atMap=(Map)etMap.get(t)) == null) etMap.put(t, atMap = new HashMap());
						exp_begin_block = true;
						break;

						case EXP_ALERTTYPE:
						alerttype = t;
						if ( (msgList=(List)atMap.get(t)) == null) atMap.put(t, msgList = new ArrayList());
						exp_begin_block = true;
						break;

						case EXP_MEDIA:
						media = t;
						exp_begin_block = true;
						break;

						case EXP_LANG:
						lang = t;
						if (lang.endsWith(":")) {
							lang = lang.substring(0, lang.length()-1);
							state++;
							is_colon_block = true;
							continue;
						} else {
							exp_begin_block = true;
							allow_colon_block = true;
						}
						break;

						case EXP_MSG:
						String msg;
						if (is_colon_block) {
							msg = t.trim();
							is_colon_block = false;
						} else {
							List l = new ArrayList();
							int margin=Integer.MAX_VALUE;
							{
								int m = line.lastIndexOf(t);
								StringBuffer sb = new StringBuffer();
								for (int i=0; i < m; i++) sb.append(" ");
								sb.append(t);
								t = sb.toString();
							}

							int i;
							while ( (i=t.indexOf("}")) == -1) {
								l.add(t);
								margin = Math.min(blanksAtStart(t), margin);
								t = in.readLine();
								lineno++;
							}
							String s = t.substring(0, i);
							l.add(s);
							margin = Math.min(blanksAtStart(s), margin);

							st = new StringTokenizer(t.length()>i+1 ? t.substring(i+1, t.length()) : "");

							StringBuffer sb = new StringBuffer();
							for (Iterator it = l.iterator(); it.hasNext();) {
								s = (String)it.next();
								sb.append((s.length() > margin ? s.substring(margin, s.length()) : "")+"\n");
							}
							sb.deleteCharAt(sb.length()-1);
							if (sb.length() > 0 && sb.charAt(sb.length()-1) == '\n') {
								sb.deleteCharAt(sb.length()-1);
							}
							msg = sb.toString();

						}
						state--;

						Log.d("PARSE_ALERTMSG", "Eventtypeid: " + eventtypeid + " Alerttype: " + alerttype + " Media: " + media + " Lang: " + lang + " Msg:");
						Log.d("PARSE_ALERTMSG", msg);
						Log.d("PARSE_ALERTMSG", "---");

						msgList.add(new String[] { media, lang, msg } );

						break;
					}
				}
			}
		}

		if (state != 0) {
			throw new ParseException("Parse error on line " + lineno + ": " + state + " unterminated blocks.", 0);
		}

		eventtypeidMap = etMap;

	}

	private static int blanksAtStart(String s)
	{
		String ss = s.trim();
		if (ss.length() == 0) return Integer.MAX_VALUE;
		return s.indexOf(ss);
	}

	/*
	private static void outd(Object o) { System.out.print(o); }
	private static void outld() { System.out.println(); }
	private static void outld(Object o) { System.out.println(o); }

	private static void err(Object o) { System.err.print(o); }
	private static void errl(Object o) { System.err.println(o); }
	*/
}
