package no.ntnu.nav.getDeviceData.dataplugins.Device;

import java.util.*;

/**
 * Describes a single device. Normally this class will be inherited.
 */

public class Device implements Comparable
{
	private static String[] badSerial = {
		"0",
		"0x0E",
		"0x12",
		"1234",
	};
	private static Set badSerials = new HashSet(Arrays.asList(badSerial));

	private int deviceid;

	private String serial;
	private String hw_ver;
	private String fw_ver;
	private String sw_ver;

	protected boolean ignore;

	/**
	 * Constructor.
	 */
	protected Device() {
	}

	/**
	 * Constructor.
	 */
	protected Device(String serial, String hwVer, String fwVer, String swVer) {
		setSerial(serial);
		this.hw_ver = hwVer;
		this.fw_ver = fwVer;
		this.sw_ver = swVer;
	}

	/**
	 * Return the deviceid.
	 */
	public int getDeviceid() { return deviceid; }

	/**
	 * Return the deviceid as a String.
	 */
	public String getDeviceidS() { return deviceid == 0 ? null : String.valueOf(getDeviceid()); }

	/**
	 * Set the deviceid of the physical device.
	 */
	protected void setDeviceid(int i) { deviceid = i; }

	void setDeviceid(String s) {
		deviceid = Integer.parseInt(s.trim());
	}
	
	public String getSerial() { return serial; }
	public String getHwVer() { return hw_ver; }
	public String getFwVer() { return fw_ver; }
	public String getSwVer() { return sw_ver; }

	boolean getIgnore() { return ignore; }

	private boolean isValidSerial(String serial) {
		if (serial == null || serial.length() == 0) return false;
		if (serial.length() <= 4) return false;
		if (badSerials.contains(serial)) return false;

		return true;		
	}

	/**
	 * Set the the serial number of the physical device.
	 */
	public void setSerial(String serial) {
		if (isValidSerial(serial)) {
			this.serial = serial;
		} else {
			this.serial = null;
		}
	}

	/**
	 * Set the the hardware version number of the physical device.
	 */
	public void setHwVer(String hwVer) {
		if (hwVer != null && hwVer.length() > 0) {
			this.hw_ver = hwVer;
		}
	}

	/**
	 * Set the the firmware version number of the physical device.
	 */
	public void setFwVer(String fwVer) {
		if (fwVer != null && fwVer.length() > 0) {
			this.fw_ver = fwVer;
		}
	}

	/**
	 * Set the the software version number of the physical device.
	 */
	public void setSwVer(String swVer) {
		if (swVer != null && swVer.length() > 0) {
			this.sw_ver = swVer;
		}
	}

	/**
	 * Return true if this device does not have a serial.
	 */
	protected boolean hasEmptySerial() {
		return (serial == null ||
						serial.length() == 0);
	}

	void setEqual(Device d) {
		if (serial == null) serial = d.serial;
		if (hw_ver == null) hw_ver = d.hw_ver;
		if (fw_ver == null) fw_ver = d.fw_ver;
		if (sw_ver == null) sw_ver = d.sw_ver;
	}

	public boolean equalsDevice(Device d) {
		return ((serial == null || serial.equals(d.serial)) &&
						(hw_ver == null || hw_ver.equals(d.hw_ver)) &&
						(fw_ver == null || fw_ver.equals(d.fw_ver)) &&
						(sw_ver == null || sw_ver.equals(d.sw_ver)));
	}

	public boolean equals(Object o) {
		return (o instanceof Device &&
						serial != null &&
						serial.equals(((Device)o).serial));
	}

	public int compareTo(Object o) {
		Device d = (Device)o;
		return new Integer(deviceid).compareTo(new Integer(d.deviceid));
	}
	public String toString() { return "devid="+deviceid+" serial="+serial+" hw_ver="+hw_ver+" fw_ver="+fw_ver+" sw_ver="+sw_ver + " ["+super.toString()+"]"; }

}
