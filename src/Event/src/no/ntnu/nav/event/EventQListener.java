package no.ntnu.nav.event;

/**
 * <p> Classes which needs to receive events from the eventq should
 * implement this interface.  </p>
 */

public interface EventQListener {

	/**
	 * Method called when an event arrives.
	 *
	 * @param e The event
	 */
	public void handleEvent(Event e);

}
