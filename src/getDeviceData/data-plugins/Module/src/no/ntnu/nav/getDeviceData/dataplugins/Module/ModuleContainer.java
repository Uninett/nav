package no.ntnu.nav.getDeviceData.dataplugins.Module;

import java.util.*;

import no.ntnu.nav.logger.*;
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

	public static final int PRIORITY_MODULE = 25;

	private ModuleHandler mh;
	private List moduleList = new ArrayList();
	//private Set moduleSet = new HashSet();
	protected Map moduleTranslation = new HashMap();
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

	// Doc in parent
	public int getPriority() {
		return PRIORITY_MODULE;
	}

	/**
	 * Get a data-handler for this container; this is a reference to the
	 * ModuleHandler object which created the container.
	 */
	public DataHandler getDataHandler() {
		return mh;
	}

	public void moduleTranslate(String from, String to) {
		System.err.println("Translate from " + from + " to " + to);
		moduleTranslation.put(from, to);
	}

	/**
	 * Return a Module object which is used to describe a single
	 * module. If the argument is not a valid number an empty Module
	 * will be returned and the error logged.
	 */
	public Module moduleFactory(String module) {
		try {
			int m = Integer.parseInt(module);
			return moduleFactory(m);
		} catch (NumberFormatException e) {
			Log.w("ModuleHandler", "MODULE-FACTORY", "Not a valid module number: " + module);
		}
		return new Module(0);
	}

	/**
	 * Return a Module object which is used to describe a single module.
	 */
	public Module moduleFactory(int module) {
		if (moduleTranslation.containsKey(""+module)) module = Integer.parseInt((String)moduleTranslation.get(""+module));
		Module m = new Module(module);
		int k;
		if ( (k=moduleList.indexOf(m)) >= 0) {
			m = (Module)moduleList.get(k);
		} else {
			addModule(m);
		}
		return m;
	}

	/**
	 * Return a Module object which is used to describe a single
	 * module. Note that serial, hw_ver and sw_ver are ignored if the
	 * module already exists.
	 */
	public Module moduleFactory(String serial, String hw_ver, String fw_ver, String sw_ver, int module) {
		if (moduleTranslation.containsKey(""+module)) module = Integer.parseInt((String)moduleTranslation.get(""+module));
		Module m = new Module(serial, hw_ver, fw_ver, sw_ver, module);
		int k;
		if ( (k=moduleList.indexOf(m)) >= 0) {
			m = (Module)moduleList.get(k);
		} else {
			addModule(m);
		}
		return m;
	}

	/**
	 * Get the module if it has been created with a previous call to
	 * moduleFactory, or return null if the module does not exist.
	 */
	public Module getModule(int module) {
		if (moduleTranslation.containsKey(""+module)) module = Integer.parseInt((String)moduleTranslation.get(""+module));
		Module m = new Module(module);
		int k;
		if ( (k=moduleList.indexOf(m)) >= 0) {
			return (Module)moduleList.get(k);
		}
		return null;
	}

	/**
	 * Get the set of module numbers.
	 */
	public Set getModuleSet() {
		Set moduleSet = new HashSet();
		for (Iterator it=moduleList.iterator(); it.hasNext();) {
			Module m = (Module)it.next();
			moduleSet.add(""+m.getModule());
		}
		return moduleSet;
	}

	/**
	 * Return the supervisor module, if not found the first module, or
	 * create module 1 if no modules are present.
	 */
	public Module getSupervisorModule() {
		// Try to find a supervisor module
		int module = 1;
		boolean found = false;
		for (Iterator it = getModules(); it.hasNext();) {
			Module m = (Module)it.next();
			if (!found) {
				module = m.getModule();
				found = true;
			}
			String model = m.getModel();
			if (model == null) model = "";
			String descr = m.getDescr();
			if (descr == null) descr = "";

			if (model.toLowerCase().indexOf("sup") >= 0 || descr.toLowerCase().indexOf("sup") >= 0) {
				module = m.getModule();
				break;
			}
		}
		Module m = moduleFactory(module);
		return m;
	}

	/**
	 * Copy all data in the given container to this container.
	 */
	public void setEqual(ModuleContainer mc) {
		for (Iterator it = mc.getModules(); it.hasNext();) {
			Module m = (Module)it.next();
			Module myModule = moduleFactory(m.getModule());
			myModule.setEqual(m);
		}
	}

	/**
	 * Add the module to the internal module list.
	 *
	 * @param m The module to add
	 */
	protected void addModule(Module m) {
		// Also add it to the parent
		addDevice(m);
		moduleList.add(m);
		//moduleSet.add(""+m.getModule());
		/*
		if ("1".equals(""+m.getModule())) {
			new RuntimeException().printStackTrace(System.err);
		}
		*/
	}

	public void commit() {
		commit = true;		
	}

	public void renameModule(int from, int to) {
		for (Iterator it=moduleList.iterator(); it.hasNext();) {
			Module m = (Module)it.next();
			if (m.getModule() == from) {
				m.setModule(to);
				return;
			}
		}
	}

	public void fixHighModuleNums() {
		for (Iterator it=moduleList.iterator(); it.hasNext();) {
			Module m = (Module)it.next();
			if (m.getModule() >= 1000) m.setModule(m.getModule() / 1000);
		}
	}

	// Doc in parent
	public boolean isCommited() {
		return commit;
	}

	// Doc in parent
	protected void removeIgnoredModules() {
		// Remove any ignored modules
		super.removeIgnoredModules();
		for (Iterator it=moduleList.iterator(); it.hasNext();) {
			if (((Module)it.next()).getIgnore()) it.remove();
		}
	}

	int getNumModules() {
		return moduleList.size();
	}
	
	public Iterator getModules() {
		Collections.sort(moduleList);
		return moduleList.iterator();
	}


}
