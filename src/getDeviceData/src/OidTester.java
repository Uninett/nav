import java.util.*;
import java.sql.*;

import no.ntnu.nav.logger.*;
import no.ntnu.nav.ConfigParser.*;
import no.ntnu.nav.Database.*;
import no.ntnu.nav.SimpleSnmp.*;

/**
 * This class tests netboxes for OID compatibility.
 */

public class OidTester
{
	private static final int DEFAULT_FREQ = 3600;

	private static Map lockMap = new HashMap();
	private static Set dupeSet = new HashSet();

	private SimpleSnmp sSnmp;

	public void oidTest(Type t, Iterator snmpoidIt) {
		// Call test for all OIDs to this type
		for (; snmpoidIt.hasNext();) {
			Snmpoid snmpoid = (Snmpoid)snmpoidIt.next();
			doTest(t, snmpoid);
		}

		try {
			Database.update("UPDATE type SET uptodate='t' WHERE typeid='"+t.getTypeid()+"'");
		} catch (SQLException e) {
			Log.e("OID_TESTER", "TEST_TYPE", "A database error occoured while updating the OID database; please report this to NAV support!");
			Log.d("OID_TESTER", "TEST_TYPE", "SQLException: " + e.getMessage());
			e.printStackTrace(System.err);
		}
		Log.i("OID_TESTER", "TEST_TYPE", "Type " + t + " is now up-to-date");
	}

	public void oidTest(Snmpoid snmpoid, Iterator typeIt) {
		// Call test for all types to this OID
		for (; typeIt.hasNext();) {
			Type t = (Type)typeIt.next();
			doTest(t, snmpoid);
		}

		try {
			Database.update("UPDATE snmpoid SET uptodate='t' WHERE snmpoidid='"+snmpoid.getSnmpoidid()+"'");
		} catch (SQLException e) {
			Log.e("OID_TESTER", "TEST_OID", "A database error occoured while updating the OID database; please report this to NAV support!");
			Log.d("OID_TESTER", "TEST_OID", "SQLException: " + e.getMessage());
			e.printStackTrace(System.err);
		}
		Log.i("OID_TESTER", "TEST_OID", "OID " + snmpoid + " is now up-to-date");
	}

	private void doTest(Type t, Snmpoid snmpoid) {
		// Return if this has already been checked
		if (!checkDupe(t.getTypeid()+":"+snmpoid.getOidkey())) return;

		Log.d("OID_TESTER", "DO_TEST", "Starting test for type: " + t + ", snmpoid: " + snmpoid);
		sSnmp = SimpleSnmp.simpleSnmpFactory(t.getTypename());

		try {
			// Get netboxes to test against
			ResultSet rs = Database.query("SELECT ip, ro FROM netbox WHERE typeid = '"+t.getTypeid()+"' AND up='y' ORDER BY random() * netboxid");
		
			while (rs.next()) {
				boolean supported = false;

				// Check that not someone else is testing against this netbox
				String ip = rs.getString("ip");
				String ro = rs.getString("ro");
				synchronized(lock(ip)) {

					// Do the test
					sSnmp.setParams(ip, rs.getString("ro"), snmpoid.getSnmpoid());

					try {
						List l = sSnmp.getAll(snmpoid.getDecodehex(), snmpoid.getGetnext());
						Log.d("OID_TESTER", "DO_TEST", "Got results, length: " + l.size());
					
						String regex = snmpoid.getMatchRegex();
						for (Iterator i = l.iterator(); i.hasNext();) {
							String[] s = (String[])i.next();
							if (s[1] != null && s[1].length() > 0 && (regex == null || s[1].matches(regex))) {
								// Update db
								Log.d("OID_TESTER", "DO_TEST", "Match: " + regex + ", val: " + s[1]);

								rs = Database.query("SELECT typeid FROM typesnmpoid WHERE typeid='"+t.getTypeid()+"' AND snmpoidid='"+snmpoid.getSnmpoidid()+"'");
								if (!rs.next()) {
									String[] ins = {
										"typeid", t.getTypeid(),
										"snmpoidid", snmpoid.getSnmpoidid(),
										"frequency", ""+DEFAULT_FREQ
									};
									Database.insert("typesnmpoid", ins);
								}
								supported = true;
								t.addSnmpoid(DEFAULT_FREQ, snmpoid);
								break;
							}
						}
					} catch (TimeoutException e) {
						Log.d("OID_TESTER", "DO_TEST", "Got timeout exception testing oidkey " + snmpoid.getOidkey() + " with netbox: " + ip);
					} catch (Exception e) {
						Log.d("OID_TESTER", "DO_TEST", "Got exception testing oidkey " + snmpoid.getOidkey() + "with netbox: " + ip + ", assuming not supported: " + e.getMessage());
					}
						
					if (!supported) {
						Database.update("DELETE FROM typesnmpoid WHERE typeid='"+t.getTypeid()+"' AND snmpoidid='"+snmpoid.getSnmpoidid()+"'");
					}

				}
				unlock(ip);

				// Check if we need to test for csAtVlan
				synchronized(lock(t.getTypeid())) {
					if (t.getCsAtVlan() == t.CS_AT_VLAN_UNKNOWN) {
						if ("3com".equals(t.getVendor())) {
							t.setCsAtVlan(t.CS_AT_VLAN_FALSE);
						} else {
							// Do test
							try {
								sSnmp.setTimeoutLimit(1);
								sSnmp.setCs_ro(ro+"@1");
								sSnmp.getNext("1", 1, false, true);
								
								// OK, supported
								t.setCsAtVlan(t.CS_AT_VLAN_TRUE);
								
							} catch (Exception e) {
								// Not supported
								t.setCsAtVlan(t.CS_AT_VLAN_FALSE);
								Log.d("OID_TESTER", "CS_AT_VLAN", "Type " + t + ", Exception " + e);
							}
							sSnmp.setDefaultTimeoutLimit();
						}
						Database.update("UPDATE type SET cs_at_vlan = '" + t.getCsAtVlanC() + "' WHERE typeid = '"+t.getTypeid()+"'");
						Log.i("OID_TESTER", "CS_AT_VLAN", "Type " + t + " supports cs@vlan: " + t.getCsAtVlanC());
					}
				}
				unlock(t.getTypeid());

				if (supported) {
					// No need to test further
					break;
				}
			}
		} catch (SQLException e) {
			Log.e("OID_TESTER", "DO_TEST", "A database error occoured while updating the OID database; please report this to NAV support!");
			Log.d("OID_TESTER", "DO_TEST", "SQLException: " + e.getMessage());
			e.printStackTrace(System.err);
		}

	}

	// Returns true if s is not a dupe (has not been checked before)
	private static synchronized boolean checkDupe(String s) {
		return dupeSet.add(s);
	}

	private static synchronized String lock(String s) {
		if (!lockMap.containsKey(s)) {
			lockMap.put(s, new Refcnt(s));
		}
		Refcnt rf = (Refcnt)lockMap.get(s);
		rf.inc();
		return rf.getS();
	}

	private static synchronized void unlock(String s) {
		Refcnt rf = (Refcnt)lockMap.get(s);
		if (rf != null && rf.dec()) {
			lockMap.remove(s);
		}
	}

	private static class Refcnt {
		private int cnt = 0;
		private String s;

		Refcnt(String s) { this.s = s; }

		String getS() { return s; }
		void inc() { cnt++; }
		boolean dec() { 
			if (cnt > 0) {
				cnt--;
			}
			return cnt == 0;
		}
	}

}
