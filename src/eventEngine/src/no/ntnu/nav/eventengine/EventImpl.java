package no.ntnu.nav.eventengine;

import no.ntnu.nav.Database.*;

import java.util.*;
import java.io.*;
import java.text.*;
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
	public String getEventtypeid() { return eventtypeid; }
	public int getState() { return state; }
	public int getValue() { return value; }
	public int getSeverity() { return severity; }
	public Set getVar(String var) { return (Set)varMap.get(var); }
	public Map getVarMap() { return varMap; }
	public void dispose()
	{
		if (disposed) return;
		try {
			Database.update("DELETE FROM eventq WHERE eventqid = '"+eventqid+"'");
			Database.commit();
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
		Set s;
		if ( (s=(Set)varMap.get(key)) == null) varMap.put(key, s=new HashSet());
		s.add(val);
	}

	public void setAlerttype(String alerttype) { this.alerttype = alerttype; }

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
		for (Iterator i = varMap.entrySet().iterator(); i.hasNext();) {
			Map.Entry me = (Map.Entry)i.next();
			String var = (String)me.getKey();
			List l = (List)me.getValue();
			s += "\n  "+var+"=";
			for (int j=0; j<l.size(); j++) {
				s += l.get(j);
				if (j < l.size()-1) s +=", ";
			}
		}
		return s;
	}


	public static boolean setAlertmsgFile(String s) throws ParseException
	{
		return AlertmsgParser.setAlertmsgFile(s);
	}

	private static void outd(Object o) { System.out.print(o); }
	private static void outld(Object o) { System.out.println(o); }

	private static void err(Object o) { System.err.print(o); }
	private static void errl(Object o) { System.err.println(o); }
}

class AlertmsgParser
{
	private static File alertmsgFile;
	private static long alertmsgLastModified;
	private static Map eventtypeidMap = new HashMap();

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

	public static Iterator formatMsgs(String eventtypeid, String alerttype, Map varMap) throws ParseException
	{

		return null;
	}

	private static final int EXP_EVENTTYPEID = 0;
	private static final int EXP_ALERTTYPE = 1;
	private static final int EXP_MEDIA = 2;
	private static final int EXP_LANG = 3;
	private static final int EXP_MSG = 4;

	private static void parseAlertmsg() throws ParseException, IOException
	{
		if (alertmsgFile == null || alertmsgFile.lastModified() == alertmsgLastModified) return;

		BufferedReader in = new BufferedReader(new FileReader(alertmsgFile));

		int lineno = 0;
		int state = EXP_EVENTTYPEID;
		boolean exp_begin_block = false;
		boolean allow_colon_block = false;
		boolean is_colon_block = false;

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
						exp_begin_block = true;
						break;

						case EXP_ALERTTYPE:
						alerttype = t;
						exp_begin_block = true;
						break;

						case EXP_MEDIA:
						media = t;
						exp_begin_block = true;
						break;

						case EXP_LANG:
						lang = t;
						if (lang.endsWith(":")) {
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

						break;
					}
				}
			}
		}

		if (state != 0) {
			throw new ParseException("Parse error on line " + lineno + ": " + state + " unterminated blocks.", 0);
		}

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