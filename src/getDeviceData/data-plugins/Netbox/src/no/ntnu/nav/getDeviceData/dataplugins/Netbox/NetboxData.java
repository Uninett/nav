package no.ntnu.nav.getDeviceData.dataplugins.Netbox;

import java.util.Map;
import java.util.HashMap;
import java.util.Iterator;

import no.ntnu.nav.logger.*;
import no.ntnu.nav.getDeviceData.Netbox;
import no.ntnu.nav.getDeviceData.dataplugins.Device.Device;

/**
 * Describes a single netbox.
 */

public class NetboxData extends Device
{
	// 1 second difference minimum before we change uptime
	private static final double DELTA = 1.0;
	private int deviceid;

	private Netbox nb;
	private String sysname;
	private String upsince;
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
	public void setUptimeTicks(long ticks) {
		double d = System.currentTimeMillis() - (ticks * 10);
		setUptime(d / 1000);
	}

	/**
	 * Set the uptime in seconds since the epoch.
	 */
	public void setUptime(double uptime) {
		this.uptime = uptime;
	}

	// Doc in parent
	protected void setDeviceid(int i) { super.setDeviceid(i); }
	protected int getDeviceid() { return super.getDeviceid(); }
	protected String getDeviceidS() { return super.getDeviceidS(); }

	void setUpsince(String upsince) { this.upsince = upsince; }

	Netbox getNetbox() { return nb; }
	String getSysname() { return sysname; }
	String getUpsince() { return upsince; }
	double getUptime() { return uptime; }

	// Doc in parent
	protected boolean hasEmptySerial() { return super.hasEmptySerial(); }

	public boolean equalsUptime(NetboxData n) {
		return Math.abs(uptime - n.uptime) < DELTA;
	}

	public boolean equalsNetboxData(NetboxData n) {
		return (getDeviceid() == n.getDeviceid() &&
						(sysname == null || sysname.equals(n.sysname)) &&
						equalsUptime(n));
	}
	
	public boolean equals(Object o) {
		return (o instanceof NetboxData && 
						equalsNetboxData((NetboxData)o) &&
						super.equals(o));
	}

	public String toString() { return getSysname(); }

}
