package no.ntnu.nav.getDeviceData.dataplugins.Swport;

import java.util.Map;
import java.util.HashMap;
import java.util.Iterator;

import no.ntnu.nav.getDeviceData.dataplugins.Module.Module;

/**
 * Describes a single switch module.
 */

public class SwModule extends Module implements Comparable
{
	private Map swports = new HashMap();

	SwModule(String serial, String hw_ver, String sw_ver, String module)
	{
		super(serial, hw_ver, sw_ver, module);
	}

	protected void setDeviceid(int i) { super.setDeviceid(i); }

	protected int getModuleid() { return super.getModuleid(); }
	protected String getModuleidS() { return super.getModuleidS(); }
	protected void setModuleid(int i) { super.setModuleid(i); }

	protected String getKey() {
		return super.getKey();
	}


	void addSwport(Swport sd) { swports.put(sd.getPort(), sd); }
	Iterator getSwports() { return swports.values().iterator(); }
	int getSwportCount() { return swports.size(); }
	Swport getSwport(Integer port) { return (Swport)swports.get(port); }

	/**
	 * Return an Swport-object which is used to describe a single switch port.
	 */
	public Swport swportFactory(Integer port, String ifindex) {
		Swport sw = new Swport(port, ifindex);
		swports.put(port, sw);
		return sw;
	}

	/**
	 * Return an Swport-object which is used to describe a single switch port.
	 */
	public Swport swportFactory(Integer port, String ifindex, char link, String speed, char duplex, String media, boolean trunk, String portname) {
		Swport sw = new Swport(port, ifindex, link, speed, duplex, media, trunk, portname);
		swports.put(port, sw);
		return sw;
	}

}
