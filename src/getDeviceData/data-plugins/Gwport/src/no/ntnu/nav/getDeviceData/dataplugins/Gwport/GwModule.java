package no.ntnu.nav.getDeviceData.dataplugins.Gwport;

import java.util.*;

import no.ntnu.nav.getDeviceData.dataplugins.Module.Module;

/**
 * Describes a single router module.
 */

public class GwModule extends Module implements Comparable
{
	private Map vlanMap = new HashMap();
	private List vlanList = new ArrayList();

	private Map gwports = new HashMap();

	GwModule(int module) {
		super(module);
	}

	GwModule(String serial, String hw_ver, String sw_ver, int module) {
		super(serial, hw_ver, sw_ver, module);
	}

	protected void setDeviceid(int i) { super.setDeviceid(i); }

	protected int getModuleid() { return super.getModuleid(); }
	protected String getModuleidS() { return super.getModuleidS(); }
	protected void setModuleid(int i) { super.setModuleid(i); }

	// Doc in parent
	protected String getKey() { return super.getKey(); }

	void addGwport(Gwport gwp) { gwports.put(gwp.getIfindex(), gwp); }
	/*
	Iterator getSwports() { return swports.values().iterator(); }
	int getSwportCount() { return swports.size(); }
	Swport getSwport(Integer port) { return (Swport)swports.get(port); }
	*/

	/**
	 * Return a Vlan-object which is used to describe a single vlan. The
	 * vlan-number is not known.
	 */
	public Vlan vlanFactory(String netident) {
		Vlan v = new Vlan(netident);
		vlanList.add(v);
		return v;
	}

	/**
	 * Return a Vlan-object which is used to describe a single vlan.
	 */
	public Vlan vlanFactory(String netident, int vlan) {
		Vlan v;
		Integer vl = new Integer(vlan);
		if ( (v=(Vlan)vlanMap.get(vl)) == null) vlanMap.put(vl, v = new Vlan(netident, vlan));
		return v;
	}

	/**
	 * Return a Gwport-object which is used to describe a single router interface.
	 */
	public Gwport gwportFactory(String ifindex, String interf) {
		Gwport gw = new Gwport(ifindex, interf);
		gwports.put(ifindex, gw);
		return gw;
	}

	Iterator getGwports() {
		return gwports.values().iterator();
	}

	public String toString() {
		return super.toString() + ", Gwports: " + gwports.size();
	}


}
