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
 * <p> The HP 2524 switch requires special treatment when used in
 * stack mode; only the first switch (the commander) can be accessed
 * normally. To access the other switches "@&lt;switch num&gt;" must
 * be appended to the community string. This class takes care of the
 * details and allows HP stacks to be accessed as a single switch.
 * </p>
 *
 * <p> Note that the individual switches in a HP stack uses the same
 * ifIndex numbers; this class therefore prepends the module number to
 * all returned OIDs.  </p>
 * 
 */
public class SimpleSnmpHP2524 extends SimpleSnmp
{
	private List stackList;

	// Constructor
	SimpleSnmpHP2524() { 
		super();
	}
	
	// Constructor
	SimpleSnmpHP2524(String host, String cs_ro, String baseOid) {
		super(host, cs_ro, baseOid);
	}

	// Doc in parent
	// Must be overridden to avoid module being prepended twice if stripCnt is 0
	public Map getAllMapList(String baseOid, int stripCnt) throws TimeoutException {
		List l = getAll(false, baseOid, false, true);
		return listToMapList(l, stripCnt);
	}

	// Doc in parent
	public ArrayList getAll(String baseOid, boolean decodeHex, boolean getNext) throws TimeoutException {
		return getAll(true, baseOid, decodeHex, getNext);
	}

	// If prependModule is true the module will be prepended to the OID
	private ArrayList getAll(boolean prependModule, String baseOid, boolean decodeHex, boolean getNext) throws TimeoutException {
		if (baseOid == null) return null;
		try {
			if (checkSnmpContext()) stackList = null;
		} catch (IOException e) {
			Log.e("SimpleSnmpHP2524", "GET_ALL", "IOException: " + e.getMessage());
			return null;
		}

		if (stackList == null) {
			// A bit ugly, OID database stuff should be in its own package		
			String hpStackOid;
			try {
				ResultSet rs = Database.query("SELECT snmpoid FROM snmpoid WHERE oidkey='hpStack'");
				if (!rs.next()) {
					Log.e("SimpleSnmpHP2524", "GET_ALL", "Oidkey 'hpStack' not found in snmpoid");
					return null;
				}
				hpStackOid = rs.getString("snmpoid");
			} catch (SQLException e) {
				Log.e("SimpleSnmpHP2524", "GET_ALL", "SQLException: " + e.getMessage());
				return null;
			}

			// Get the number of devices in the stack
			stackList = super.getAll(hpStackOid, false, true);

			if (stackList.isEmpty()) stackList.add(new String[] { "", "0" });
			Log.d("SimpleSnmpHP2524", "GET_ALL", "stackList.size: " + stackList.size() );
		}

		String cs_ro = getCs_ro();
		ArrayList l = new ArrayList();
		for (int i=stackList.size()-1; i >= 0; i--) {
			String[] s = (String[])stackList.get(i);
			
			setCs_ro(cs_ro+(!s[1].equals("0")?"@sw"+s[1]:""));
			String module = s[1].equals("0") ? "" : s[1];
			
			List pl = super.getAll(baseOid, decodeHex, getNext);
			for (Iterator it = pl.iterator(); it.hasNext();) {
				s = (String[])it.next();
				if (prependModule) {
					s[0] = module + s[0];
				}
				s = new String[] { s[0], s[1], module };
				l.add(s);
			}
		}
		setCs_ro(cs_ro);
		return l;
	}
	
}

