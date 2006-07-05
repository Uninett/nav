package no.ntnu.nav.getDeviceData.dataplugins.Module;

import no.ntnu.nav.getDeviceData.dataplugins.Device.Device;

/**
 * Describes a single module. Normally this class will be inherited.
 */

public class Module extends Device implements Comparable
{
	private int moduleid;

	private int module;
	private String model;
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
	protected Module(String serial, String hwVer, String fwVer, String swVer, int module) {
		super(serial, hwVer, fwVer, swVer);
		this.module = module;
	}

	// Doc in parent
	protected void setDeviceid(int i) { super.setDeviceid(i); }
	public int getDeviceid() { return super.getDeviceid(); }
	public String getDeviceidS() { return super.getDeviceidS(); }

	/**
	 * Return the moduleid.
	 */
	protected int getModuleid() { return moduleid; }

	/**
	 * Return the moduleid as a String.
	 */
	protected String getModuleidS() { return String.valueOf(moduleid); }

	public void setSerial(String s) {
		super.setSerial(s);
	}


	/**
	 * Set the moduleid of this module.
	 */
	protected void setModuleid(int i) { moduleid = i; }

	void setModuleid(String s) { setModuleid(Integer.parseInt(s)); }

	public int getModule() { return module; }
	String getModuleS() { return ((module < 10)?" ":"")+getModule(); }
	void setModule(int module) {
		this.module = module;
	}

	public String getModel() { return model; }
	public String getDescr() { return descr; }

	public boolean getIgnore() { return ignore; }

	/**
	 * Set the model of this module.
	 */
	public void setModel(String s) {
		if (s != null && s.length() > 0) {
			model = s;
		}
	}

	/**
	 * Set the description of this module.
	 */
	public void setDescr(String s) {
		if (s != null && s.length() > 0) {
			descr = s;
		}
	}

	/**
	 * Return a key which identifies this module (currently the module number is returned).
	 */
	protected String getKey() {
		return ""+module;
	}

	public void setEqual(Module m) {
		if (m.moduleid != 0) moduleid = m.moduleid;
		if (m.model != null) model = m.model;
		if (m.descr != null) descr = m.descr;
	}

	protected boolean hasEmptySerial() { return super.hasEmptySerial(); }

	public boolean equalsModule(Module m) {
		return (getDeviceid() == m.getDeviceid() &&
						module == m.module &&
						(model == null || model.equals(m.model)) &&
						(descr == null || descr.equals(m.descr)));
	}
	
	public boolean equals(Object o) {
		return (o instanceof Module &&
						module == (((Module)o).module));
	}


	public int compareTo(Object o) {
		Module m = (Module)o;
		return new Integer(module).compareTo(new Integer(m.module));
	}
	public String toString() { return super.toString() + ", moduleid="+moduleid+", " + getModuleS() + " model="+model+" descr="+descr; }
}
