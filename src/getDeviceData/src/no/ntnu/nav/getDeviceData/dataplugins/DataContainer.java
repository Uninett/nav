package no.ntnu.nav.getDeviceData.dataplugins;

/**
 * <p> Each data handler must include a class which implements
 * DataContainer; this is the interface presented to the device
 * plugins. There is no restriction on which other methods this class
 * can privode; each device plugin will need to cast the given
 * DataContainer object to the actual implementing class in order to
 * gain access to the methods used for storing collected data.  </p>
 *
 * <p> <i>Device plugin developers</i> should look at the documentation for
 * the classes implementing this interface for details on provided
 * methods for the data handler plugins in question. </p>
 */

public interface DataContainer {
	
	/**
	 * Get the name of the container. This must be unique, and is used by device plugins
   * to retrieve a reference to a DataContainer object.
	 *
	 * @return the name of this DataContainer
	 */
	public String getName();

	/**
	 * Get a {@link DataHandler DataHandler} for this container; this is typically a reference
	 * to the same object which created the container.
	 *
	 * @return reference to a DataHandler object which can handle this DataContainer
	 */
	public DataHandler getDataHandler();

	/**
	 * This method must be called after all processing is done to signal
	 * that collection of data completed successfully and old data no
	 * longer present can safely be deleted. After this method is called
	 * it is no longer possible to add new data.
	 */
	public void commit();


}
