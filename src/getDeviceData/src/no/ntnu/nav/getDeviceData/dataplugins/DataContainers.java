package no.ntnu.nav.getDeviceData.dataplugins;

/**
 * Each DataContainer must have an unique name, and DataContainer
 * objects can be retrieved using the {@link #getContainer
 * getContainer()} method with the name of the DataContainer as
 * argument. See the documentation for the class implementing
 * DataContainer in each data plugin for getting the names.
 *
 * @see DataContainer
 */

public interface DataContainers {

	/**
	 * Return the container assosiated with name, or null if no such container exists.
	 *
	 * @param name The name of the DataContainer
	 * @return the DataContainer associated with name, or null if no such container exists.
	 */
	public DataContainer getContainer(String name);

}
