package no.ntnu.nav.getDeviceData.dataplugins.Netbox;

import java.util.Map;
import java.util.HashMap;
import java.util.Iterator;

import no.ntnu.nav.getDeviceData.Netbox;
import no.ntnu.nav.getDeviceData.dataplugins.Device.Device;

/**
 * Describes a single netbox.
 */

public class NetboxData extends Device
{
	private int deviceid;

	private Netbox nb;
	private String type;
	private String sysname;

	/**
	 * Constructor.
	 */
	protected NetboxData(String serial, String hw_ver, String sw_ver, Netbox nb, String type, String sysname)
	{
		super(serial, hw_ver, sw_ver);
		this.nb = nb;
		this.type = type;
		this.sysname = sysname;
	}

	// Doc in parent
	protected void setDeviceid(int i) { super.setDeviceid(i); }
	protected int getDeviceid() { return super.getDeviceid(); }
	protected String getDeviceidS() { return super.getDeviceidS(); }

	Netbox getNetbox() { return nb; }
	String getType() { return type; }
	String getSysname() { return sysname; }

	// Doc in parent
	protected boolean hasEmptySerial() { return super.hasEmptySerial(); }

	public boolean equalsNetboxData(NetboxData n) {
		return (getDeviceid() == n.getDeviceid() &&
						type.equals(n.type) &&
						sysname.equals(n.sysname));
	}
	
	public boolean equals(Object o) {
		return (o instanceof NetboxData && 
						equalsNetboxData((NetboxData)o) &&
						super.equals(o));
	}

	public String toString() { return getSysname(); }

}
