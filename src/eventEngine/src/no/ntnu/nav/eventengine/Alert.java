package no.ntnu.nav.eventengine;

import java.util.*;

/**
 * An Alert; contains all data about the alert.
 *
 */

public interface Alert
{

	public void setDeviceid(int deviceid);
	public void setNetboxid(int netboxid);
	public void setSubid(int subid);
	public void setEventtypeid(String eventtypeid);
	public void setState(int state);
	public void setValue(int value);
	public void setSeverity(int severity);

	public void addVar(String key, String val);
	public void addVars(Map varMap);

	public void setAlerttype(String alerttype);

	/**
	 * Normally the event will be assosiated with the alert when it is
	 * created, but in the case where more than one event should be
	 * assosiated with an alert this method can be used. All events
	 * assosiated with an alert are deleted from the eventq when the
	 * alert is posted to the alertq.
	 *
	 * @param e The event to assosiate with this alert
	 * @see DeviceDB#alertFactory(Event)
	 * @see Event#dispose
	 */
	public void addEvent(Event e);

}
