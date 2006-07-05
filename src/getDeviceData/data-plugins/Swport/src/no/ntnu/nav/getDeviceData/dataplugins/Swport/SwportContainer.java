package no.ntnu.nav.getDeviceData.dataplugins.Swport;

import java.util.*;

import no.ntnu.nav.getDeviceData.dataplugins.*;
import no.ntnu.nav.getDeviceData.dataplugins.Module.Module;
import no.ntnu.nav.getDeviceData.dataplugins.Module.ModuleContainer;
import no.ntnu.nav.logger.Log;

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
 * <p> For storing data the device plugin should request an {@link
 * SwModule SwModule} from the {@link #swModuleFactory
 * swModuleFactory} method for each module, giving the module
 * number. For each switch port on the module an {@link Swport Swport}
 * object should be requested.  </p>
 *
 * @see SwportHandler
 */

public class SwportContainer extends ModuleContainer implements DataContainer {

	public static final int PRIORITY_SWPORT = 20;

	private SwportHandler swh;
	private List swModuleList = new ArrayList();
	private Map swportMap = new HashMap();
	private Set ignoreSet = new HashSet();

	protected SwportContainer(SwportHandler swh) {
		super(null);
		this.swh = swh;
	}

	/**
	 * Get the name of the container; returns the string SwportContainer
	 */
	public String getName() {
		return "SwportContainer";
	}

	// Doc in parent
	public int getPriority() {
		return PRIORITY_SWPORT;
	}

	/**
	 * Get a data-handler for this container; this is a reference to the
	 * SwportHandler object which created the container.
	 */
	public DataHandler getDataHandler() {
		return swh;
	}

	/**
	 * Returns true if this SwportContainer already knows about the
	 * specified ifindex.
	 */
	public boolean containsIfindex(String ifindex) {
		return swportMap.containsKey(ifindex);
	}

	Swport createOrGetSwport(String ifindex) {
		if (swportMap.containsKey(ifindex)) {
			return (Swport)swportMap.get(ifindex);
		}
		Swport swp = new Swport(ifindex);
		swportMap.put(ifindex, swp);
		return swp;
	}

	public Iterator swportIterator() {
		return swportMap.values().iterator();
	}

	/**
	 * <p>
	 * Since the ifIndex number is unique on a Netbox, this method can be used to get an Swport directly if only
	 * the ifIndex is know, but not the module number.
	 * </p>
	 *
	 * <p> If no Swport with the given ifindex exists it will be
	 * created, but not assigned to a module. The Swport is assigned to
	 * a module when the {@link SwModule#swportFactory
	 * SwModule.swportFactory()} method is called; if an Swport is not
	 * assigned to a module it will automatically be assigned to module
	 * 1.  </p>
	 *
	 * @param ifindex The ifindex of the Swport to get
	 * @return an Swport with the given ifindex
	 */
	public Swport swportFactory(String ifindex) {
		return createOrGetSwport(ifindex);
	}

	/**
	 * Specify that the swport for the given ifindex should be ignored
	 * (not inserted into the database).
	 */
	public void ignoreSwport(String ifindex) {
		ignoreSet.add(ifindex);
	}

	boolean getIgnoreSwport(String ifindex) {
		return ignoreSet.contains(ifindex);
	}

	/**
	 * Return an SwModule object which is used to describe one switch module.
	 */
	public SwModule swModuleFactory(int module) {
		Log.d("SwPortHandler", "SWMODULE-FACTORY", "Asked to create module " + module);
		module = translateModule(module);
		SwModule m = new SwModule(module, this);
		int k;
		if ( (k=swModuleList.indexOf(m)) >= 0) {
			m = (SwModule)swModuleList.get(k);
			Log.d("SwPortHandler", "SWMODULE-FACTORY", "Got existing module " + module + " (" + m +")");
		} else {
			addSwModule(m);
			Log.d("SwPortHandler", "SWMODULE-FACTORY", "Created module " + module + " (" + m +")");
		}
		return m;
	}

	/**
	 * Add the switch module to the internal switch module list.
	 *
	 * @param m The switch module to add
	 */
	protected void addSwModule(SwModule m) {
		// Also add it to the parent
		addModule(m);
		swModuleList.add(m);
	}
	
	// Doc in parent
	public boolean isCommited() {
		return super.isCommited();
	}

	// Doc in parent
	protected void removeIgnoredModules() {
		// Remove any ignored modules
		super.removeIgnoredModules();
		for (Iterator it=swModuleList.iterator(); it.hasNext();) {
			if (((SwModule)it.next()).getIgnore()) it.remove();
		}
	}

	// Assign any module-less swports to a module
	void assignSwportsWithoutModule() {
		List l = new ArrayList();
		for (Iterator it = swportMap.values().iterator(); it.hasNext();) {
			Swport swp = (Swport)it.next();
			if (!swp.isAssignedToModule() && !getIgnoreSwport(swp.getIfindex())) l.add(swp);
		}

		// Only create SwModule if it contains any swports
		if (!l.isEmpty()) {
			Module m = (Module)getSupervisorModule();
			SwModule swm = swModuleFactory(m.getModule());
			for (Iterator it = l.iterator(); it.hasNext();) swm.addSwport((Swport)it.next());
		}

		// Ignore any empty modules
		for (Iterator it=swModuleList.iterator(); it.hasNext();) {
			SwModule swm = (SwModule)it.next();
			boolean ignore = true;
			for (Iterator swpit=swm.getSwports(); swpit.hasNext() && ignore;) {
				if (!getIgnoreSwport(((Swport)swpit.next()).getIfindex())) ignore = false;
			}
			if (ignore) swm.ignore();
		}
		removeIgnoredModules();

	}

	Iterator getSwModules() {
		Collections.sort(swModuleList);
		return swModuleList.iterator();
	}


}
