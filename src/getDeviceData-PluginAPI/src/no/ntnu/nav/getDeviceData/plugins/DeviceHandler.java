package no.ntnu.nav.getDeviceData.plugins;

import no.ntnu.nav.SimpleSnmp.*;

public interface DeviceHandler
{
	/**
	 * This method should check if the implementing plugin can handle the device specified
	 * by the BoksData argument, and return a value greater than zero if it does.
	 *
	 * All plugins will be asked if they can handle a given device, and the one that returns
	 * the highest value greater than zero will be picked.
	 *
	 * @param bd The data describing the device
	 * @return a value greater than zero (0) if the plugin can handle the given device
	 */
	public int canHandleDevice(BoksData bd);

	public void handle(BoksData bd, SimpleSnmp sSnmp, DeviceDataList ddList) throws TimeoutException;

}