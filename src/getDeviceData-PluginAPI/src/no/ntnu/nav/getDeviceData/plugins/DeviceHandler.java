package no.ntnu.nav.getDeviceData.plugins;

import no.ntnu.nav.SimpleSnmp.*;
import no.ntnu.nav.ConfigParser.*;

/**
 * <p>
 * The DeviceHandler interface must be implemented by all plugin modules to getDeviceData;
 * it contains two methods, canHandleDevice() and handle().
 * </p>
 *
 * <b>Step-by-step guide for writing a plugin</b>
 * <p>
 * <ul>
 *  <li>Create a class in package <i>no.ntnu.nav.getDeviceData.plugins</i> which
 *      implement the DeviceHandler interface (found in package no.ntnu.nav.getDeviceData.plugins).
 *      Look at one of the existing plugin modules for an example.
 *  </li>
 *  <li>Implement the canHandleDevice() method. The method will typically use the getType() and
 *      getTypegruppe() methods to determine if the device can be handled.
 *  </li>
 *  <li>Implement the handle() method. Here the actual data collection should take place; the
 *      SimpleSnmp object can be used for getting data via SNMP. Data should be returned in the
 *      DeviceDataList object (see below for details).
 *  </li>
 *  <li>Compile the plugin to a JAR file. Again look at an existing plugin module for
 *      an example. The build.xml will need to be updated with the new name for the JAR file,
 *      and the Plugin-class with the name of the class implementing the DeviceHandler interface.
 *  </li>
 *  <li>Copy the JAR file into the plugin directory of getDeviceData. It will automatically
 *      be loaded; if an older copy was overwritten it will be reloaded.
 *  </li>
 * </ul>
 *
 * <b>The architecture of getDeviceData</b>
 * <p>
 * getDeviceData first loads all devices to be queried from netbox and stores them in a
 * FIFO queue; the device list is reloaded from the database every <i>loadDataInterval</i> minutes
 * (a future version will do this in respons to a changeDevice event). Then all data from
 * modules / swport is loaded; this data need not be refreshed. Finally the scheduler is called.
 * </p>
 *
 * <b>The scheduler</b>
 * <p>
 * The scheduler first examines the head of the queue, and asks the device object if it is ready
 * to be queried (currently a minimum time must have passed since the last query of the device
 * for it to be ready); if it is, and a thread is idle, the thread is assigned the device.
 * </p>
 *
 * <b>Threads and plugin modules</b>
 * <p>
 * When a thread is assigned a device it iterates through all DeviceHandler plugins, and calls
 * the canHandleDevice() method with the device description object, BoksData, as parameter.
 * The plugin must examine the device and determine if it can handle it. The method documentation
 * gives more details.
 * </p>
 *
 * <p>
 * After it is determined which plugins can handle the device and in which order the handle()
 * method is called; here the plugin should to the actual work by collecting data from the
 * device. How this is done is not specified, but normally the SimpleSnmp object will be
 * used to query the device. The collected data is returned in the DeviceDataList object;
 * the plugin creates new objects describing the device (e.g. new SwportData objects for
 * describing switch ports) and adds them by calling the appropriate method of DeviceDataList
 * (e.g. addSwportData() in the case of switch ports) for each object. After data collection
 * is done the handle() method can simply return.
 * </p>
 *
 * <b>Database updating</b>
 * <p>
 * After the handle() method is called the database is updated to reflect the new state
 * of the device; rows are updated if possible, missing rows are deleted and new rows
 * inserted. The plugin modules does not need to worry about the old state of things,
 * they only need to collect the current state. This moves much complexity out of the
 * plugin module writing and avoids the need to duplicating the database updating code.
 * </p>
 *
 */
public interface DeviceHandler
{
	/**
	 * <p>
	 * This method should check if the implementing plugin can handle the device specified
	 * by the BoksData argument, and return a value different from zero if it does.
	 * </p>
	 *
	 * <p>
	 * If the value returned is greater than zero, no plugins with a lower absolute value
	 * will be asked to handle the device. The plugins will then be asked to handle the
	 * device in order from highest to lowest value, ignoring sign.
	 * </p>
	 *
	 * <p>
	 * If two (or more) plugins return the same positive value, only one of them will be
	 * asked to handle the device, but it is not defined which one. If two (or more)
	 * plugins return the same absolute value, but with different sign, the plugins who
	 * returned negative values will not be asked.
	 * </p>
	 *
	 * <p>
	 * For example, if there are five plugins, returning values -4, 1, -3, 4, and -6, only
	 * the plugins returning -6 and 4 will be asked (in that order).
	 * </p>
	 *
	 * @param bd The data describing the device
	 * @return a value different from zero (0) if the plugin can handle the given device
	 */
	public int canHandleDevice(BoksData bd);

	/**
	 * Actually handle the device specified by the BoksData argument.
	 *
	 * @param bd The data describing the device
	 * @param sSnmp An instance of SimpleSnmp the plugins can use to do SNMP queries
	 * @param cp A ConfigParser instance reading data from nav.conf
	 * @param ddList The object used to return the data collected
	 */
	public void handle(BoksData bd, SimpleSnmp sSnmp, ConfigParser cp, DeviceDataList ddList) throws TimeoutException;

}
