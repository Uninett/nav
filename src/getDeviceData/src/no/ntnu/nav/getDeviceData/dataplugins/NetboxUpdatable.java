package no.ntnu.nav.getDeviceData.dataplugins;

/**
 * <p>
 * Allowed some items of a Netbox to be updated.
 * </p>
 */ 
public interface NetboxUpdatable
{
	public void setType(String s);
	public void setSysname(String s);
}
