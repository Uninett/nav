package no.ntnu.nav.getDeviceData.plugins;

import java.util.Map;
import java.util.HashMap;
import java.util.Iterator;

public class ModuleData implements Comparable
{
	int deviceid;
	int moduleid;

	String serial;
	String hw_ver;
	String sw_ver;

	String module;
	String submodule;

	Map swportData = new HashMap();

	public ModuleData(String serial, String hw_ver, String sw_ver, String module)
	{
		this.serial = serial;
		this.hw_ver = hw_ver;
		this.sw_ver = sw_ver;
		this.module = module;
		submodule = "";
	}

	public int getDeviceid() { return deviceid; }
	public void setDeviceid(int i) { deviceid = i; }
	public void setDeviceid(String s) { deviceid = Integer.parseInt(s); }

	public int getModuleid() { return moduleid; }
	public String getModuleidS() { return String.valueOf(moduleid); }
	public void setModuleid(int i) { moduleid = i; }
	public void setModuleid(String s) { moduleid = Integer.parseInt(s); }

	public String getSerial() { return serial; }
	public String getHwVer() { return hw_ver; }
	public String getSwVer() { return sw_ver; }

	public String getModule() { return module; }
	public String getModuleS() { return ((module.length()==1)?" ":"")+getModule(); }

	public String getSubmodule() { return submodule; }
	public void setSubmodule(String s) { submodule = s; }

	public void addSwportData(SwportData sd) { swportData.put(sd.getPortI(), sd); }
	public Iterator getSwportData() { return swportData.values().iterator(); }
	public int getSwportCount() { return swportData.size(); }
	public SwportData getSwportData(Integer port) { return (SwportData)swportData.get(port); }

	public String getKey() {
		return module;
	}

	public boolean equals(Object o) {
		if (o instanceof ModuleData) {
			ModuleData md = (ModuleData)o;
			return (deviceid == md.deviceid &&
					module.equals(md.module) &&
					submodule.equals(md.submodule));
		}
		return false;
	}
	public boolean equalsDevice(ModuleData md) {
		return (serial.equals(md.serial) &&
				hw_ver.equals(md.hw_ver) &&
				sw_ver.equals(md.sw_ver));
	}

	public int compareTo(Object o) {
		ModuleData md = (ModuleData)o;
		try {
			return new Integer(module).compareTo(new Integer(md.getModule()));
		} catch (NumberFormatException e) {}
		return module.compareTo(md.getModule());
	}
	public String toString() { return getModuleS(); }
}
