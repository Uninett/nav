package no.ntnu.nav.getDeviceData.plugins;

import no.ntnu.nav.SimpleSnmp.*;
import no.ntnu.nav.ConfigParser.*;

public interface DeviceHandler
{
	/**
	 * This method should check if the implementing plugin can handle the device specified
	 * by the BoksData argument, and return a value different from zero if it does.
	 *
	 * If the value returned is greater than zero, no plugins with a lower absolute value
	 * will be asked to handle the device. The plugins will then be asked to handle the
	 * device in order from highest to lowest value, ignoring sign.
	 *
	 * If two (or more) plugins return the same positive value, only one of them will be
	 * asked to handle the device, but it is not defined which one. If two (or more)
	 * plugins return the same absolute value, but with different sign, the plugins who
	 * returned negative values will not be asked.
	 *
	 * For example, if there are five plugins, returning values -4, 1, -3, 4, and -6, only
	 * the plugins returning -6 and 4 will be asked (in that order).
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