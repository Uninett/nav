package no.ntnu.nav.eventengine;

/**
 * The EventHandler interface must be implemented by all event handler
 * plugins to eventengine. The method handleEventTypes() tells
 * eventengine which types of events should be handled by this plugin,
 * while the handle() method does the actual handling of the events.
 */

import java.util.*;

import no.ntnu.nav.ConfigParser.*;

public interface EventHandler
{

	/**
	 * Return a String array with each element containing a String with
	 * the name of an eventtype this plugin can handle.
	 *
	 * @return supported eventtypes
	 */
	public String[] handleEventTypes();

	/**
	 * Handle the given event.
	 *
	 * @param ddb A reference to the DeviceDB object; used for communicating with eventengine.
	 * @param e The event to be handled.
	 * @param cp A reference to a ConfigParser; used to get runtime configuration options.
	 */
	public void handle(DeviceDB ddb, Event e, ConfigParser cp);

}
