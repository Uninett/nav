package no.ntnu.nav.eventengine;

import no.ntnu.nav.Database.*;

import java.util.*;
import java.io.*;
import java.text.*;
import java.sql.ResultSet;
import java.sql.ResultSetMetaData;
import java.sql.SQLException;

class EventImpl implements Event, Alert
{
	private int eventqid;
	private String source;
	private int deviceid;
	private int boksid;
	private int subid;
	private Date time;
	private String eventtypeid;
	private int state;
	private int value;
	private int severity;
	private Map varMap;

	private String alerttype;

	private List eventList = new ArrayList();

	private boolean disposed;

	public EventImpl(int eventqid, String source, int deviceid, int boksid, int subid, String time, String eventtypeid, char state, int value, int severity, Map varMap)
	{
		this.eventqid = eventqid;
		this.source = source;
		this.deviceid = deviceid;
		this.boksid = boksid;
		this.subid = subid;

		try {
			this.time = stringToDate(time);
		} catch (ParseException e) {
			errl("Error in date '" + time + "' from Postgres, should not happen: " + e.getMessage());
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
		boksid = e.boksid;
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

	public int getEventqid() { return eventqid; }
	public void setEventqid(int i) { eventqid = i; }

	// Event
	public String getSource() { return source; }
	public int getDeviceid() { return deviceid; }
	public Integer getDeviceidI() { return new Integer(deviceid); }
	public int getBoksid() { return boksid; }
	public int getSubid() { return subid; }
	public Date getTime() { return time; }
	public String getTimeS() { return dateToString(time); }
	public String getEventtypeid() { return eventtypeid; }
	public int getState() { return state; }
	public int getValue() { return value; }
	public int getSeverity() { return severity; }
	//public Set getVar(String var) { return (Set)varMap.get(var); }
	public String getVar(String var) { return (String)varMap.get(var); }
	public Map getVarMap() { return varMap; }
	public void dispose()
	{
		if (disposed) return;
		try {
			Database.update("DELETE FROM eventq WHERE eventqid = '"+eventqid+"'");
		} catch (SQLException e) {
			errl("EventImpl: Cannot dispose of self: " + e.getMessage());
			return;
		}
		disposed = true;
	}

	// Alert
	public void setDeviceid(int deviceid) { this.deviceid = deviceid; }
	public void setBoksid(int boksid) { this.boksid = boksid; }
	public void setSubid(int subid) { this.subid = subid; }
	public void setEventtypeid(String eventtypeid) { this.eventtypeid = eventtypeid; }
	public void setState(int state) { this.state = state; }
	public void setValue(int value) { this.value = value; }
	public void setSeverity(int severity) { this.severity = severity; }

	public void addVar(String key, String val)
	{
		varMap.put(key, val);
	}
	public void addVars(Map vm)
	{
		varMap.putAll(vm);
	}

	public void setAlerttype(String alerttype) { this.alerttype = alerttype; }
	public Iterator getMsgs() {
		// Update varMap from database
		try {
			ResultSet rs = Database.query("SELECT * FROM device JOIN netbox USING (deviceid) LEFT JOIN type USING (typeid) LEFT JOIN room USING (roomid) LEFT JOIN location USING (locationid) WHERE deviceid = " + deviceid);
			ResultSetMetaData rsmd = rs.getMetaData();
			if (rs.next()) {
				HashMap hm = Database.getHashFromResultSet(rs, rsmd);
				varMap.putAll(hm);
			}
		} catch (SQLException e) {
			errl("EventImpl: SQLException when fetching data from deviceid("+deviceid+"): " + e.getMessage());
		}

		return AlertmsgParser.formatMsgs(eventtypeid, alerttype, state, varMap);
	}

	public void addEvent (Event e) { eventList.add(e); }

	public List getEventList() { return eventList; }


	public String getSourceSql() { return source; }
	public String getDeviceidSql() { return deviceid>0 ? String.valueOf(deviceid) : "null"; }
	public String getBoksidSql() { return boksid>0 ? String.valueOf(boksid) : "null"; }
	public String getSubidSql() { return subid>0 ? String.valueOf(subid) : "null"; }
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
		if (boksid > 0) sb.append(boksid+":");
		if (subid > 0) sb.append(subid+":");
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
		//String s = "eventqid="+eventqid+" deviceid="+deviceid+" boksid="+boksid+" time="+time+" eventtypeid="+eventtypeid;
		String s = "eventqid="+eventqid+" deviceid="+deviceid+" boksid="+boksid+" time=[] eventtypeid="+eventtypeid+" state="+getStateSql();
		boolean first=true;
		for (Iterator i = varMap.entrySet().iterator(); i.hasNext();) {
			Map.Entry me = (Map.Entry)i.next();
			String var = (String)me.getKey();
			String val = (String)me.getValue();
			if (first) { first = false; s += "\n"; }
			s += "["+var+"="+val+"] ";
			/*
			List l = (List)me.getValue();
			s += "\n  "+var+"=";
			for (int j=0; j<l.size(); j++) {
				s += l.get(j);
				if (j < l.size()-1) s +=", ";
			}
			*/
		}
		return s;
	}

	/*
	private HashMap getHashFromResultSet(ResultSet rs, ResultSetMetaData md) throws SQLException
	{
		HashMap hm = new HashMap();
		for (int i=md.getColumnCount(); i > 0; i--) {
			hm.put(md.getColumnName(i), rs.getString(i));
		}
		return hm;
	}
	*/

	private static void outd(Object o) { System.out.print(o); }
	private static void outld(Object o) { System.out.println(o); }

	private static void err(Object o) { System.err.print(o); }
	private static void errl(Object o) { System.err.println(o); }
}

class AlertmsgParser
{
	private static File alertmsgFile;
	private static long alertmsgLastModified;
	private static Map eventtypeidMap;

	public static boolean setAlertmsgFile(String s) throws ParseException
	{
		File f = new File(s);
		if (!f.exists()) return false;
		if (alertmsgFile != null && alertmsgFile.equals(f)) return true;

		alertmsgFile = f;
		alertmsgLastModified = 0;

		try {
			parseAlertmsg();
		} catch (IOException e) {
			outld("IOException when parsing alertmsg file: " + e.getMessage());
		}
		return true;
	}

	public static Iterator formatMsgs(String eventtypeid, String alerttype, int state, Map varMap)
	{
		try {
			parseAlertmsg();
		} catch (ParseException e) {
			outld("ParseException when parsing alertmsg file: " + e.getMessage());
		} catch (IOException e) {
			outld("IOException when parsing alertmsg file: " + e.getMessage());
		}

		Map m = (Map)eventtypeidMap.get(eventtypeid);
		if (m == null) {
			outld("Eventtypeid: " + eventtypeid + " not found in alertmsg file!");
			return null;
		}

		if (alerttype == null) alerttype = "";
		List msgList = (List)m.get(alerttype);
		if (msgList == null) {
			String s = state==Event.STATE_NONE?"":state==Event.STATE_START?"Start":"End";
			outld("Alerttype: WARNING: " + alerttype + " not found in alertmsg file! Trying default"+s);

			msgList = (List)m.get("default"+s);
			if (msgList == null) {
				outld("Alerttype: FATAL: default"+s+" not found in alertmsg file!");
				return null;
			}
		}

		List l = new ArrayList();
		for (Iterator it=msgList.iterator(); it.hasNext();) {
			String[] s = (String[])it.next();

			StringBuffer msg = new StringBuffer(s[2]);

			int i = 0;
			while ( (i=msg.indexOf("$", i)) != -1) {
				if (++i == msg.length()) break;
				int e = i;
				while (e < msg.length() && Character.isLetterOrDigit(msg.charAt(e))) e++;
				String var = msg.substring(i, e).trim();
				if (var.length() == 0) continue;
				if (varMap.containsKey(var)) {
					String val = (String)varMap.get(var);
					if (val == null) val = "[empty]";
					msg.replace(i-1, e, val);
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

		BufferedReader in = new BufferedReader(new FileReader(alertmsgFile));

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

						outld("Eventtypeid: " + eventtypeid + " Alerttype: " + alerttype + " Media: " + media + " Lang: " + lang + " Msg:");
						outld(msg);
						outld("---");

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


	private static void outd(Object o) { System.out.print(o); }
	private static void outld() { System.out.println(); }
	private static void outld(Object o) { System.out.println(o); }

	private static void err(Object o) { System.err.print(o); }
	private static void errl(Object o) { System.err.println(o); }
}