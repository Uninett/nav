package no.ntnu.nav.getDeviceData.dataplugins.Swport;

import java.util.Map;
import java.util.HashMap;
import java.util.Iterator;

/**
 * Contain Swport-objects
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

	private Map swports = new HashMap();

	Module(String serial, String hw_ver, String sw_ver, String module)
	{
		this.serial = serial;
		this.hw_ver = hw_ver;
		this.sw_ver = sw_ver;
		this.module = module;
		submodule = "";
	}

	int getDeviceid() { return deviceid; }
	void setDeviceid(int i) { deviceid = i; }
	void setDeviceid(String s) { deviceid = Integer.parseInt(s); }
	
	int getModuleid() { return moduleid; }
	String getModuleidS() { return String.valueOf(moduleid); }
	public void setModuleid(int i) { moduleid = i; }
	public void setModuleid(String s) { moduleid = Integer.parseInt(s); }

	String getSerial() { return serial; }
	String getHwVer() { return hw_ver; }
	String getSwVer() { return sw_ver; }

	String getModule() { return module; }
	String getModuleS() { return ((module.length()==1)?" ":"")+getModule(); }

	String getSubmodule() { return submodule; }
	public void setSubmodule(String s) { submodule = s; }

	void addSwport(Swport sd) { swports.put(sd.getPort(), sd); }
	Iterator getSwports() { return swports.values().iterator(); }
	int getSwportCount() { return swports.size(); }
	Swport getSwport(Integer port) { return (Swport)swports.get(port); }

	public Swport swportFactory(Integer port, String ifindex) {
		Swport sw = new Swport(port, ifindex);
		swports.put(port, sw);
		return sw;
	}

	public Swport swportFactory(Integer port, String ifindex, char link, String speed, char duplex, String media, boolean trunk, String portname) {
		Swport sw = new Swport(port, ifindex, link, speed, duplex, media, trunk, portname);
		swports.put(port, sw);
		return sw;
	}


	String getKey() {
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
