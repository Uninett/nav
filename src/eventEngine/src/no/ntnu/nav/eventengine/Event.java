package no.ntnu.nav.eventengine;

import java.util.*;


public interface Event
{
	public static final int STATE_NONE = 0;
	public static final int STATE_START = 10;
	public static final int STATE_END = 20;

	public String getSource();
	public int getDeviceid();
	public int getBoksid();
	public int getSubid();
	public Date getTime();
	public String getEventtypeid();
	public int getState();
	public int getValue();
	public int getSeverity();

	public Map getVarMap();

	public String getKey();

}
