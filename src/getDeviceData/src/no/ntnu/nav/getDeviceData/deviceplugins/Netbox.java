package no.ntnu.nav.getDeviceData.deviceplugins;

/**
 * <p>
 * Describes a Netbox.
 * </p>
 */ 
public interface Netbox
{
	public String getNetboxid();
	public String getIp();
	public String getCommunityRo();
	public String getTypegroup();
	public String getType();
	public String getSysname();
	public String getCat();
	public int getSnmpMajor();
	public String getSnmpagent();
}
