package no.ntnu.nav.getDeviceData.dataplugins.Gwport;

import java.util.*;

import no.ntnu.nav.getDeviceData.dataplugins.*;
import no.ntnu.nav.getDeviceData.dataplugins.Module.ModuleContainer;

/**
 * <p> The interface to device plugins for storing collected data.
 * </p>
 *
 * <p> A router is seen as a collection of modules, each of which has
 * a number of gwports. Each gwport can be on multiple prefixes;
 * however, normally only one. Each prefix has a single vlan. </p>
 *
 * <p> For storing data the device plugin should request a {@link
 * GwModule GwModule} from the {@link #gwModuleFactory
 * gwModuleFactory} method for each module, giving the module number,
 * serial number, and, if available, the hardware and software
 * version. </p>
 *
 * @see GwportHandler
 */

public class GwportContainer extends ModuleContainer implements DataContainer {

	private GwportHandler gwh;
	private List gwModuleList = new ArrayList();

	protected GwportContainer(GwportHandler gwh) {
		super(null);
		this.gwh = gwh;
	}

	/**
	 * Get the name of the container; returns the string GwportContainer
	 */
	public String getName() {
		return "GwportContainer";
	}

	/**
	 * Get a data-handler for this container; this is a reference to the
	 * GwportHandler object which created the container.
	 */
	public DataHandler getDataHandler() {
		return gwh;
	}

	/**
	 * Return an GwModule object which is used to describe one router module.
	 */
	public GwModule gwModuleFactory(int module) {
		GwModule m = new GwModule(module);
		int k;
		if ( (k=gwModuleList.indexOf(m)) >= 0) {
			m = (GwModule)gwModuleList.get(k);
		} else {
			addGwModule(m);
		}
		return m;
	}

	/**
	 * Return an GwModule object which is used to describe one router
	 * module. Note that serial, hw_ver and sw_ver are ignored if the
	 * module already exists.
	 */
	public GwModule gwModuleFactory(String serial, String hw_ver, String sw_ver, int module) {
		GwModule m = new GwModule(serial, hw_ver, sw_ver, module);
		int k;
		if ( (k=gwModuleList.indexOf(m)) >= 0) {
			m = (GwModule)gwModuleList.get(k);
		} else {
			addGwModule(m);
		}
		return m;
	}

	/**
	 * Add the router module to the internal router module list.
	 *
	 * @param m The router module to add
	 */
	protected void addGwModule(GwModule m) {
		// Also add it to the parent
		addModule(m);
		gwModuleList.add(m);
	}

	// Doc in parent
	protected boolean isCommited() {
		return super.isCommited();
	}

	Iterator getGwModules() {
		Collections.sort(gwModuleList);
		return gwModuleList.iterator();
	}


}
