package no.ntnu.nav.getDeviceData.dataplugins;

/**
 * <p>
 * Container for DataContainer objects
 * </p>
 */

public interface DataContainers {

	/**
	 * Return the container assosiated with name, or null if no such container exists.
	 */
	public DataContainer getContainer(String name);

}
