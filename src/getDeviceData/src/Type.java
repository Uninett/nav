import java.util.*;

public class Type
{
	// Maps an OID key to frequency in seconds
	private Map keyFreqMap;

	// Maps an OID key to OID
	private Map keyMap;

	Type() {

	}

	synchronized int getFreq(String key) {
			return ((Integer)keyFreqMap.get(key)).intValue();
	}

	synchronized String getOid(String key) {
		return (String)keyMap.get(key);
	}



}
