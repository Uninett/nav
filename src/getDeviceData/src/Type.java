import java.util.*;

public class Type
{

	private String typeid;
	private String typename;
	private boolean uptodate;
	private boolean dirty;

	// Maps an OID key to frequency in seconds
	private Map keyFreqMap;

	// Maps an OID key to Snmpoid
	private Map keyMap;

	Type(String typeid, String typename, boolean uptodate, Map keyFreqMap, Map keyMap) {
		this.typeid = typeid;
		this.typename = typename;
		this.uptodate = uptodate;
		this.keyFreqMap = keyFreqMap;
		this.keyMap = keyMap;
		if (!uptodate) dirty = true;
	}

	String getTypeid() {
		return typeid;
	}

	String getTypename() {
		return typename;
	}

	Iterator getKeyFreqMapIterator() {
		return keyFreqMap.entrySet().iterator();
	}

	int getFreq(String key) {
		return ((Integer)keyFreqMap.get(key)).intValue();
	}

	String getOid(String key) {
		return (String)keyMap.get(key);
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

	boolean getUptodate() {
		return uptodate;
	}

	void addSnmpoid(int freq, Snmpoid snmpoid) {
		String oidkey = snmpoid.getOidkey();
		keyFreqMap.put(oidkey, new Integer(freq));
		keyMap.put(oidkey, snmpoid);
	}

	public String toString() {
		return "Type: " + typeid;
	}



}
