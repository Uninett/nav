package no.ntnu.nav.SimpleSnmp;

import java.io.*;
import java.util.*;
import java.sql.*;

import uk.co.westhawk.snmp.stack.*;
import uk.co.westhawk.snmp.pdu.*;

import no.ntnu.nav.logger.*;
import no.ntnu.nav.Database.*;

/**
 * <p> Class for quering devices via SNMP. The aim of this class is to
 * provide a very simple API for doing basic SNMP walking.  </p>
 *
 * <p> HP switches requires special treatment when used in stack mode;
 * only the first switch (the commander) can be accessed normally. To
 * access the other switches "@&lt;switch num&gt;" must be appended to
 * the community string. This class takes care of the details and
 * allows HP stacks to be accessed as a single switch.  </p>
 *
 * <p> Note that the individual switches in a HP stack uses the same
 * ifIndex numbers; this class therefore prepends the module number to
 * all returned OIDs.  </p>
 * 
 */
public class SimpleSnmpHP extends SimpleSnmp
{
	private List stackList;
	private String askOnlyModule;

	// Constructor
	SimpleSnmpHP() { 
		super();
	}
	
	// Constructor
	SimpleSnmpHP(String host, String cs_ro, String baseOid) {
		super(host, cs_ro, baseOid);
	}

	// Doc in parent
	// Must be overridden to avoid module being prepended twice if stripCnt is 0
	public Map getAllMapList(String baseOid, int stripCnt) throws TimeoutException {
		List l = getAll(false, baseOid, 0, false, true, 0);
		return listToMapList(l, stripCnt);
	}

	/**
	 * Override to add module number to ifIndex.
	 */
	protected String convertToIfIndex(String[] s) {
		// Construct ifIndex
		String ifindex = s[0];
		if (ifindex.split("\\.")[0].length() == 1) ifindex = "0" + ifindex;
		ifindex = new Integer(Integer.parseInt(s[2])+1) + ifindex;
		return ifindex;
	}

	/**
	 * Remove the module part from the ifindex.
	 */
	public String extractIfIndexOID(String ifindex) {
		if (ifindex.length() >= 3) ifindex = ifindex.substring(1, ifindex.length());
		if (ifindex.startsWith("0")) ifindex = ifindex.substring(1, ifindex.length());
		return ifindex;
	}

	/**
	 * HP adds -# to the name of modules other than the master, which
	 * this method removes.
	 */
	public String extractSysname(String sysname, String module) {
		if (sysname == null || module == null) return null;
		if (sysname.endsWith("-"+module)) sysname = sysname.substring(0, sysname.length()-2);
		return sysname;
	}


	// Doc in parent
	public void onlyAskModule(String module) {
		this.askOnlyModule = module;
	}

	// Doc in parent
	public ArrayList getAll(String baseOid, int getCnt, boolean decodeHex, boolean getNext, int stripCnt) throws TimeoutException {
		return getAll(true, baseOid, getCnt, decodeHex, getNext, stripCnt);
	}

	// If prependModule is true the module will be prepended to the OID
	private ArrayList getAll(boolean prependModule, String baseOid, int getCnt, boolean decodeHex, boolean getNext, int stripCnt) throws TimeoutException {
		if (baseOid == null) return null;
		//Log.d("SimpleSnmpHP", "GET_ALL", "Fetch baseOid: " + baseOid);
		try {
			if (checkSnmpContext()) stackList = null;
		} catch (IOException e) {
			Log.e("SimpleSnmpHP", "GET_ALL", "IOException: " + e.getMessage());
			return null;
		}

		if (stackList == null) {
			// A bit ugly, OID database stuff should be in its own package		
			String hpStackOid;
			try {
				ResultSet rs = Database.query("SELECT snmpoid FROM snmpoid WHERE oidkey='hpStack'");
				if (!rs.next()) {
					Log.e("SimpleSnmpHP", "GET_ALL", "Oidkey 'hpStack' not found in snmpoid");
					return null;
				}
				hpStackOid = rs.getString("snmpoid");
			} catch (SQLException e) {
				Log.e("SimpleSnmpHP", "GET_ALL", "SQLException: " + e.getMessage());
				return null;
			}

			// Get the number of devices in the stack
			stackList = super.getAll(hpStackOid, 0, false, true, 0);

			if (stackList.isEmpty()) stackList.add(new String[] { "", "0" });

			Log.d("SimpleSnmpHP", "GET_ALL", "stackList.size: " + stackList.size() + " Prepend: " + prependModule);
		}

		String cs_ro = getCs_ro();
		ArrayList l = new ArrayList();
		for (Iterator stackIt = stackList.iterator(); stackIt.hasNext();) {
			String[] s = (String[])stackIt.next();
			if (askOnlyModule != null && !askOnlyModule.equals(s[1])) continue;
			
			setCs_ro(cs_ro+(!s[1].equals("0")?"@sw"+s[1]:""));
			String module = s[1];
			//String modulePrepend = s[1].equals("0") ? "" : s[1];
			
			List pl = super.getAll(baseOid, getCnt, decodeHex, getNext, stripCnt);
			for (Iterator it = pl.iterator(); it.hasNext();) {
				s = (String[])it.next();
				String port = s[0];
				s = new String[] { s[0], s[1], module, port };
				if (prependModule) {
					// Construct ifIndex
					s[0] = convertToIfIndex(s);
				}
				//System.err.println("Ret s0: " + s[0] + " s1: " + s[1] + " s2: " + s[2] + " s3: " + s[3]);
				l.add(s);
			}
		}
		setCs_ro(cs_ro);
		return l;
	}
	
}

