package no.ntnu.nav.getDeviceData.dataplugins;

/**
 * Used by DeviceHandler plugins to return data to DataHandlers. The methods
 * provided by the actuall object are not specified; check the documentation
 * for each plugin.
 */

public interface DataContainer {
	
	/**
	 * Get the name of the container.
	 */
	public String getName();

	/**
	 * Get a data-handler for this container; this is typically a reference
	 * to the same object which created the container.
	 */
	public DataHandler getDataHandler();

}
