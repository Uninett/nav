import no.ntnu.nav.eventengine.*;

import java.util.*;
import java.text.*;

public class EventImpl implements Event
{
	int eventqid;
	int deviceid;
	int boksid;
	Date time;
	String eventtypeid;
	Map varMap;

	public EventImpl(int eventqid, int deviceid, int boksid, String time, String eventtypeid, Map varMap)
	{
		this.eventqid = eventqid;
		this.deviceid = deviceid;
		this.boksid = boksid;
		this.eventtypeid = eventtypeid;
		this.varMap = varMap;

		SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
		try {
			this.time = sdf.parse(time);
		} catch (ParseException e) {
			errl("Error in date '" + time + "' from Postgres, should not happen: " + e.getMessage());
			return;
		}
	}

	public String toString()
	{
		//String s = "eventqid="+eventqid+" deviceid="+deviceid+" boksid="+boksid+" time="+time+" eventtypeid="+eventtypeid;
		String s = "eventqid="+eventqid+" deviceid="+deviceid+" boksid="+boksid+" time=[] eventtypeid="+eventtypeid;
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

	public int getDeviceid() { return deviceid; }
	public int getBoksid() { return boksid; }
	public Date getTime() { return time; }
	public String getEventtypeid() { return eventtypeid; }
	public Map getVarMap() { return varMap; }


	private static void outd(Object o) { System.out.print(o); }
	private static void outld(Object o) { System.out.println(o); }

	private static void err(Object o) { System.err.print(o); }
	private static void errl(Object o) { System.err.println(o); }
}