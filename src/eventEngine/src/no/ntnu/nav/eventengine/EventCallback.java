package no.ntnu.nav.eventengine;

/**
 * Interface for getting a callback from DeviceDB.
 */

import java.util.*;

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
