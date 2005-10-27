import java.util.*;
import java.sql.*;

import no.ntnu.nav.Database.*;

public class Snmpoid
{
	String snmpoidid;
	String oidkey;
	String snmpoid;

	boolean getnext;
	boolean decodehex;
	String matchRegex;

	int defaultfreq;

	boolean uptodate;

	Map typeMap;

	public Snmpoid(String snmpoidid, String oidkey, String snmpoid, boolean getnext, boolean decodehex, String matchRegex, int defaultfreq, boolean uptodate) {
		this.snmpoidid = snmpoidid;
		this.oidkey = oidkey;
		this.snmpoid = snmpoid;
		this.getnext = getnext;
		this.decodehex = decodehex;
		this.defaultfreq = defaultfreq;
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

	public void setGetnext(boolean getnext) {
		this.getnext = getnext;
	}

	public boolean getDecodehex() {
		return decodehex;
	}

	public String getMatchRegex() {
		return matchRegex;
	}

	public int getDefaultfreq() {
		return defaultfreq;
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

	public String getKey() {
		return "s" + getOidkey();
	}

	public String toString() {
		return oidkey;
	}

	public static String getOid(String oidkey) {
		try {
			ResultSet rs = Database.query("SELECT snmpoid FROM snmpoid WHERE oidkey = '"+oidkey+"'");
			if (rs.next()) {
				return rs.getString("snmpoid");
			}
		} catch (SQLException e) {
			e.printStackTrace(System.err);
		}
		return null;
	}

}
