package no.ntnu.nav.getDeviceData.dataplugins;

/**
 * Store collected data in the database
 */

import java.util.*;

import no.ntnu.nav.getDeviceData.deviceplugins.Netbox;

public interface DataHandler {

	/**
	 * Do init. Usually used for fetching initial data from the database and
	 * store it in the given persistent storage object.
	 */
	public void init(Map persistentStorage);

	/**
	 * Return a DataContainer object used to return data to this
	 * DataHandler.
	 */
	public DataContainer dataContainerFactory();

	/**
	 * Store the data in the DataContainer in the database.
	 */
	public void handleData(Netbox nb, DataContainer dc);

}
