package no.ntnu.nav.eventengine;

import java.util.*;


public interface Event
{

	public int getDeviceid();
	public int getBoksid();
	public Date getTime();
	public String getEventtypeid();
	public Map getVarMap();

}
