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

	/**
	 * Constructor.
	 */
	protected Device(String serial, String hw_ver, String sw_ver)
	{
		this.serial = serial;
		this.hw_ver = hw_ver;
		this.sw_ver = sw_ver;
	}

	/**
	 * Return the deviceid.
	 */
	protected int getDeviceid() { return deviceid; }

	/**
	 * Return the deviceid as a String.
	 */
	protected String getDeviceidS() { return String.valueOf(getDeviceid()); }

	/**
	 * Set the deviceid of the physical device which this module represents.
	 */
	protected void setDeviceid(int i) { deviceid = i; }

	void setDeviceid(String s) { deviceid = Integer.parseInt(s); }
	
	String getSerial() { return serial; }
	String getHwVer() { return hw_ver; }
	String getSwVer() { return sw_ver; }

	/**
	 * Return true if this device does not have a serial.
	 */
	protected boolean hasEmptySerial() {
		return (serial == null ||
						serial.length() == 0);
	}

	public boolean equalsDevice(Device d) {
		return (serial.equals(d.serial) &&
						hw_ver.equals(d.hw_ver) &&
						sw_ver.equals(d.sw_ver));
	}

	public boolean equals(Object o) {
		return (o instanceof Device &&
						serial != null &&
						serial.equals(((Device)o).serial));
	}

	public String toString() { return "Device deviceid="+deviceid+" serial="+serial+" hw_ver="+hw_ver+" sw_ver="+sw_ver; }

}
