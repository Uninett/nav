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
	private static final double DELTA = 0.00001;
	private int deviceid;

	private Netbox nb;
	private String sysname;
	private double uptime;

	/**
	 * Constructor.
	 */
	protected NetboxData(String serial, String hw_ver, String sw_ver, Netbox nb)
	{
		super(serial, hw_ver, sw_ver);
		this.nb = nb;
	}

	/**
	 * Set the sysname of the netbox.
	 */
	public void setSysname(String sysname) {
		this.sysname = sysname;
	}

	/**
	 * Set the uptime in timerticks (100 ticks per second).
	 */
	public void setUptime(double uptime) {
		this.uptime = uptime;
	}

	// Doc in parent
	protected void setDeviceid(int i) { super.setDeviceid(i); }
	protected int getDeviceid() { return super.getDeviceid(); }
	protected String getDeviceidS() { return super.getDeviceidS(); }

	Netbox getNetbox() { return nb; }
	String getSysname() { return sysname; }
	double getUptime() { return uptime; }

	// Doc in parent
	protected boolean hasEmptySerial() { return super.hasEmptySerial(); }

	public boolean equalsNetboxData(NetboxData n) {
		return (getDeviceid() == n.getDeviceid() &&
						sysname.equals(n.sysname) &&
						Math.abs(uptime - n.uptime) < DELTA);
	}
	
	public boolean equals(Object o) {
		return (o instanceof NetboxData && 
						equalsNetboxData((NetboxData)o) &&
						super.equals(o));
	}

	public String toString() { return getSysname(); }

}
