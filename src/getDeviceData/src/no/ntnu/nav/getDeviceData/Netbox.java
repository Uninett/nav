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
	public String getTypegroup();
	public String getType();
	public String getSysname();
	public String getCat();
	public int getSnmpMajor();
	public String getSnmpagent();

	/**
	 * <p> Check if the OID for the given key is ready to be
	 * quiered. Since different OID's, or even equal OID's, but on
	 * different types of devices, can have different query frequencies,
	 * this method should be called before attempting to query the
	 * device. </p>
	 *
	 * <p> Note that when this method is called with a key and returns
	 * true it is assumed the OID will be quiered in this run. </p>
	 *
	 * @param key The key for the OID
	 * @return if the OID is ready to be quieried
	 */
	public boolean isReadyOid(String key);

	/**
	 * Get the OID for the given key.
	 *
	 * @param key The OID key
	 * @return the OID for the given key
	 */
	public String getOid(String key);

}
