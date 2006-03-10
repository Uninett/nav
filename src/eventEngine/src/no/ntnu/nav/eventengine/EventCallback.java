package no.ntnu.nav.eventengine;

import java.util.*;

/**
 * Interface for getting callbacks from DeviceDB.
 */

public interface EventCallback
{
	/**
	 * Method called by DeviceDB.
	 *
	 * @param ddb Reference to DeviceDB
	 * @param invocationsRemaining Specifies how many remaining callbacks are currently scheduled
	 */
	public void callback(DeviceDB ddb, int invocationsRemaining);

}
