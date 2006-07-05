
public class Type
{
	public static final int CS_AT_VLAN_TRUE = 0;
	public static final int CS_AT_VLAN_FALSE = 1;
	public static final int CS_AT_VLAN_UNKNOWN = 2;

	public static final String UNKNOWN_TYPEID = "-1";

	private String typeid;
	private String typename;
	private String vendor;
	private int csAtVlan;
	private boolean chassis;

	Type(String typeid, String typename, String vendor, int csAtVlan, boolean chassis) {
		this.typeid = typeid;
		this.typename = typename;
		this.vendor = vendor;
		this.csAtVlan = csAtVlan;
		this.chassis = chassis;
	}

	public String getTypeid() {
		return typeid;
	}

	String getTypename() {
		return typename;
	}
	
	String getVendor() {
		return vendor;
	}

	void setCsAtVlan(int i) {
		csAtVlan = i;
	}

	int getCsAtVlan() {
		return csAtVlan;
	}
	char getCsAtVlanC() {
		return getCsAtVlan() == CS_AT_VLAN_TRUE ? 't' : 'f';
	}

	static int csAtVlan(boolean b) {
		return b ? CS_AT_VLAN_TRUE : CS_AT_VLAN_FALSE;
	}

	boolean getChassis() {
		return chassis;
	}

	void setChassis(boolean chassis) {
		this.chassis = chassis;
	}

	public String getKey() {
		return "t" + getTypeid();
	}

	public String toString() {
		return typename+"("+typeid+")";
	}



}
