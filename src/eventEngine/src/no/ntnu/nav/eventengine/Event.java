package no.ntnu.nav.eventengine;

import java.util.*;

/**
 * An Event; contains all data about the event.
 *
 */

public interface Event
{
	public static final int STATE_NONE = 0;
	public static final int STATE_START = 10;
	public static final int STATE_END = 20;

	public String getSource();
	public int getDeviceid();
	public Integer getDeviceidI();
	public int getNetboxid();
	public int getSubid();
	public Date getTime();
	public String getTimeS();
	public String getEventtypeid();
	public int getState();
	public int getValue();
	public int getSeverity();

	public String getVar(String var);

	public String getKey();

	/**
	 * Dispose of the event. Normally this happens automatically when an
	 * alert created from this event is posted, but in the case no alert
	 * is to be posted this method can be used.
	 */
	public void dispose();

}
