import java.util.*;

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
	private boolean uptodate;
	private boolean dirty;

	// Maps an OID key to frequency in seconds
	private Map keyFreqMap;

	// Maps an OID key to Snmpoid
	private Map keyMap;

	Type(String typeid, String typename, String vendor, int csAtVlan, boolean uptodate, Map keyFreqMap, Map keyMap) {
		this.typeid = typeid;
		this.typename = typename;
		this.vendor = vendor;
		this.csAtVlan = csAtVlan;
		this.uptodate = uptodate;
		this.keyFreqMap = keyFreqMap;
		this.keyMap = keyMap;
		if (!uptodate) dirty = true;
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

	Iterator getKeyFreqMapIterator() {
		return keyFreqMap.entrySet().iterator();
	}

	int getFreq(String key) {
		return ((Integer)keyFreqMap.get(key)).intValue();
	}

	String getOid(String key) {
		Snmpoid snmpoid = (Snmpoid)keyMap.get(key);
		return snmpoid == null ? null : snmpoid.getSnmpoid();
	}

	Iterator getOidIterator() {
		return keyMap.values().iterator();
	}

	void setDirty(boolean dirty) {
		this.dirty = dirty;
	}

	boolean getDirty() {
		return dirty;
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

	boolean getUptodate() {
		return uptodate;
	}

	void addSnmpoid(int freq, Snmpoid snmpoid) {
		String oidkey = snmpoid.getOidkey();
		keyFreqMap.put(oidkey, new Integer(freq));
		keyMap.put(oidkey, snmpoid);
	}

	public String toString() {
		return typename+"("+typeid+")";
	}



}
