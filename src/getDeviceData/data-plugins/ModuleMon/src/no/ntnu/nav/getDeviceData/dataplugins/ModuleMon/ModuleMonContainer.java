package no.ntnu.nav.getDeviceData.dataplugins.ModuleMon;

import java.util.*;

import no.ntnu.nav.util.*;
import no.ntnu.nav.getDeviceData.Netbox;
import no.ntnu.nav.getDeviceData.dataplugins.*;

/**
 * <p>
 * The interface to device plugins for storing collected data.
 * </p>
 *
 * @see ModuleMonHandler
 */

public class ModuleMonContainer implements DataContainer {

	public static final int PRIORITY_MODULE_MON = PRIORITY_NORMAL;

	private ModuleMonHandler mmh;
	private boolean commit = false;

	private MultiMap queryIfindices;
	private Map moduleToIfindex;
	private Set moduleUpSet = new HashSet();

	protected ModuleMonContainer(ModuleMonHandler mmh, MultiMap queryIfindices, Map moduleToIfindex) {
		this.mmh = mmh;
		this.queryIfindices = queryIfindices;
		this.moduleToIfindex = moduleToIfindex;
	}

	/**
	 * Get the name of the container; returns the string ModuleMonContainer
	 */
	public String getName() {
		return "ModuleMonContainer";
	}

	// Doc in interface
	public int getPriority() {
		return PRIORITY_MODULE_MON;
	}

	/**
	 * Get a data-handler for this container; this is a reference to the
	 * ModuleMonHandler object which created the container.
	 */
	public DataHandler getDataHandler() {
		return mmh;
	}

	/**
	 * <p> Give a list of ifindices to query; these are a random
	 * selection, one from each module on the box.  </p>
	 */
	public Iterator getQueryIfindices(String netboxid) {
		Set s = queryIfindices.get(netboxid);
		if (s != null) return s.iterator();
		return null;
	}

	/**
	 * Reschedule the given netbox for the given module and OID. OID =
	 * null means all OIDs.
	 */
	public void rescheduleNetbox(Netbox nb, String module, String oid) {
		int cnt = nb.get(module);
		if (cnt < 3) {
			if (cnt < 0) cnt = 0;
			nb.set(module, ++cnt);
			long delay;
			switch (cnt) {
			case 1: delay = 30; break;
			case 2: delay = 60; break;
			case 3: delay = 120; break;
			default:
				System.err.println("Error in rescheduleNetbox, cnt="+cnt+", should not happen");
				return;
			}
			nb.scheduleOid(oid, delay);
		}
	}

	/**
	 * <p> Returns the ifindex to ask for the given module.  </p>
	 */
	public String ifindexForModule(String netboxid, String module) {
		Map mm = (Map)moduleToIfindex.get(netboxid);
		return (String)mm.get(module);
	}

	/**
	 * <p> Register that the given module is up on the netbox.
	 * </p>
	 *
	 * @param module The up module
	 */
	public void moduleUp(Netbox nb, String module) {
		moduleUpSet.add(module);
		nb.set(module, 0);
	}

	public void commit() {
		commit = true;		
	}

	boolean isCommited() {
		return commit;
	}

	Iterator getModulesUp() {
		return moduleUpSet.iterator();
	}

	Set getModulesUpSet() {
		return moduleUpSet;
	}


}
