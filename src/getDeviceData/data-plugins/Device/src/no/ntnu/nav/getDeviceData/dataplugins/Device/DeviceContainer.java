package no.ntnu.nav.getDeviceData.dataplugins.Device;

import java.util.*;

import no.ntnu.nav.getDeviceData.dataplugins.*;

/**
 * <p>
 * The interface to device plugins for storing collected data.
 * </p>
 *
 * <p> This plugin provides an interface for storing data about
 * physical devices.</p>
 * 
 * <p> For storing data the device plugin should request a {@link
 * Device Device} from the {@link #deviceFactory deviceFactory} method
 * for each Device, giving the serial number, and, if available, the
 * hardware and software version. </p>
 *
 * Normally this class will be inherited.
 *
 * @see DeviceHandler
 */

public class DeviceContainer implements DataContainer {

	private DeviceHandler dh;
	private List deviceList = new ArrayList();
	private boolean commit = false;

	protected DeviceContainer(DeviceHandler dh) {
		this.dh = dh;
	}

	/**
	 * Get the name of the container; returns the string DeviceContainer
	 */
	public String getName() {
		return "DeviceContainer";
	}

	/**
	 * Get a data-handler for this container; this is a reference to the
	 * ModuleHandler object which created the container.
	 */
	public DataHandler getDataHandler() {
		return dh;
	}

	/**
	 * Return a Device object which is used to describe a single physical device
	 */
	public Device deviceFactory(String serial, String hw_ver, String sw_ver) {
		Device d = new Device(serial, hw_ver, sw_ver);
		int k;
		if ( (k=deviceList.indexOf(d)) >= 0) {
			d = (Device)deviceList.get(k);
		} else {
			addDevice(d);
		}
		return d;
	}

	/**
	 * Add the device to the internal device list.
	 *
	 * @param d The device to add
	 */
	protected void addDevice(Device d) {
		deviceList.add(d);
	}

	public void commit() {
		commit = true;		
	}

	/**
	 * Return if the data in this container is commited.
	 */
	protected boolean isCommited() {
		return commit;
	}

	// Return an iterator over the devices in this container.
	Iterator getDevices() {
		return deviceList.iterator();
	}


}
