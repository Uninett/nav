package no.ntnu.nav.getDeviceData.dataplugins;

/**
 * <p> Each data handler must include a class which implements
 * DataContainer; this is the interface presented to the device
 * plugins. There is no restriction on how this interface should look;
 * each device plugin will need to cast the given DataHandler object
 * to the actual implementing class in order to gain access to the
 * methods used for storing collected data.  </p>
 *
 * <p> For details on the interface for the data handler plugin in
 * interest, look at the documentation for the class implementing this
 * interface.  </p>
 */

public interface DataContainer {
	
	/**
	 * Get the name of the container.
	 *
	 * @return the name of this DataContainer
	 */
	public String getName();

	/**
	 * Get a data-handler for this container; this is typically a reference
	 * to the same object which created the container.
	 *
	 * @return reference to a DataHandler object which can handle this DataContainer
	 */
	public DataHandler getDataHandler();

}
