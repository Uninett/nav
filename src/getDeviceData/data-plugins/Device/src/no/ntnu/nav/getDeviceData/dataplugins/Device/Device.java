package no.ntnu.nav.getDeviceData.dataplugins.Device;

/**
 * Describes a single device. Normally this class will be inherited.
 */

public class Device
{
	private int deviceid;

	private String serial;
	private String hw_ver;
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
	protected Device(String serial, String hwVer, String swVer) {
		setSerial(serial);
		this.hw_ver = hwVer;
		this.sw_ver = swVer;
	}

	/**
	 * Return the deviceid.
	 */
	protected int getDeviceid() { return deviceid; }

	/**
	 * Return the deviceid as a String.
	 */
	protected String getDeviceidS() { return deviceid == 0 ? null : String.valueOf(getDeviceid()); }

	/**
	 * Set the deviceid of the physical device.
	 */
	protected void setDeviceid(int i) { deviceid = i; }

	void setDeviceid(String s) { deviceid = Integer.parseInt(s); }
	
	String getSerial() { return serial; }
	String getHwVer() { return hw_ver; }
	String getSwVer() { return sw_ver; }

	boolean getIgnore() { return ignore; }

	/**
	 * Set the the serial number of the physical device.
	 */
	public void setSerial(String serial) {
		if (serial != null && serial.length() > 0 && !serial.equals("0")) {
			this.serial = serial;
		} else {
			this.serial = null;
		}
	}

	/**
	 * Set the the hardware version number of the physical device.
	 */
	public void setHwVer(String hwVer) { this.hw_ver = hwVer; }

	/**
	 * Set the the software version number of the physical device.
	 */
	public void setSwVer(String swVer) { this.sw_ver = swVer; }

	/**
	 * Return true if this device does not have a serial.
	 */
	protected boolean hasEmptySerial() {
		return (serial == null ||
						serial.length() == 0);
	}

	public boolean equalsDevice(Device d) {
		return ((serial == null || serial.equals(d.serial)) &&
						(hw_ver == null || hw_ver.equals(d.hw_ver)) &&
						(sw_ver == null || sw_ver.equals(d.sw_ver)));
	}

	public boolean equals(Object o) {
		return (o instanceof Device &&
						serial != null &&
						serial.equals(((Device)o).serial));
	}

	public String toString() { return "serial="+serial+" hw_ver="+hw_ver+" sw_ver="+sw_ver; }

}
