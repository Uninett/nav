/**
 * <p>
 * Implementation DataContainer interface
 * </p>
 */

import java.util.*;

import no.ntnu.nav.logger.*;
import no.ntnu.nav.getDeviceData.dataplugins.*;
import no.ntnu.nav.getDeviceData.deviceplugins.*;


public class DataContainersImpl implements DataContainers {

	private Map containers = new HashMap();

	/**
	 * Return the container assosiated with name, or null if no such container exists.
	 */
	public DataContainer getContainer(String name) {
		return (DataContainer)containers.get(name);
	}

	void addContainer(DataContainer dc) {
		String name = dc.getName();
		if (name != null) {
			Log.d("DataContainers", "ADD_CONTAINER", "Added container: " + name);
			containers.put(name, dc);
		}
	}

	/**
	 * Call the handleData() methods of all the DataContainer objects
	 */
	void callDataHandlers(Netbox nb) {
		for (Iterator i = containers.values().iterator(); i.hasNext();) {
			DataContainer dc = (DataContainer)i.next();
			dc.getDataHandler().handleData(nb, dc);
		}
	}

}
