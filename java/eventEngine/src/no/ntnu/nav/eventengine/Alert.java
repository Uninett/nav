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
	public void setSubid(String subid);
	public void setEventtypeid(String eventtypeid);
	public void setState(int state);
	public void setValue(int value);
	public void setSeverity(int severity);

	/**
	 * Add a variable and assosiated value to the alert. Used for
	 * replacing values in the message template from
	 * <i>alertmsg.conf</i>; see the top of that file for more details.
	 *
	 * @param key The key
	 * @param val The value assosiated with the key
	 * @see EventHandler
	 */
	public void addVar(String key, String val);

	/**
	 * Add all values in the given map; equivalent to calling {@link
	 * #addVar(String, String) addVar()} with each key/value in the map.
	 *
	 * @param varMap Map with the keys/values to add
	 * @see #addVar(String, String)
	 */
	public void addVars(Map varMap);

	/**
	 * Set the alerttype for the alert; used for selecting message
	 * template from <i>alertmsg.conf</i> to use for this alert; see the
	 * top of that file for details.
	 *
	 * @param alerttype The alerttype to set
	 * @see EventHandler
	 */
	public void setAlerttype(String alerttype);

	/**
	 * Controls if the alert should be posted to the alertq; all alerts
	 * are posted to alerthist, but it may be desirable to not actually
	 * send out some alerts.
	 *
	 * @param postAlertq true if the alert should be posted to alertq; false otherwise
	 */
	public void setPostAlertq(boolean postAlertq);

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

	/**
	 * Adds a variable and assosiated value which will be saved togheter
	 * with the alert in the alert history table in the database.
	 *
	 * @param key The key
	 * @param val The value assosiated with the key
	 */
	public void addHistoryVar(String key, String val);

	/**
	 * Add all values in the given map; equivalent to calling {@link
	 * #addHistoryVar(String, String) addHistoryVar()} with each
	 * key/value in the map.
	 *
	 * @param varMap Map with the keys/values to add
	 * @see #addHistoryVar(String, String)
	 */
	public void addHistoryVars(Map varMap);

	/**
	 * Copies the specified variable, if present, from the event to be
	 * saved togheter with the alert in the alert history table in the
	 * database.
	 *
	 * @param e The event to copy from
	 * @param key The key to copy
	 */
	public void copyHistoryVar(Event e, String key);

	/**
	 * Copies the specified variables, if present, from the event to be
	 * saved togheter with the alert in the alert history table in the
	 * database.
	 *
	 * @param e The event to copy from
	 * @param keys The keys to copy
	 */
	public void copyHistoryVars(Event e, String[] keys);

}
