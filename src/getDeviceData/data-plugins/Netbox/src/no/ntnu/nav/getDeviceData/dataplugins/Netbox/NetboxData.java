package no.ntnu.nav.getDeviceData.dataplugins.Netbox;

import java.util.*;

import no.ntnu.nav.logger.*;
import no.ntnu.nav.getDeviceData.Netbox;
import no.ntnu.nav.getDeviceData.dataplugins.Device.Device;

/**
 * Describes a single netbox.
 */

public class NetboxData extends Device
{
	// 300 second difference minimum before we change uptime
	public static final double DELTA = 300.0;
	public static final double EVENT_DELTA = 3600.0;

	private int deviceid;

	private Netbox nb;
	private String sysname;
	private String upsince;
	private double uptime = 0;
	//private long curTime;
	//private long baseTime;
	private Set vtpVlanSet = new HashSet();

	//public long u1,u2;

	/**
	 * Constructor.
	 */
	protected NetboxData(String serial, String hw_ver, String fw_ver, String sw_ver, Netbox nb)
	{
		super(serial, hw_ver, fw_ver, sw_ver);
		this.nb = nb;
		//curTime = System.currentTimeMillis();
	}

	/**
	 * Set the sysname of the netbox.
	 */
	public void setSysname(String sysname) {
		this.sysname = sysname;
	}

	/*
	public void setSerial(String serial) {
		super.setSerial(serial);
		new RuntimeException("Setting serial: " + serial + " (devid: " + getDeviceid()+ ")").printStackTrace(System.err);
	}
	*/

	/**
	 * Set the uptime in timerticks (100 ticks per second).
	 */
	public void setUptimeTicks(long ticks) {
		long baseTime = System.currentTimeMillis();
		uptime = ticksToUptime(ticks, baseTime);
	}

	/**
	 * Set the uptime in seconds since the epoch.
	 */
	public void setUptime(double uptime) {
		//long baseTime = System.currentTimeMillis();
		this.uptime = uptime;
	}

	private static double ticksToUptime(long ticks, long baseTime) {
		double uptime = (baseTime - (ticks * 10)) / 1000.0;
		return uptime;
	}

	private static long uptimeToTicks(double uptime) {
		long curTime = System.currentTimeMillis();
		long ticks = (long) ((curTime - (uptime * 1000)) / 10);
		return ticks;
	}

	// Doc in parent
	protected void setDeviceid(int i) { super.setDeviceid(i); }
	public int getDeviceid() { return super.getDeviceid(); }
	public String getDeviceidS() { return super.getDeviceidS(); }

	void setUpsince(String upsince) { this.upsince = upsince; }

	Netbox getNetbox() { return nb; }
	String getSysname() { return sysname; }
	String getUpsince() { return upsince; }
	long getTicks() { return uptimeToTicks(getUptime()); }
	//double getUptime() { return uptime - (System.currentTimeMillis()-baseTime)/1000.0; }
	double getUptime() { return uptime; }

	/**
	 * Add a VTP vlan to the netbox.
	 */
	public void addVtpVlan(int vtpVlan) {
		if (vtpVlan > 0 && vtpVlan <= 999) {
			vtpVlanSet.add(""+vtpVlan);
		}
	}
	Iterator vtpVlanIterator() {
		return vtpVlanSet.iterator();
	}
	Set vtpVlanDifference(NetboxData nd) {
		Set diff = new HashSet(vtpVlanSet);
		diff.removeAll(nd.vtpVlanSet);
		return diff;
	}

	// Doc in parent
	protected boolean hasEmptySerial() { return super.hasEmptySerial(); }

	/**
	 * Returns true if the uptimeDelta is less than DELTA.
	 */
	public boolean equalsUptime(NetboxData n) {
		return uptimeDelta(n) < DELTA;
	}

	/**
	 * Calculate the difference in uptime between this unit and the
	 * given, in seconds. It is assumed that the counter (at 100
	 * ticks/second) is 32 bit, and if the difference taking this into
	 * account is less than one day we will assume the value has not
	 * wrapped.
	 */
	public double uptimeDelta(NetboxData n) {
		// The counter is 32 bits, 100 ticks/sec, thus we must take care when the value wraps
		// If the delta is bigger than 2^32 - 1 day we assume the value has wrapped

		long wrapVal = (1L<<32)-1;
		long wrapDelta = wrapVal - (24 * 3600 * 100);

		long ticks = getTicks();
		long nticks = n.getTicks();

		// Wrap values in case they are already above the limit; we are only interested in the delta
		long up = ticks - wrapVal * (ticks / wrapVal);
		long nup = nticks - wrapVal * (nticks / wrapVal);

		long d = Math.abs(up - nup);

		/*
		System.err.println("ticks    : " + ticks);
		System.err.println("n.ticks  : " + n.ticks);
		System.err.println("wrapVal  : " + wrapVal);
		System.err.println("wrapDelta: " + wrapDelta);
		System.err.println("up       : " + up);
		System.err.println("nup      : " + nup);
		System.err.println("d        : " + (d));
		System.err.println("w-d      : " + (wrapVal-d));
		*/

		if (d > wrapDelta) {
			// Value has wrapped
			Log.d("UPTIME_DELTA", "Uptime wrapped for netbox("+nb.getNetboxid()+"): " + nb.getSysname());
			d = wrapVal - d;
		}
		return d / 100.0;
	}

	public boolean equalsNetboxData(NetboxData n) {
		return (getDeviceid() == n.getDeviceid() &&
				(sysname == null || sysname.equals(n.sysname)) &&
				(uptime == 0 || equalsUptime(n)));
	}

	// Override to avoid Netbox/Module fighting over fields
	public boolean equalsDevice(Device d) {
		if (!(d instanceof NetboxData)) {
			if (d.getHwVer() != null) setHwVer(d.getHwVer());
			if (d.getFwVer() != null) setFwVer(d.getFwVer());
			if (d.getSwVer() != null) setSwVer(d.getSwVer());
		}
		return super.equalsDevice(d);
	}
	
	public boolean equals(Object o) {
		return (o instanceof NetboxData && 
						equalsNetboxData((NetboxData)o) &&
						super.equals(o));
	}

	public String toString() { return getSysname() + ", " + super.toString(); }

}
