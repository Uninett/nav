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
	private SwportContainer sc;

	SwModule(String module, SwportContainer sc) {
		super(module);
		this.sc = sc;
	}

	SwModule(String serial, String hwVer, String swVer, String module, SwportContainer sc) {
		super(serial, hwVer, swVer, module);
		this.sc = sc;
	}

	protected void setDeviceid(int i) { super.setDeviceid(i); }

	protected int getModuleid() { return super.getModuleid(); }
	protected String getModuleidS() { return super.getModuleidS(); }
	protected void setModuleid(int i) { super.setModuleid(i); }

	// Doc in parent
	protected String getKey() { return super.getKey(); }

	void addSwport(Swport sd) { swports.put(sd.getIfindex(), sd); }
	Iterator getSwports() { return swports.values().iterator(); }
	int getSwportCount() { return swports.size(); }
	Swport getSwport(String ifindex) { return (Swport)swports.get(ifindex); }

	/**
	 * Return an Swport-object which is used to describe a single switch port.
	 */
	public Swport swportFactory(String ifindex) {
		Swport sw = sc.createOrGetSwport(ifindex);
		sw.assignedToModule();
		swports.put(ifindex, sw);
		return sw;
	}

}
