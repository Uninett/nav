import java.util.*;

public class Snmpoid
{
	String snmpoidid;
	String oidkey;
	String snmpoid;

	boolean getnext;
	String matchRegex;

	boolean uptodate;

	Map typeMap;

	public Snmpoid(String snmpoidid, String oidkey, String snmpoid, boolean getnext, String matchRegex, boolean uptodate) {
		this.snmpoidid = snmpoidid;
		this.oidkey = oidkey;
		this.snmpoid = snmpoid;
		this.getnext = getnext;
		this.matchRegex = matchRegex;
		this.uptodate = uptodate;
		typeMap = new HashMap();
	}

	public String getSnmpoidid() {
		return snmpoidid;
	}

	public String getOidkey() {
		return oidkey;
	}

	public String getSnmpoid() {
		return snmpoid;
	}

	public boolean getGetnext() {
		return getnext;
	}

	public String getMatchRegex() {
		return matchRegex;
	}

	public boolean getUptoDate() {
		return uptodate;
	}

	public void addType(Type t) {
		typeMap.put(t.getTypeid(), t);
	}

	public Iterator getTypeIterator() {
		return typeMap.values().iterator();
	}

}
