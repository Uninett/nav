package no.ntnu.nav.getDeviceData;

import java.util.Set;

/**
 * <p>
 * Describes a Netbox.
 * </p>
 */

public interface Netbox
{
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

}
