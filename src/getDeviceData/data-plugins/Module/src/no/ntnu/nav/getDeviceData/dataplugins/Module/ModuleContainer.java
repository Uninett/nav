package no.ntnu.nav.getDeviceData.dataplugins.Module;

import java.util.*;

import no.ntnu.nav.getDeviceData.dataplugins.*;
import no.ntnu.nav.getDeviceData.dataplugins.Device.DeviceContainer;

/**
 * <p>
 * The interface to device plugins for storing collected data.
 * </p>
 *
 * <p> This plugin provides an interface for storing logical module
 * data and data about the physical device which the module
 * represent.</p>
 * 
 * <p> For storing data the device plugin should request a {@link
 * Module Module} from the {@link #moduleFactory moduleFactory} method
 * for each Module, giving the module number, serial number, and, if
 * available, the hardware and software version. </p>
 *
 * Normally this class will be inherited.
 *
 * @see ModuleHandler
 */

public class ModuleContainer extends DeviceContainer implements DataContainer {

	private ModuleHandler mh;
	private List moduleList = new ArrayList();
	private boolean commit = false;

	protected ModuleContainer(ModuleHandler mh) {
		super(null);
		this.mh = mh;
	}

	/**
	 * Get the name of the container; returns the string ModuleContainer
	 */
	public String getName() {
		return "ModuleContainer";
	}

	/**
	 * Return a Module object which is used to describe a single module
	 */
	public Module moduleFactory(String serial, String hw_ver, String sw_ver, String module) {
		Module m = new Module(serial, hw_ver, sw_ver, module);
		moduleList.add(m);
		return m;
	}

	public void commit() {
		commit = true;		
	}

	// Doc in parent
	protected boolean isCommited() {
		return commit;
	}
	
	Iterator getModules() {
		Collections.sort(moduleList);
		return moduleList.iterator();
	}


}
