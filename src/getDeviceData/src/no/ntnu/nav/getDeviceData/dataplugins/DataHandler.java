package no.ntnu.nav.getDeviceData.dataplugins;

import java.util.*;

import no.ntnu.nav.getDeviceData.Netbox;

/**
 * <p> The DataHandler interface must be implemented by all data
 * plugin modules to getDeviceData; its purpose is to provide an
 * interface for device plugins to store collected data, and then
 * store said data in the database. </p>
 *
 * <b>Step-by-step guide for writing a data plugin</b>
 * <p>
 * <ol>
 *  <li>Create a class in package {@link no.ntnu.nav.getDeviceData.dataplugins dataplugins} which
 *      implement the {@link DataHandler DataHandler} interface
 *      (found in package no.ntnu.nav.getDeviceData.dataplugins).
 *      Look at one of the existing device plugin modules for an example.
 *  </li>
 *  <li>Implement the {@link #init init()} method. The method will typically fetch initial data from the database
 *      used for comparing with collected data as to only update the database when values change.
 *  </li>
 *  <li>Implement the {@link #dataContainerFactory dataContainerFactory()} method. It should return an object implementing the
 *      {@link no.ntnu.nav.getDeviceData.dataplugins.DataContainer DataContainer} interface. This is
 *      the interface presented to the device plugins for storing
 *      collected data. See the {@link no.ntnu.nav.getDeviceData.dataplugins.DataContainer DataContainer}
 *      doc for more information.
 *  </li>
 *  <li>Implement the {@link #handleData handleData()} method. The arguments are the Netbox the data was collected from
 *      along with an object returned from the {@link #dataContainerFactory dataContainerFactory()} method. The plugin should now
 *      store the collected data in the database.
 *  </li>
 *  <li>Compile the plugin to a JAR file. Again look at an existing data plugin module for
 *      an example. The build.xml file will need to be updated with the new name for the JAR file,
 *      and the Plugin-class with the name of the class implementing the DataHandler interface.
 *  </li>
 *  <li>Copy the JAR file into the data-plugin directory of getDeviceData. It will automatically
 *      be loaded; if an older copy was overwritten getDeviceData must be restarted before the
 *      changes take effect.
 *  </li>
 * </ol>
 *
 * <b>The reason for data plugins</b>
 *
 * <p> The idea behind data plugins is to provide a general way for
 * device handlers to store collected values in the
 * database. Typically there will be several different plugins
 * collecting the same data from different types of equipment, and it
 * would be wasteful if all device handlers must implement their own
 * routines for updating the database.  </p>
 *
 * <p> A data plugin provides an interface for device handlers to
 * store collected data and is then responsible for updating the
 * database with said data; updating if possible, inserting or
 * deleting otherwise. The device handlers should not have to care
 * about the previous state of the device they are collecting data
 * from; only the current state is important. Writing a device plugin
 * then becomes a much easier process. </p>
 *
 * @see DataContainers
 * @see DataContainer
 */

public interface DataHandler {

	/**
	 * Do init. Usually used for fetching initial data from the database and
	 * store it in the given persistent storage object.
	 *
	 * @param persistentStorage A map the plugin can use for storing data between succesive calls
	 * @param changedDeviceids Set of deviceids which have changed (been added)
	 */
	public void init(Map persistentStorage, Set changedDeviceids);

	/**
	 * Return a DataContainer object used to return data to this
	 * DataHandler.
	 *
	 * @return a DataContainer used for storing data collected by a device plugin
	 */
	public DataContainer dataContainerFactory();

	/**
	 * Store the data in the DataContainer in the database.
	 *
	 * @param nb The Netbox the data was collected from
	 * @param dc The collected data
	 * @param changedDeviceids set of new/changed deviceids by this DataHandler
	 */
	public void handleData(Netbox nb, DataContainer dc, Set changedDeviceids);

}
