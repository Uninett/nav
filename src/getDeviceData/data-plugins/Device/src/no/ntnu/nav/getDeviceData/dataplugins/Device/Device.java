package no.ntnu.nav.getDeviceData.dataplugins.Device;

/**
 * Describes a single device. Normally this class will be inherited.
 */

public class Device
{
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
	 * Set the the firmware version number of the physical device.
	 */
	public void setFwVer(String fwVer) { this.fw_ver = fwVer; }

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
						(fw_ver == null || fw_ver.equals(d.fw_ver)) &&
						(sw_ver == null || sw_ver.equals(d.sw_ver)));
	}

	public boolean equals(Object o) {
		return (o instanceof Device &&
						serial != null &&
						serial.equals(((Device)o).serial));
	}

	public String toString() { return "devid="+deviceid+" serial="+serial+" hw_ver="+hw_ver+" fw_ver="+fw_ver+" sw_ver="+sw_ver; }

}
