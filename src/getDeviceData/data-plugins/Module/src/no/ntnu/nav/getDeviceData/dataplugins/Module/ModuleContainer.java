package no.ntnu.nav.getDeviceData.dataplugins.Module;

import java.util.*;

import no.ntnu.nav.getDeviceData.dataplugins.*;

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

public class ModuleContainer implements DataContainer {

	private ModuleHandler mh;
	private List moduleList = new ArrayList();
	private boolean commit = false;

	protected ModuleContainer(ModuleHandler mh) {
		this.mh = mh;
	}

	/**
	 * Get the name of the container; returns the string ModuleContainer
	 */
	public String getName() {
		return "ModuleContainer";
	}

	/**
	 * Get a data-handler for this container; this is a reference to the
	 * ModuleHandler object which created the container.
	 */
	public DataHandler getDataHandler() {
		return mh;
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

	/**
	 * Return if the data in this container is commited.
	 */
	protected boolean isCommited() {
		return commit;
	}
	
	/**
	 * Add a module to the internal module list.
	 */
	protected void addModule(Module m) {
		moduleList.add(m);
	}

	Iterator getModules() {
		Collections.sort(moduleList);
		return moduleList.iterator();
	}


}
