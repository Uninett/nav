package no.ntnu.nav.getDeviceData;

import java.util.Set;

/**
 * <p>
 * Describes a Netbox.
 * </p>
 */

public interface Netbox
{
	public int getDeviceid();
	public int getNetboxid();
	public String getNetboxidS();
	public String getIp();
	public String getCommunityRo();
	public String getType();
	public String getSysname();
	public String getCat();
	public int getSnmpMajor();
	public String getSnmpagent();

	/**
	 * Returns the number of modules in the stack of which this netbox
	 * is a member; or 1 if it is not part of a stack.
	 */
	public int getNumInStack();

	/**
	 * <p> Takes as input an array of oidkeys, and returns true if this
	 * netbox supports any of the given oidkeys.  </p>
	 *
	 * @param oidkeys Oidkeys to check
	 * @return true if netbox supports any of the given oidkeys
	 */
	public boolean isSupportedOids(String[] oidkeys);

	/**
	 * <p> Takes as input an array of oidkeys, and returns true if this
	 * netbox supports all of the given oidkeys.  </p>
	 *
	 * @param oidkeys Oidkeys to check
	 * @return true if netbox supports all of the given oidkeys
	 */
	public boolean isSupportedAllOids(String[] oidkeys);

	/**
	 * <p> Takes as input an array of oidkeys, and returns the set of
	 * oidkeys not supported by this netbox.  </p>
	 *
	 * @param oidkeys Oidkeys to check
	 * @return the set of oidkeys not supported by this netbox
	 */
	public Set oidsNotSupported(String[] oidkeys);

	/**
	 * <p> Check if the OID for the given key is ready to be
	 * fetched. Since different OID's, or even equal OID's, but on
	 * different types of devices, can have different query frequencies,
	 * is it necessary to do this check before attempting to query the
	 * device.  </p>
	 *
	 * <p> Note that the {@link #getOid getOid} method does this check
	 * automatically, thus normally it should not be necessary to call
	 * this method directly.  </p>
	 *
	 * @param key The key for the OID
	 * @return true if the OID is ready to be quieried
	 */
	public boolean canGetOid(String key);

	/**
	 * <p> Get the OID for the given key; this method will return null
	 * if the OID is not ready to be fetched.  </p>
	 *
	 * @param key The OID key
	 * @return the OID for the given key, or null if the OID is not ready to be fetched
	 */
	public String getOid(String key);


	/**
	 * <p> Get the OID for the given key without checking if it
	 * scheduled for fetching.  </p>
	 *
	 * @param key The OID key
	 * @return the OID for the given key, or null if the key is not supported
	 */
	public String getOidNoCheck(String key);

	/**
	 * <p> Schedule the given OID to run again in <i>delay</i> seconds. </p>
	 *
	 * @param key The OID key
	 * @param delay The schdule delay in seconds
	 */
	public void scheduleOid(String key, long delay);

	/**
	 * <p> Store a number in this netbox object. </p>
	 */
	public void set(String k, int n);

	/**
	 * <p> Retrieve a number previously stored in this netbox
	 * object. </p>
	 */
	public int get(String k);

	/**
	 * <p>Get a key which uniquely identifies this netbox. Currently
	 * the netboxid is returned. </p>
	 *
	 * @return the netboxid
	 */
	public String getKey();

}
