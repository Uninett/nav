package no.ntnu.nav.getDeviceData;

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
	 * Takes as input an array of oidkeys, and returns true if this
	 * netbox supports any of the given oidkeys.
	 *
	 * @param oidkeys Oidkeys to check
	 * @return true if netbox supports any of the given oidkeys
	 */
	public boolean isSupportedOids(String[] oidkeys);

	/**
	 * <p> Ask permission to fetch the OID for the given key. Since
	 * different OID's, or even equal OID's, but on different types of
	 * devices, can have different query frequencies, this method must
	 * be called before attempting to query the device. </p>
	 *
	 * @param key The key for the OID
	 * @return true if the OID is ready to be quieried
	 */
	public boolean requestOidFetchPermission(String key);

	/**
	 * Get the OID for the given key.
	 *
	 * @param key The OID key
	 * @return the OID for the given key
	 */
	public String getOid(String key);

}
