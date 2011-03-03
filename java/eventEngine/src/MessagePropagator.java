
/**
 * MessagePropgator is used for propagating message between internal
 * eventEngine classes.
 *
 */

interface MessagePropagator
{

	/**
	 * Ask device handlers to update from DB.
	 */
	public void updateFromDB();

}
