import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import no.ntnu.nav.Database.Database;
import no.ntnu.nav.SimpleSnmp.SimpleSnmp;
import no.ntnu.nav.SimpleSnmp.TimeoutException;
import no.ntnu.nav.getDeviceData.Netbox;
import no.ntnu.nav.logger.Log;
import no.ntnu.nav.util.HashMultiMap;
import no.ntnu.nav.util.MultiMap;

/**
 * This class tests netboxes for OID compatibility.
 */

public class OidTester
{
	public static int DEFAULT_FREQ = 21600; // Used only for "virtual" oids (e.g. typeoid, dnscheck)

	private static Map lockMap = new HashMap();
	//private static Set dupeSet = new HashSet();
	private static MultiMap dupeMap = new HashMultiMap();
	private static Set typeChecked = Collections.synchronizedSet(new HashSet());

	//private SimpleSnmp sSnmp;

	public void oidTest(NetboxImpl nb, Iterator snmpoidIt, SimpleSnmp sSnmp) {
		// Call test for all OIDs to this type
		Map tmp = new HashMap();
		nb.clearSnmpoid();
		Log.d("OID_TESTER", "DO_TEST", "Using SNMP version " + sSnmp.getSnmpVersion() + " for " + nb.getSysname());
		for (; snmpoidIt.hasNext();) {
			Snmpoid snmpoid = (Snmpoid)snmpoidIt.next();
			doTest(nb, snmpoid, sSnmp, tmp, false);
		}

		try {
			Database.update("UPDATE netbox SET uptodate='t' WHERE netboxid='"+nb.getNetboxid()+"'");
		} catch (SQLException e) {
			Log.e("OID_TESTER", "TEST_NETBOX", "A database error occoured while updating the OID database; please report this to NAV support!");
			Log.d("OID_TESTER", "TEST_NETBOX", "SQLException: " + e.getMessage());
			e.printStackTrace(System.err);
		}
		nb.setUptodate(true);
		Log.i("OID_TESTER", "TEST_NETBOX", "Netbox " + nb + " is now up-to-date");
	}

	public void oidTest(Snmpoid snmpoid, Iterator netboxIt) {
		// Call test for all types to this OID
		SimpleSnmp sSnmp = null;
		Map tmp = new HashMap();
		for (; netboxIt.hasNext();) {
			NetboxImpl nb = (NetboxImpl)netboxIt.next();
			sSnmp = SimpleSnmp.simpleSnmpFactory();
			doTest(nb, snmpoid, sSnmp, tmp, true);
			sSnmp.destroy();
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

	private void doTest(NetboxImpl nb, Snmpoid snmpoid, SimpleSnmp sSnmp, Map tmp, boolean checkSnmpVersion) {
		boolean dupeType = dupeMap.containsKey(nb.getKey());

		// Return if this has already been checked
		if (!checkDupe(nb, snmpoid)) return;

		Type t = nb.getTypeT();
		Log.setNetbox(nb.getSysname());
		Log.d("OID_TESTER", "DO_TEST", "Starting test for netbox: " + nb + " ("+t+"), snmpoid: " + snmpoid);

		try {
			boolean supported = false;

			// Check that not someone else is testing against this netbox
			String ip = nb.getIp();
			String ro = nb.getCommunityRo();
			String sysname = nb.getSysname();

			sSnmp.setHost(ip);
			sSnmp.setCs_ro(ro);
			if (checkSnmpVersion) {
				sSnmp.checkSnmpVersion();
			}

			if (t.getTypeid() != Type.UNKNOWN_TYPEID && typeChecked.add(t.getTypeid())) {
				// Check if we need to test for csAtVlan and chassis
				try { synchronized(lock(t.getTypeid())) {
					// Chassis first, using chassisId and exception for cat2924 (FIXME!)
					try {
						boolean chassis = true;
						if (!"cisco".equals(t.getVendor())) {
							chassis = false;
						} else if (t.getTypename().startsWith("cat2924") || t.getTypename().startsWith("cat2950")) {
							chassis = false;
						} else {
							// Check if cChassisSlots is 1
							List chassisSlotsList = sSnmp.getAll(Snmpoid.getOid("cChassisSlots"));
							if (chassisSlotsList != null && !chassisSlotsList.isEmpty()) {
								String[] s = (String[])chassisSlotsList.get(0);
								try {
									int slots = Integer.parseInt(s[1]);
									if (slots == 0 || slots == 1) {
										chassis = false;
									}
								} catch (NumberFormatException exp) { }
							}
						}
						
						if (chassis != t.getChassis()) {
							// Change status of chassis
							String[] set = {
								"chassis", (chassis?"t":"f"),
							};
							String[] where = {
								"typeid", t.getTypeid(),
							};
							Database.update("type", set, where);
							t.setChassis(chassis);
						}
					} catch (TimeoutException exp) {
						Log.d("OID_TESTER", "DO_TEST", "Got timeout exception testing cChassisSlots with netbox: " + ip);
					} catch (Exception e) {
						Log.d("OID_TESTER", "DO_TEST", "Got exception testing cChassisSlots with netbox: " + ip + ": " + e.getMessage());
						e.printStackTrace(System.err);
					}
						
					if (t.getCsAtVlan() == Type.CS_AT_VLAN_UNKNOWN) {
						if ("3com".equals(t.getVendor())) {
							t.setCsAtVlan(Type.CS_AT_VLAN_FALSE);
						} else {
							// Do test
							try {
								sSnmp.setTimeoutLimit(1);
								sSnmp.setCs_ro(ro+"@1");
								sSnmp.getNext("1", 1, false, true);
								
								// OK, supported
								t.setCsAtVlan(Type.CS_AT_VLAN_TRUE);
								
							} catch (Exception e) {
								// Not supported
								t.setCsAtVlan(Type.CS_AT_VLAN_FALSE);
								Log.d("OID_TESTER", "CS_AT_VLAN", "Type " + t + ", Exception " + e);
							}
							sSnmp.setDefaultTimeoutLimit();
						}
						Database.update("UPDATE type SET cs_at_vlan = '" + t.getCsAtVlanC() + "' WHERE typeid = '"+t.getTypeid()+"'");
						Log.i("OID_TESTER", "CS_AT_VLAN", "Type " + t + " supports cs@vlan: " + t.getCsAtVlanC());
					}
				} } finally { unlock(t.getTypeid()); }
			}

			try { synchronized(lock(ip)) {

				List atVlan;
				if (tmp.containsKey("atVlan")) {
					atVlan = (List)tmp.get("atVlan");
				} else {
					tmp.put("atVlan", atVlan = new ArrayList());
					atVlan.add("");
					if (t.getCsAtVlan() == Type.CS_AT_VLAN_TRUE) {
						sSnmp.setTimeoutLimit(1);

						// Try to find the vlan of the netbox's IP
						boolean foundVl = false;
						try {
							List myVlan = sSnmp.getNext(Snmpoid.getOid("ipAdEntIfIndex")+"."+ip, 1, false, false);
							if (!myVlan.isEmpty()) {
								myVlan = sSnmp.getNext(Snmpoid.getOid("ifDescr")+"."+((String[])myVlan.get(0))[1], 1, true, false);
								if (!myVlan.isEmpty()) {
									String interf = ((String[])myVlan.get(0))[1].toLowerCase();
									String pattern = "vlan(\\d+).*";
									if (interf.matches(pattern)) {
										Matcher m = Pattern.compile(pattern).matcher(interf);
										m.matches();
										int vlan = Integer.parseInt(m.group(1));
										atVlan.add("@"+vlan);
										foundVl = true;
									}
								}
							}
						} catch (Exception e) {
						}

						if (!foundVl) {
							try {
								// Try the vtp OID
								List myVlan = sSnmp.getAll(Snmpoid.getOid("vtpVlanState")+".1", false);
								for (Iterator myIt = myVlan.iterator(); myIt.hasNext();) {
									String vl = ((String[])myIt.next())[0];
									atVlan.add("@"+vl);
									foundVl = true;
								}
							} catch (Exception e) {
							}
						}

						if (!foundVl) {
							for (int vlCnt = 1; vlCnt <= 999; vlCnt++) {
								atVlan.add("@"+vlCnt);
							}
						}

						sSnmp.setDefaultTimeoutLimit();
					}
				}

				for (Iterator vlIt = atVlan.iterator(); vlIt.hasNext();) {
					String atVl = (String)vlIt.next();

					// Do the test
					sSnmp.setParams(ip, ro+atVl, snmpoid.getSnmpoid());

					try {
						List l = null;
						boolean reqGetnext = true;
						if (snmpoid.getGetnext()) {
							// Check if getnext is really necessary
							l = sSnmp.getAll(snmpoid.getDecodehex(), false);
							if (!l.isEmpty()) {
								String[] s = (String[])l.get(0);
								if (s[1] != null && s[1].length() > 0) {
									reqGetnext = false;
									Log.d("TEST_GETNEXT", "Switch getnext from true to false");
								}
							}
						} else {
							l = sSnmp.getAll(snmpoid.getDecodehex(), false);						
						}
						if (snmpoid.getGetnext() && reqGetnext) {
							// If we need to do regex matching against the values in the subtree, 
							// get all values.  If not, just get the first value of the subtree.
							int getCnt = snmpoid.getMatchRegex() == null ? 1 : 0;
							l = sSnmp.getNext(getCnt, snmpoid.getDecodehex(), true, false);
							if (getCnt == 1 && l.size() > 0) {
								// Make sure the retrieved OID is in the subtree. If not, we consider the response not valid.
								String[] response = (String[]) l.get(0);
								if (!response[0].startsWith(snmpoid.getSnmpoid())) {
									Log.d("OID_TESTER", "DO_TEST", "GET-NEXT Response "+response[0]+" was outside baseOid " + snmpoid.getSnmpoid() + " (" + snmpoid.getOidkey() + "), ignoring.");
									l.clear();
								} else if (response[0].equals(snmpoid.getSnmpoid())) {
									Log.d("OID_TESTER", "DO_TEST", "GET-NEXT of " + snmpoid.getOidkey() + " was apparently outside the mib view");
									l.clear();
								}
							}
						}
						Log.d("OID_TESTER", "DO_TEST", "Got results from " + sysname + ", length: " + l.size() + " (oid: " + snmpoid.getOidkey() + ", reqGetnext: "+reqGetnext+", vl: " + atVl+")");
					
						String regex = snmpoid.getMatchRegex();
						for (Iterator i = l.iterator(); i.hasNext();) {
							String[] s = (String[])i.next();
							if (s[1] != null && (regex == null || s[1].matches(regex))) {
								// Update db
								Log.d("OID_TESTER", "DO_TEST", "Match: " + regex + ", val: " + s[1]);

								ResultSet rs = Database.query("SELECT netboxid FROM netboxsnmpoid WHERE netboxid='"+nb.getNetboxid()+"' AND snmpoidid='"+snmpoid.getSnmpoidid()+"'");
								if (!rs.next()) {
									String[] ins = {
										"netboxid", nb.getNetboxidS(),
										"snmpoidid", snmpoid.getSnmpoidid(),
										"frequency", ""+snmpoid.getDefaultfreq(),
									};
									Database.insert("netboxsnmpoid", ins);

									if (!reqGetnext) {
										// Change status of getnext to false
										String[] set = {
											"getnext", "f",
										};
										String[] where = {
											"snmpoidid", snmpoid.getSnmpoidid(),
										};
										Database.update("snmpoid", set, where);
									}
								}
								supported = true;
								nb.addSnmpoid(snmpoid.getDefaultfreq(), snmpoid);
								break;
							}
						}
					} catch (TimeoutException e) {
						Log.d("OID_TESTER", "DO_TEST", "Got timeout exception testing oidkey " + snmpoid.getOidkey() + " with netbox: " + ip + " (vl: " + atVl + ")");
						break;
					} catch (Exception e) {
						Log.d("OID_TESTER", "DO_TEST", "Got exception testing oidkey " + snmpoid.getOidkey() + " with netbox: " + ip + ", assuming not supported: " + e.getMessage());
						break;
					}

					if (supported) break;
					
					/**
					 * cs@vlan AKA cs_at_vlan AKA community string indexing for vlans
					 * is only necessary when retrieving multiple instances of the 
					 * BRIDGE-MIB on Cisco switches.  See the following URL for doc:
					 * 
					 * http://www.cisco.com/en/US/tech/tk648/tk362/technologies_tech_note09186a00801576ff.shtml
					 * 
					 * If the snmpoid we are currently testing is _not_ from the
					 * BRIDGE-MIB, then we shouldn't waste time on checking every
					 * possible vlan in the world - i.e. break out of the vlan loop.
					 */
					if (!"BRIDGE-MIB".equals(snmpoid.getMib()))
						break;
					else if (atVlan.size() > 1) {
						Log.d("OID_TESTER", "No response from BRIDGE-MIB oid " + snmpoid.getOidkey() + ", will now test up to " + (atVlan.size()-1) + " vlan(s)");
					}
				}

				if (!supported) {
					Database.update("DELETE FROM netboxsnmpoid WHERE netboxid='"+nb.getNetboxid()+"' AND snmpoidid='"+snmpoid.getSnmpoidid()+"'");
				}
			} } finally { unlock(ip); }

		} catch (SQLException e) {
			Log.e("OID_TESTER", "DO_TEST", "A database error occoured while updating the OID database; please report this to NAV support!");
			Log.d("OID_TESTER", "DO_TEST", "SQLException: " + e.getMessage());
			e.printStackTrace(System.err);
 		} finally {
			Log.setNetbox(null);
		}
	}

	// Returns true if s is not a dupe (has not been checked before)
	private static boolean checkDupe(Netbox nb, Snmpoid snmpoid) {
		synchronized (dupeMap) {
			boolean b1 = dupeMap.put(nb.getKey(), snmpoid.getKey());
			boolean b2 = dupeMap.put(snmpoid.getKey(), nb.getKey());
			return b1 || b2;
		}
	}

	// Clear the type from the dupe cache
	public static void clearDupe(Netbox nb) {
		synchronized (dupeMap) {
			dupeMap.remove(nb.getKey());
		}
	}

	// Clear the snmpoid from the dupe cache
	public static void clearDupe(Snmpoid snmpoid) {
		synchronized (dupeMap) {
			dupeMap.remove(snmpoid.getKey());
		}
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

	public static synchronized Set getLockSet() {
		return new HashSet(lockMap.keySet());
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
