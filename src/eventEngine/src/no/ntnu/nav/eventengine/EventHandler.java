package no.ntnu.nav.eventengine;

import java.util.*;

import no.ntnu.nav.ConfigParser.*;

/**
 * <p> The EventHandler interface must be implemented by all event
 * handler plugins to eventengine. The method {@link #handleEventTypes
 * handleEventTypes()} tells eventengine which types of events should
 * be handled by this plugin, while the {@link #handle handle()}
 * method does the actual handling of the events.  </p>
 *
 * <b>Step-by-step guide for writing an EventHandler plugins to eventengine</b>
 * <p>
 * <ol>
 *  <li>Create a new package and class in package <i>no.ntnu.nav.eventengine.handlerplugins</i> which
 *      implement the EventHandler interface (found in package no.ntnu.nav.eventengine).
 *      Look at one of the existing EventHandler plugins for an example.
 *  </li>
 *  <li>Implement the {@link #handleEventTypes handleEventTypes()} method. It should return the names of the
 *      eventtypes the plugin can handle.
 *  </li>
 *  <li>Implement the {@link #handle handle()} method. Here the actual event processing should take place; the
 *      {@link no.ntnu.nav.eventengine.DeviceDB DeviceDB} object can be used for communicating with eventengine and
 *      device plugins.
 *  </li>
 *  <li>Compile the plugin to a JAR file. Again look at an existing plugin for
 *      an example. The build.xml file will need to be updated with the new name for the JAR file,
 *      and the Plugin-class with the name of the class implementing the EventHandler interface.
 *  </li>
 *  <li>Copy the JAR file into the handler-plugins directory of eventEngine. It will automatically
 *      be loaded; if an older copy was overwritten eventEngine must be restarted before the
 *      changes take effect.
 *  </li>
 * </ol>
 *
 * <b>The Event</b>
 *
 * <p> The {@link Event Event} object describes the event as posted on
 * the eventq. All information about the event can be retrieved from
 * this object, including any variables assosiated with the event.
 * </p>
 *
 * <b>The Alert</b>
 *
 * <p> The {@link Alert Alert} object describes an alert which is to
 * be posted on the alertq. The basic task of an EventHandler plugin
 * is to look at an incoming event, do any neccessary processing
 * (e.g. look up a {@link Device Device}, update its status and
 * observe any consequences) and post an alert if appropriate. </p>
 *
 * <p> An alert is created by calling the {@link
 * DeviceDB#alertFactory(Event) alertFactory} method of DeviceDB,
 * giving the event as an argument. All relevant information is copied
 * from the Event to the Alert. After constructing the Alert object
 * the plugin can alter it in any way it sees fit; it can update any
 * of the fields and add extra variables (the variables are used for
 * constructing the alert message texts; see the next section). The
 * alert will automatically be populated with relevant fields from the
 * database (see the top of <i>alertmsg.conf</i> for details), but
 * variables provided by the plugin will always override any variables
 * from the event or database tables.  </p>
 *
 * <b>Alertmsg.conf and the Alert message texts</b>
 *
 * <p> Events and Alerts have an eventtypeid assosiated with them;
 * Alert also has an alerttype. The combination of eventtypeid and
 * alerttype are used to find message templates in
 * <i>alertmsg.conf</i> (see the top of <i>alertmsg.conf</i> for
 * details).  The messages can contain variables (written as
 * <i>$&lt;name of variable&gt;</i>) which will be replaced by the
 * corresponding values from the Alert before it is posted on the
 * alertq.  </p>
 *
 * <p> <b>Note:</b> This is the sole use of the variables; they are
 * not used outside of eventengine. The reason for this is that
 * alertengine should not need to know about the details of event
 * processing; eventengine, and its plugins, takes sole responsability
 * for this.  </p>
 *
 * @see no.ntnu.nav.eventengine.DeviceDB
 * @see no.ntnu.nav.eventengine.Alert
 * @see no.ntnu.nav.eventengine.Event
 *
 */

public interface EventHandler
{

	/**
	 * Special event type matching all events.
	 */
	public static final String[] HANDLE_ALL_EVENTS = new String[] { "_all" };

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
