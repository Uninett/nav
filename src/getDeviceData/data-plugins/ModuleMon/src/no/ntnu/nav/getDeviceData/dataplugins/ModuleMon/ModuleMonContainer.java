package no.ntnu.nav.getDeviceData.dataplugins.ModuleMon;

import java.util.*;

import no.ntnu.nav.util.*;
import no.ntnu.nav.getDeviceData.dataplugins.*;

/**
 * <p>
 * The interface to device plugins for storing collected data.
 * </p>
 *
 * @see ModuleMonHandler
 */

public class ModuleMonContainer implements DataContainer {

	private ModuleMonHandler mmh;
	private boolean commit = false;

	private MultiMap queryIfindices;
	private Set ifindexActiveSet = new HashSet();

	protected ModuleMonContainer(ModuleMonHandler mmh, MultiMap queryIfindices) {
		this.mmh = mmh;
		this.queryIfindices = queryIfindices;
	}

	/**
	 * Get the name of the container; returns the string ModuleMonContainer
	 */
	public String getName() {
		return "ModuleMonContainer";
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
	 * <p> Register that the given ifindex is active on the switch; the
	 * module which owns the ifindex is considered up.  </p>
	 *
	 * @param ifindex The active ifindex
	 */
	public void ifindexActive(String ifindex) {
		ifindexActiveSet.add(ifindex);
	}

	public void commit() {
		commit = true;		
	}

	boolean isCommited() {
		return commit;
	}

	Iterator getActiveIfindices() {
		return ifindexActiveSet.iterator();
	}


}
