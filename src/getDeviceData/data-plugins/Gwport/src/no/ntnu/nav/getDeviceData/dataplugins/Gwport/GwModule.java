package no.ntnu.nav.getDeviceData.dataplugins.Gwport;

import java.util.Map;
import java.util.HashMap;
import java.util.Iterator;

import no.ntnu.nav.getDeviceData.dataplugins.Module.Module;

/**
 * Describes a single router module.
 */

public class GwModule extends Module implements Comparable
{
	private Map gwports = new HashMap();

	GwModule(String serial, String hw_ver, String sw_ver, String module)
	{
		super(serial, hw_ver, sw_ver, module);
	}

	protected void setDeviceid(int i) { super.setDeviceid(i); }

	protected int getModuleid() { return super.getModuleid(); }
	protected String getModuleidS() { return super.getModuleidS(); }
	protected void setModuleid(int i) { super.setModuleid(i); }

	// Doc in parent
	protected String getKey() { return super.getKey(); }

	/*
	void addGwport(Gwport sd) { swports.put(sd.getPort(), sd); }
	Iterator getSwports() { return swports.values().iterator(); }
	int getSwportCount() { return swports.size(); }
	Swport getSwport(Integer port) { return (Swport)swports.get(port); }
	*/

	/**
	 * Return a Gwport-object which is used to describe a single router interface.
	 */
	public Gwport gwportFactory(String ifindex, String interf, String gwip) {
		Gwport gw = new Gwport(ifindex, interf, gwip);
		gwports.put(ifindex, gw);
		return gw;
	}

}
