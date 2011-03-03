package no.ntnu.nav.eventengine;

import java.util.*;

/**
 * An Event; contains all data about the event.
 *
 */

public interface Event
{
	/**
	 * A stateless event, which is not assosiated with any other events.
	 */
	public static final int STATE_NONE = 0;

	/**
	 * The start-event of a stateful event. Start-events needs to be followed by
	 * an end-event.
	 */
	public static final int STATE_START = 10;

	/**
	 * The end-event of a stateful event. Cancels the state set by the
	 * start-event. Note that the "key" (see {@link #getKey getKey}
	 * below) of the end-event must be equal to that of the start-event
	 * except for the state.
	 *
	 * @see #getKey
	 */
	public static final int STATE_END = 20;

	public String getSource();
	public int getDeviceid();
	public Integer getDeviceidI();
	public int getNetboxid();
	public String getSubid();
	public Date getTime();
	public String getTimeS();
	public String getEventtypeid();
	public int getState();
	public int getValue();
	public int getSeverity();

	/**
	 * Get the value assosiated with the given variable. The variables
	 * are those posted to eventqvar togheter with the event.
	 *
	 * @return the value assosiated with the given key
	 */
	public String getVar(String var);

	/**
	 * Returns an iterator over all variables in this Event. Each element is a {@link java.util.Map.Entry Map.Entry} object.
	 *
	 * @return iterator over all variables in this Event
	 */
	public Iterator getVarIterator();

	/**
	 * Returns a map with all variables in this Event.
	 */
	public Map getVarMap();

	/**
	 * <p> Get the key which identifies this Event. It is composed of:
	 * </p>
	 *
	 * <p>
	 * <ul>
	 *  <li>deviceid</li>
	 *  <li>netboxid</li>
	 *  <li>sbuid</li>
	 *  <li>eventtypeid</li>
	 *  <li>state</li>
	 * </ul>
	 * </p>
	 *
	 * <p> These fields are required to uniquely identify the Event; if
	 * a second Event arrives with these fields equal to any previous
	 * Event not yet processed and posted to the alertq it should be
	 * consitered a duplicate by eventengine plugins.  </p>
	 *
	 * @return the key which uniquely identifies this Event
	 */
	public String getKey();

	/**
	 * <p> Dispose of the event. Normally this happens automatically
	 * when an alert created from this event is posted, but in the case
	 * no alert is to be posted this method can be used.  </p>
	 *
	 * <p> <b>Note:</b> Events not disposed of, either automatically or
	 * through this method will <b>not</b> be deleted from the eventq.
	 * </p>
	 */
	public void dispose();

	/**
	 * <p> Defer the event. The event will not be deleted, but rather
	 * marked as 'deferred'; its severity will be set to a negative
	 * value and eventengine will not do further prosessing on it.  </p>
	 *
	 * <p> Also the reason for deferring it will be written to
	 * eventqvar, with the variables 'deferred = yes' and
	 * 'deferred_reason = reason'.  </p>
	 */
	public void defer(String reason);

}
