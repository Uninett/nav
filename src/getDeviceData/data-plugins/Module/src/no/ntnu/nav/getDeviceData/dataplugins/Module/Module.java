package no.ntnu.nav.getDeviceData.dataplugins.Module;

import java.util.Map;
import java.util.HashMap;
import java.util.Iterator;

import no.ntnu.nav.getDeviceData.dataplugins.Device.Device;

/**
 * Describes a single module. Normally this class will be inherited.
 */

public class Module extends Device implements Comparable
{
	private int moduleid;

	private int module;
	private String descr;

	/**
	 * Constructor.
	 */
	protected Module(int module) {
		super();
		this.module = module;
	}

	/**
	 * Constructor.
	 */
	protected Module(String serial, String hwVer, String swVer, int module) {
		super(serial, hwVer, swVer);
		this.module = module;
	}

	// Doc in parent
	protected void setDeviceid(int i) { super.setDeviceid(i); }
	protected int getDeviceid() { return super.getDeviceid(); }
	protected String getDeviceidS() { return super.getDeviceidS(); }

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

	int getModule() { return module; }
	String getModuleS() { return ((module < 10)?" ":"")+getModule(); }

	String getDescr() { return descr; }

	/**
	 * Set the description of this module.
	 */
	public void setDescr(String s) { descr = s; }

	/**
	 * Return a key which identifies this module (currently the module number is returned).
	 */
	protected String getKey() {
		return ""+module;
	}

	protected boolean hasEmptySerial() { return super.hasEmptySerial(); }

	public boolean equalsModule(Module m) {
		return (getDeviceid() == m.getDeviceid() &&
						module == m.module &&
						(descr == null || descr.equals(m.descr)));
	}
	
	public boolean equals(Object o) {
		return (o instanceof Module &&
						module == (((Module)o).module));
	}


	public int compareTo(Object o) {
		Module m = (Module)o;
		return new Integer(module).compareTo(new Integer(m.getModule()));
	}
	public String toString() { return super.toString() + ", " + getModuleS() + " descr="+descr; }
}
