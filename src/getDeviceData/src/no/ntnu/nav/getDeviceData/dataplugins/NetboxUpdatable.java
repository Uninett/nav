package no.ntnu.nav.getDeviceData.dataplugins;

/**
 * <p> Allowed some items of a Netbox to be updated. The Netbox object
 * can be casted to this class, and by doing the cast the intention to
 * do updates it is made explicit.  </p>
 */ 
public interface NetboxUpdatable
{

	/**
	 * Return the typeid for the type. Normally only required if you
	 * want to make updates to the database directly.
	 */
	public String getTypeid();

	/**
	 * <p> Remove the netbox; calling this method guarantees that no
	 * other plugins will process it. This method is typically used if
	 * the netbox is deleted from the database.  </p>
	 *
	 * @param updateNetboxes Specifies if a new netbox has been added to
	 * the database and gDD needs to update itself.
	 *
	 */
	public void remove(boolean updateNetboxes);

}
