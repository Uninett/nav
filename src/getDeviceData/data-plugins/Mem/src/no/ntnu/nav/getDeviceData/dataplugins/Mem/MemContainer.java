package no.ntnu.nav.getDeviceData.dataplugins.Mem;

import java.util.*;

import no.ntnu.nav.getDeviceData.dataplugins.*;

/**
 * <p>
 * The interface to device plugins for storing collected mem data.
 * </p>
 *
 * @see MemHandler
 */

public class MemContainer implements DataContainer {

	public static final int PRIORITY_MEM = 20;

	public static final String TYPE_MEMORY = "memory";
	public static final String TYPE_FLASH = "flash";

	private MemHandler memh;
	private boolean commit = false;
	private Map memMap = new HashMap();

	protected MemContainer(MemHandler memh) {
		this.memh = memh;
	}

	/**
	 * Get the name of the container; returns the string MemContainer
	 */
	public String getName() {
		return "MemContainer";
	}

	// Doc in parent
	public int getPriority() {
		return PRIORITY_MEM;
	}

	/**
	 * Get a data-handler for this container; this is a reference to the
	 * MemHandler object which created the container.
	 */
	public DataHandler getDataHandler() {
		return memh;
	}

	public void commit() {
		commit = true;		
	}

	/**
	 * Return if the data in this container is commited.
	 */
	public boolean isCommited() {
		return commit;
	}

	public void addMem(String type, String name, long size, long used) {
		String key = type+":"+name;
		Object[] data = new Object[] { type, name, new Long(size), new Long(used) };
		memMap.put(key, data);
	}

	Iterator getMem() {
		return memMap.values().iterator();
	}


}
