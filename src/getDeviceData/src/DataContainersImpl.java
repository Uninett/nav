/**
 * <p>
 * Implementation DataContainer interface
 * </p>
 */

import java.util.*;

import no.ntnu.nav.logger.*;
import no.ntnu.nav.getDeviceData.Netbox;
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
	Map callDataHandlers(Netbox nb) {
		Map changedDeviceids = new HashMap();

		// Make sure we call the containers in the correct order
		List containersSorted = new ArrayList(containers.values());
		Collections.sort(containersSorted, new Comparator() {
				public int compare(Object o1, Object o2) {
					if (!(o1 instanceof DataContainer) || !(o2 instanceof DataContainer)) return 0;
					return new Integer(((DataContainer)o2).getPriority()).compareTo(new Integer(((DataContainer)o1).getPriority()));
				}
			});

		// Print for debug
		String order = "";
		for (Iterator i = containersSorted.iterator(); i.hasNext();) {
			order += ((DataContainer)i.next()).getName()+(i.hasNext()?",":"");
		}
		Log.d("DataContainers", "CALL_DATA_HANDLERS", "Calling data handlers: " + order.substring(0,order.length()-1));

		for (Iterator i = containersSorted.iterator(); i.hasNext();) {
			DataContainer dc = (DataContainer)i.next();
			DataHandler dh = dc.getDataHandler();
			if (dh == null) {
				Log.w("DATA_CONTAINERS_IMPL", "CALL_DATA_HANDLERS", "DataHandler is null for DataContainer: " + dc);
				continue;
			}
			Map m = new HashMap();
			dh.handleData(nb, dc, m);
			changedDeviceids.putAll(m);
		}
		return changedDeviceids;
	}

}
