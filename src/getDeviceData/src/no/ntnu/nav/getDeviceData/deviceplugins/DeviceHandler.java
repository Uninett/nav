package no.ntnu.nav.getDeviceData.deviceplugins;

import no.ntnu.nav.SimpleSnmp.*;
import no.ntnu.nav.ConfigParser.*;

import no.ntnu.nav.getDeviceData.Netbox;
import no.ntnu.nav.getDeviceData.dataplugins.DataContainers;

/**
 * <p> The DeviceHandler interface must be implemented by all device
 * plugin modules to getDeviceData; it contains two methods,
 * {@link #canHandleDevice canHandleDevice()} and {@link #handleDevice handleDevice()}.  </p>
 *
 * <b>Step-by-step guide for writing a device plugin</b>
 * <p>
 * <ol>
 *  <li>Create a class in package <i>no.ntnu.nav.getDeviceData.deviceplugins</i> which
 *      implement the DeviceHandler interface (found in package no.ntnu.nav.getDeviceData.deviceplugins).
 *      Look at one of the existing device plugin modules for an example.
 *  </li>
 *  <li>Implement the {@link #canHandleDevice canHandleDevice()} method. The method will typically use the
 *      {@link Netbox#getType getType()} and
 *      {@link Netbox#getTypegroup getTypegroup()} methods of {@link Netbox Netbox} to determine if the device can be handled.
 *  </li>
 *  <li>Implement the {@link #handleDevice handleDevice()} method. Here the actual data collection should take place; the
 *      {@link no.ntnu.nav.SimpleSnmp.SimpleSnmp SimpleSnmp} object can be used for getting data via SNMP.
 *      Data should be returned in {@link no.ntnu.nav.getDeviceData.dataplugins.DataContainer DataContainer}
 *      objects retrieved from the {@link no.ntnu.nav.getDeviceData.dataplugins.DataContainers DataContainers} object;
 *      see DataContainers for details.
 *  </li>
 *  <li>Compile the plugin to a JAR file. Again look at an existing plugin module for
 *      an example. The build.xml file will need to be updated with the new name for the JAR file,
 *      and the Plugin-class with the name of the class implementing the DeviceHandler interface.
 *  </li>
 *  <li>Copy the JAR file into the device-plugin directory of getDeviceData. It will automatically
 *      be loaded; if an older copy was overwritten getDeviceData must be restarted before the
 *      changes take effect.
 *  </li>
 * </ol>
 *
 * <b>The architecture of getDeviceData</b>
 *
 * <p> getDeviceData first loads all devices to be queried from the
 * database and stores them in a FIFO queue as Netbox objects; the
 * device list is reloaded from the database every
 * <i>loadDataInterval</i> (see config file) minutes (a future version
 * will do this in response to a changeDevice event). Next plugins,
 * both data and device, are loaded from disk. Finally the scheduler
 * is called.  </p>
 *
 * <b>The scheduler</b>
 *
 * <p> The scheduler first examines the head of the queue, and asks
 * the Netbox object if it is ready to be queried (currently a minimum
 * time must have passed since the last query of the device for it to
 * be ready); if it is, and a thread is idle, the thread is assigned
 * the Netbox.  </p>
 *
 * <b>Threads and plugin modules</b>
 *
 * <p> When a thread is assigned a Netbox it iterates through all
 * DeviceHandler plugins, and calls the canHandleDevice() method with
 * the Netbox object as argument. Each plugin must examine the Netbox
 * and determine if it can handle it. The method documentation gives
 * more details.  </p>
 *
 * <p> After it is determined which plugins can handle the device and
 * in which order they should be called the handleDevice() method is
 * called; here the plugin should to the actual work by collecting
 * data from the device. How this is done is not specified, but
 * normally the SimpleSnmp object will be used to query the
 * device. The collected data is returned by retrieving DataContainer
 * objects from the DataContainers argument; see the doc for
 * DataContainers and DataContainer interfaces for more details.
 * After data collection is done the handleDevice() method can simply
 * return.  </p>
 *
 * @see no.ntnu.nav.getDeviceData.dataplugins.DataContainers
 * @see no.ntnu.nav.getDeviceData.dataplugins.DataContainer
 * @see no.ntnu.nav.getDeviceData.dataplugins.DataHandler
 *
 */
public interface DeviceHandler
{
	/**
	 * The value 0, which means this plugin cannot handle the given
	 * Netbox.
	 */
	public static final int NEVER_HANDLE = 0;

	/**
	 * Special value saying that this plugin should always handle the
	 * device, but its order among the plugins is not important.
	 */
	public static final int ALWAYS_HANDLE = 1;

	/**
	 * <p> This method should check if the implementing plugin can
	 * handle the device specified by the Netbox argument, and return a
	 * value different from zero if it does; this will typically be
	 * ALWAYS_HANDLE if the plugin does not have any special needs.
	 * </p>
	 *
	 * <p> If the value returned is greater than zero, no plugins with a
	 * lower absolute value will be asked to handle the device. The
	 * plugins will then be asked to handle the device in order from
	 * highest to lowest value, ignoring sign.  </p>
	 *
	 * <p> If two (or more) plugins return the same positive value, only
	 * one of them will be asked to handle the device, but it is not
	 * defined which one. If two (or more) plugins return the same
	 * absolute value, but with different sign, the plugins who returned
	 * negative values will not be asked.  </p>
	 *
	 * <p> For example, if there are five plugins, returning values -4,
	 * 1, -3, 4, and -6, only the plugins returning -6 and 4 will be
	 * asked (in that order).  </p>
	 *
	 * @param bd The data describing the device
	 * @return a value different from zero (0) if the plugin can handle the given device
	 */
	public int canHandleDevice(Netbox nb);

	/**
	 * Actually handle the device specified by the Netbox argument.
	 *
	 * @param bd The data describing the device
	 * @param sSnmp An instance of SimpleSnmp the plugins can use to do SNMP queries
	 * @param cp A ConfigParser instance reading data from nav.conf
	 * @param containers Gives access to the DataContainer objects used for returning data
	 */
	public void handleDevice(Netbox nb, SimpleSnmp sSnmp, ConfigParser cp, DataContainers containers) throws TimeoutException;

}
