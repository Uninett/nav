package no.ntnu.nav.getDeviceData.dataplugins.Swport;

/**
 * Contain Module-objects
 */

import java.util.*;

import no.ntnu.nav.getDeviceData.dataplugins.*;

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
