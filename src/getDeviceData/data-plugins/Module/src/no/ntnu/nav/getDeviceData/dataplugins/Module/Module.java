package no.ntnu.nav.getDeviceData.dataplugins.Module;

import java.util.Map;
import java.util.HashMap;
import java.util.Iterator;

/**
 * Describes a single module. Normally this class will be inherited.
 */

public class Module implements Comparable
{
	private int deviceid;
	private int moduleid;

	private String serial;
	private String hw_ver;
	private String sw_ver;

	private String module;
	private String submodule;

	/**
	 * Constructor.
	 */
	protected Module(String serial, String hw_ver, String sw_ver, String module)
	{
		this.serial = serial;
		this.hw_ver = hw_ver;
		this.sw_ver = sw_ver;
		this.module = module;
		submodule = "";
	}

	int getDeviceid() { return deviceid; }

	/**
	 * Set the deviceid of the physical device which this module represents.
	 */
	protected void setDeviceid(int i) { deviceid = i; }

	void setDeviceid(String s) { deviceid = Integer.parseInt(s); }
	
	/**
	 * Return the moduleid.
	 */
	protected int getModuleid() { return moduleid; }

	/**
	 * Return the moduleid as a String.
	 */
	protected String getModuleidS() { return String.valueOf(moduleid); }

	/**
	 * Set the moduleid of this module.
	 */
	protected void setModuleid(int i) { moduleid = i; }

	void setModuleid(String s) { moduleid = Integer.parseInt(s); }

	String getSerial() { return serial; }
	String getHwVer() { return hw_ver; }
	String getSwVer() { return sw_ver; }

	String getModule() { return module; }
	String getModuleS() { return ((module.length()==1)?" ":"")+getModule(); }

	String getSubmodule() { return submodule; }

	/**
	 * Set the submodule number of this module.
	 */
	public void setSubmodule(String s) { submodule = s; }

	/**
	 * Return a key which identifies this module (currently the module number is returned).
	 */
	protected String getKey() {
		return module;
	}

	public boolean equals(Object o) {
		if (o instanceof Module) {
			Module m = (Module)o;
			return (deviceid == m.deviceid &&
					module.equals(m.module) &&
					submodule.equals(m.submodule));
		}
		return false;
	}
	boolean equalsDevice(Module m) {
		return (serial.equals(m.serial) &&
				hw_ver.equals(m.hw_ver) &&
				sw_ver.equals(m.sw_ver));
	}

	public int compareTo(Object o) {
		Module m = (Module)o;
		try {
			return new Integer(module).compareTo(new Integer(m.getModule()));
		} catch (NumberFormatException e) {}
		return module.compareTo(m.getModule());
	}
	public String toString() { return getModuleS(); }
}
