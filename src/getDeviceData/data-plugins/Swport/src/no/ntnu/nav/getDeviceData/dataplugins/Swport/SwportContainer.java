package no.ntnu.nav.getDeviceData.dataplugins.Swport;

import java.util.*;

import no.ntnu.nav.getDeviceData.dataplugins.*;

/**
 * <p>
 * The interface to device plugins for storing collected data.
 * </p>
 *
 * <p>
 * There are three types of switches:
 * <ul>
 *  <li>Single unit with fixed number of ports. This is the basic stand-alone switch, e.g. unstacked HP2524.
 *      The unit is both a Device, a Netbox and a Module.</li>
 *  <li>Multiple stacked units, each with fixed number of ports. This is simply normal switches stacked togheter; however,
 *      only the first will have an IP adress, and it is considered to be the Netbox. All units are Devices and Modules.</li>
 *  <li>Single chassis with removable modules. The chassis is a Device and Netbox, but <b>not</b> a Module. The removable
 *      modules with switch ports are considered Devices and Modules.</li>
 * </ul>
 * </p>
 *
 * <p> For storing data the device plugin should request a {@link
 * Module Module} from the {@link #moduleFactory moduleFactory} method
 * for each Module, giving the module number, serial number, and, if
 * available, the hardware and software version. For each switch port
 * on the module an {@link Swport Swport} object should be
 * requested.</p>
 *
 * @see SwportHandler
 */

public class SwportContainer implements DataContainer {

	private SwportHandler swh;
	private List moduleList = new ArrayList();

	SwportContainer(SwportHandler swh) {
		this.swh = swh;
	}

	/**
	 * Get the name of the container; returns the string SwportContainer
	 */
	public String getName() {
		return "SwportContainer";
	}

	/**
	 * Get a data-handler for this container; this is a reference to the
	 * SwportHandler object which created the container.
	 */
	public DataHandler getDataHandler() {
		return swh;
	}

	/**
	 * Return a Module object which is used to describe one switch module
	 */
	public Module moduleFactory(String serial, String hw_ver, String sw_ver, String module) {
		Module m = new Module(serial, hw_ver, sw_ver, module);
		moduleList.add(m);
		return m;
	}

	Iterator getModules() {
		Collections.sort(moduleList);
		return moduleList.iterator();
	}


}
