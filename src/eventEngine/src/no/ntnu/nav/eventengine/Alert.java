package no.ntnu.nav.eventengine;

import java.util.*;


public interface Alert
{

	public void setSource(String source);
	public void setDeviceid(int deviceid);
	public void setBoksid(int boksid);

	public void addVar(String key, String val);

}
