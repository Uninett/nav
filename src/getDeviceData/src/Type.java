import java.util.*;

public class Type
{

	private String typeid;

	// Maps an OID key to frequency in seconds
	private Map keyFreqMap;

	// Maps an OID key to OID
	private Map keyMap;

	Type(String typeid, Map keyFreqMap, Map keyMap) {
		this.typeid = typeid;
		this.keyFreqMap = keyFreqMap;
		this.keyMap = keyMap;
	}

	String getTypeid() {
		return typeid;
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

	public String toString() {
		return "Type: " + typeid;
	}



}
