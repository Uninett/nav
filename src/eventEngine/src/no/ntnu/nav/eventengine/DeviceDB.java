package no.ntnu.nav.eventengine;

/**
 * Eventengine plugins use DeviceDB to communicate with eventengine
 * and wth each other.
 *
 */

public interface DeviceDB
{

	/**
	 * Reload data from database.
	 */
	public void updateFromDB();

	/**
	 * Get the device with the given deviceid.
	 *
	 * @param deviceid Deviceid of device to get
	 * @return Device with given deviceid, or null if no such device exists
	 */
	public Device getDevice(int deviceid);

	/**
	 * Add a device to the DeviceDB.
	 *
	 * @param d The device to put
	 */
	public void putDevice(Device d);

	/**
	 * Touch the given device; that is, it is present and should not be
	 * removed.
	 *
	 * @param d The device to touch
	 */
	public void touchDevice(Device d);

	/**
	 * Return if the given device has been touched.
	 *
	 * @param d The device to check
	 * @see #touchDevice
	 */
	public boolean isTouchedDevice(Device d);

	/**
	 * Get the 'up' Alert to use for completing a previous 'down' Alert.
	 *
	 * @param e The 'up' event (STATE_END)
	 * @return the 'up' alert
	 */
	public Alert getDownAlert(Event e);

	/**
	 * Create a new alert with the given event as a template. 'default'
	 * will be used as alerttype.
	 *
	 * @param e The event to use as template
	 * @return a new alert
	 */
	public Alert alertFactory(Event e);

	/**
	 * Create a new alert with the given event as a template.
	 *
	 * @param e The event to use as template
	 * @param alerttype The alerttype to use (see top of alertmsg.conf for details)
	 * @return a new alert
	 */
	public Alert alertFactory(Event e, String alerttype);

	/**
	 * Create an 'end' event from a 'start' event. This is typically
	 * used to finish a previous 'start' event without getting an actual
	 * 'end' event.
	 *
	 * @param e The event to use as template; all key fields except for the state must match the previous 'start' event.
	 * @return an 'end' event
	 */
	public Event endEventFactory(Event e);

	/**
	 * Post and commit the given alert to the alertq, then delete
	 * the associated Events.
	 *
	 * If the state for this Alert is 'down', it will be added to the
	 * down alert list. Call getDownAlert() to get the alert to use
	 * for the 'up' Alert.
	 *
	 * @param a The alert to be posted
	 */
	public void postAlert(Alert a) throws PostAlertException;

	/**
	 * Schedule a callback after the given delay. Any previously
	 * scheduled callbacks are canceled.
	 *
	 * @param ec The object to callback
	 * @param delay Delay before callback in milliseconds
	 */
	public void scheduleCallback(EventCallback ec, long delay);

	/**
	 * Schedule a callback after the given delay. Any previously
	 * scheduled callbacks are canceled.
	 *
	 * @param ec The object to callback
	 * @param delay Delay before callback in milliseconds
	 * @param invocationCount Number of callbacks to perform
	 */
	public void scheduleCallback(EventCallback ec, long delay, int invocationCount);

	/**
	 * Check if a callback is currently scheduled.
	 *
	 * @param ec The object to check
	 * @return if a callback is currently scheduled for the given object
	 */
	public boolean isScheduledCallback(EventCallback ec);

	/**
	 * Cancel any scheduled callbacks.
	 *
	 * @param ec The object to cancel callbacks for
	 * @return true if a callback was canceled; false otherwise
	 */
	public boolean cancelCallback(EventCallback ec);

}
