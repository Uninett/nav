package no.ntnu.nav.eventengine;

import java.util.*;


public interface Alert
{

	public void setDeviceid(int deviceid);
	public void setBoksid(int boksid);
	public void setSubid(int subid);
	public void setEventtypeid(String eventtypeid);
	public void setState(int state);
	public void setValue(int value);
	public void setSeverity(int severity);

	public void addVar(String key, String val);
	public void addVars(Map varMap);

	public void setAlerttype(String alerttype);

	public void addEvent (Event e);

}
