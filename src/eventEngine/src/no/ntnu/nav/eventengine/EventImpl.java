package no.ntnu.nav.eventengine;

import java.util.*;
import java.text.*;

class EventImpl implements Event, Alert
{
	int eventqid;
	String source;
	int deviceid;
	int boksid;
	int subid;
	Date time;
	String eventtypeid;
	int state;
	int value;
	int severity;
	Map varMap;

	List eventList = new ArrayList();

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
			case 't': this.state = STATE_START; break;
			case 'f': this.state = STATE_END; break;
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
	public int getBoksid() { return boksid; }
	public int getSubid() { return subid; }
	public Date getTime() { return time; }
	public String getEventtypeid() { return eventtypeid; }
	public int getState() { return state; }
	public int getValue() { return value; }
	public int getSeverity() { return severity; }
	public Map getVarMap() { return varMap; }

	// Alert
	public void setDeviceid(int deviceid) { this.deviceid = deviceid; }
	public void setBoksid(int boksid) { this.boksid = boksid; }
	public void setSubid(int subid) { this.subid = subid; }
	public void setEventtypeid(String eventtypeid) { this.eventtypeid = eventtypeid; }
	public void setState(int state) { this.state = state; }
	public void setValue(int value) { this.value = value; }
	public void setSeverity(int severity) { this.severity = severity; }

	public void addVar(String key, String val) { varMap.put(key, val); }

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
			case STATE_START: return "t";
			case STATE_END: return "f";
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


	private static void outd(Object o) { System.out.print(o); }
	private static void outld(Object o) { System.out.println(o); }

	private static void err(Object o) { System.err.print(o); }
	private static void errl(Object o) { System.err.println(o); }
}