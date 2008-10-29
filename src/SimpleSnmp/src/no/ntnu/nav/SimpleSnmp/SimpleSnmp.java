/*
 * $Id$
 *
 * Copyright 2002-2004 Norwegian University of Science and Technology
 * Copyright 2007 UNINETT AS
 * 
 * This file is part of Network Administration Visualized (NAV)
 * 
 * NAV is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 * 
 * NAV is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with NAV; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 */

package no.ntnu.nav.SimpleSnmp;

import java.io.*;
import java.util.*;
import java.net.*;

//import uk.co.westhawk.snmp.stack.*;
//import uk.co.westhawk.snmp.pdu.*;

import snmp.*;

/**
 * <p> Class for quering devices via SNMP. The aim of this class is to
 * provide a very simple API for doing basic SNMP walking.  </p>
 *
 * <p> To use first call setBaseOid(), setCs_ro() and setHost()
 * methods (or use setParams() ), then call the getAll() (or getNext()
 * ) method to retrieve values.  </p>
 *
 * @version $LastChangedRevision$ $LastChangedDate$
 * @author Kristian Eide &lt;kreide@online.no&gt;
 */

public class SimpleSnmp
{
	public static final int IFINDEX_OID = 0;
	public static final int IFINDEX_VALUE = 1;
	public static final int IFINDEX_BOTH = 2;
	public static final int IFINDEX_NONE = 3;
	public static final int IFINDEX_DEFAULT = IFINDEX_OID;

	private static final int DEFAULT_RETRIES = 4;
	private int retries = DEFAULT_RETRIES;
	private int backoff = 2;

	private String host = "127.0.0.1";
	private String cs_ro = "community";
	private String baseOid = "1.3";
	private int timeoutCnt = 0;
	private boolean gotTimeout = false;
	private long getNextDelay = 0;
	private int socketTimeout = 1000; // milliseconds
	private int snmpVersion = 0;

	private SNMPv1CommunicationInterface comInterface = null;
	private boolean valid = false;
	//private SnmpContext context = null;


	private Map cache = new HashMap();

	protected Set ignoredModules = new HashSet();

	/**
	 * Construct an empty SimpleSnmp class.
	 */
	protected SimpleSnmp() {
	}
	
	/**
	 * Construct a SimpleSnmp class and set initial parameters.
	 */
	protected SimpleSnmp(String host, String cs_ro, String baseOid) {
		setParams(host, cs_ro, baseOid);
	}

	public static SimpleSnmp simpleSnmpFactory() {
		return new SimpleSnmp();
	}

	public static SimpleSnmp simpleSnmpFactory(String host, String cs_ro, String baseOid) {
		return new SimpleSnmp(host, cs_ro, baseOid);
	}

	/**
	 * @deprecated SimpleSnmp no longer perform special handling for different types or vendors
	 */
	public static SimpleSnmp simpleSnmpFactory(String vendor, String type) {
		return SimpleSnmp.simpleSnmpFactory();
	}

	/**
	 * @deprecated SimpleSnmp no longer perform special handling for different types or vendors
	 */
	public static SimpleSnmp simpleSnmpFactory(String vendor, String type, String host, String cs_ro, String baseOid) {
		return SimpleSnmp.simpleSnmpFactory(vendor, type, host, cs_ro, baseOid);
	}

	public void setHost(String host) { if (!this.host.equals(host)) valid=false; this.host = host; }
	public void setCs_ro(String cs_ro) { if (!this.cs_ro.equals(cs_ro)) valid=false; this.cs_ro = cs_ro; }
	protected String getCs_ro() { return cs_ro; }
	public void setBaseOid(String baseOid) { this.baseOid = baseOid; }
	public void setParams(String host, String cs_ro, String baseOid)
	{
		setHost(host);
		setCs_ro(cs_ro);
		setBaseOid(baseOid);
	}

	/**
	 * Set the SNMP version to use.
	 * @param version 1 = SNMPv1, 2 = SNMPv2c.
	 */	
	public void setSnmpVersion(int version) {
		if (version < 1 || version > 2) throw new RuntimeException("Invalid SNMP version: " + version);
		version--;
		if (snmpVersion != version) {
			valid = false;
			snmpVersion = version;
		}
	}

	/**
	 * Return the SNMP version used for communication by this instance.
	 * @return 1 for SNMP v1 and 2 for SNMP v2c
	 */
	public int getSnmpVersion() {
		return snmpVersion+1;
	}

	/**
	 * Set the delay, in ms, between getNext requests.
	 */
	public void setGetNextDelay(long delay)
	{
		getNextDelay = delay;
	}

	/**
	 * Set how many times the device can time out before a TimeoutException is thrown.
	 * 
	 * @deprecated Use the more aptly named {@link #setRetries(int)} method.
	 */
	public void setTimeoutLimit(int limit)
	{
		setRetries(limit);
	}

	/**
	 * Set the timeout limit to the default value (currently 4).
	 * 
	 * @deprecated Use the more aptly named {@link #setDefaultRetries()} method.
	 */
	public void setDefaultTimeoutLimit()
	{
		setDefaultRetries();
	}

	/**
	 * Set the number of times the device may time out before a TimeoutException is thrown.
	 */
	public void setRetries(int limit)
	{
		retries = Math.max(1,limit);
	}

	/**
	 * Set the number of retries to the default value, as defined by the static value DEFAULT_RETRIES
	 */
	public void setDefaultRetries()
	{
		retries = DEFAULT_RETRIES;
	}

	/**
	 * Set the UDP socket timeout for the following requests.
	 * @param socketTimeout A value in milliseconds.
	 */
	public void setSocketTimeout(int socketTimeout)
	{
		this.socketTimeout = socketTimeout;
	}

	/**
	 * Use this method to specify that only the module with the given
	 * module number should be asked for data. Note that this
	 * information is only respected if this class is subclassed; the
	 * default is to do nothing.
	 *
	 * @param module The number of the module to ask; use null to again ask all modules
	 */
	public void onlyAskModule(String module) {

	}

	/**
	 * Use this method to specify that the given module should be
	 * ignored and not collected data for. This is useful if the
	 * module is down and would only give timeout exceptions. Note
	 * that this information is only respected if this class is
	 * subclassed; the default is to do nothing.
	 *
	 * @param module The number of the module to ignore.
	 */
	public void ignoreModule(String module) {
		ignoredModules.add(module);
	}

	/**
	 * Specify if the ifindex is contained in the OID, the value,
	 * both, or there is no ifindex. This is important for certain
	 * types, e.g. HP, which need to treat the ifindex special due to
	 * unit stacking.
	 */
	public void setIfindexIs(int ifindexIs) {
		
	}

	/*
	public boolean resetGotTimeout() {
		boolean b = gotTimeout;
		gotTimeout = false;
		return b;
	}
	*/

	/**
	 * <p> Snmpwalk the given OID and return a maximum of cnt entries
	 * from the subtree.  </p>
	 *
	 * <p> Note: the baseOid prefix will be removed from any returned
	 * OIDs.  </p>
	 *
	 * @param getCnt The maximum number of OIDs to get; 0 or less means get as much as possible
	 * @param decodeHex try to decode returned hex to ASCII
	 * @return an ArrayList containing String arrays of two elements; OID and value
	 * @throws TimeoutException if the hosts times out
	 */
	public ArrayList getNext(int getCnt, boolean decodeHex) throws TimeoutException
	{
		return getAll(baseOid, getCnt, decodeHex, true, 0);
	}

	/**
	 * <p> Snmpwalk the given OID and return a maximum of cnt entries
	 * from the subtree.  </p>
	 *
	 * <p> Note: the baseOid prefix will be removed from any returned
	 * OIDs.  </p>
	 *
	 * @param getCnt The maximum number of OIDs to get; 0 or less means get as much as possible
	 * @param decodeHex try to decode returned hex to ASCII
	 * @param getNext Send GETNEXT in first packet, this will not work if you specify an exact OID
	 * @return an ArrayList containing String arrays of two elements; OID and value
	 * @throws TimeoutException if the hosts times out
	 */
	public ArrayList getNext(int getCnt, boolean decodeHex, boolean getNext) throws TimeoutException
	{
		return getAll(baseOid, getCnt, decodeHex, getNext, 0);
	}

	/**
	 * <p> Snmpwalk the given OID and return a maximum of cnt entries
	 * from the subtree.  </p>
	 *
	 * @param getCnt The maximum number of OIDs to get; 0 or less means get as much as possible
	 * @param decodeHex try to decode returned hex to ASCII
	 * @param getNext Send GETNEXT in first packet, this will not work if you specify an exact OID
	 * @param stripPrefix Strip baseOid prefix from response OIDs if true
	 * @return an ArrayList containing String arrays of two elements; OID and value
	 * @throws TimeoutException if the hosts times out
	 */
	public ArrayList getNext(int getCnt, boolean decodeHex, boolean getNext, boolean stripPrefix) throws TimeoutException
	{
		return getAll(baseOid, getCnt, decodeHex, getNext, stripPrefix, 0);
	}

	/**
	 * <p> Snmpwalk the given OID and return a maximum of cnt entries
	 * from the subtree.  </p>
	 *
	 * <p> Note: the baseOid prefix will be removed from any returned
	 * OIDs.  </p>
	 *
	 * @param baseOid Override the baseOid; if null a null value is returned
	 * @param getCnt The maximum number of OIDs to get; 0 or less means get as much as possible
	 * @param decodeHex try to decode returned hex to ASCII
	 * @param getNext Send GETNEXT in first packet, this will not work if you specify an exact OID
	 * @return an ArrayList containing String arrays of two elements; OID and value
	 * @throws TimeoutException if the hosts times out
	 */
	public ArrayList getNext(String baseOid, int getCnt, boolean decodeHex, boolean getNext) throws TimeoutException
	{
		return getAll(baseOid, getCnt, decodeHex, getNext, 0);
	}

	/**
	 * <p> Snmpwalk the given OID and return the entire subtree as a
	 * Map.  </p>
	 *
	 * <p> Note: the baseOid prefix will be removed from any returned
	 * OIDs.  </p>
	 *
	 * @param baseOid Override the baseOid; if null a null value is returned
	 * @return a Map which maps the OIDs to their corresponding values
	 * @throws TimeoutException if the hosts times out
	 */
	public Map getAllMap(String baseOid) throws TimeoutException
	{
		return getAllMap(baseOid, false, 0);
	}

	/**
	 * <p> Snmpwalk the given OID and return the entire subtree as a
	 * Map.  </p>
	 *
	 * <p> Note: the baseOid prefix will be removed from any returned
	 * OIDs.  </p>
	 *
	 * @param baseOid Override the baseOid; if null a null value is returned
	 * @param decodeHex try to decode returned hex to ASCII
	 * @return a Map which maps the OIDs to their corresponding values
	 * @throws TimeoutException if the hosts times out
	 */
	public Map getAllMap(String baseOid, boolean decodeHex) throws TimeoutException
	{
		return getAllMap(baseOid, decodeHex, 0);
	}

	/**
	 * <p> Snmpwalk the given OID and return the entire subtree as a
	 * Map.  </p>
	 *
	 * <p> Note: the baseOid prefix will be removed from any returned
	 * OIDs.  </p>
	 *
	 * @param baseOid Override the baseOid; if null a null value is returned
	 * @param decodeHex try to decode returned hex to ASCII
	 * @param stripCnt Strip this many elements (separated by .) from the start of OIDs
	 * @return a Map which maps the OIDs to their corresponding values
	 * @throws TimeoutException if the hosts times out
	 */
	public Map getAllMap(String baseOid, boolean decodeHex, int stripCnt) throws TimeoutException
	{
		List l = getAll(baseOid, decodeHex);
		if (l == null) return null;

		Map m = new HashMap();
		for (Iterator it = l.iterator(); it.hasNext();) {
			String[] s = (String[])it.next();
			s[0] = strip(s[0], '.', stripCnt, true);
			m.put(s[0], s[1]);
		}
		return m;
	}

	/**
	 * <p> Snmpwalk the given OID and return the entire subtree as a
	 * Map. Includes the option to ask for a map from OID to module to
	 * be included, but the default implementation ignores this.  </p>
	 *
	 * <p> Note: the baseOid prefix will be removed from any returned
	 * OIDs.  </p>
	 *
	 * @param baseOid Override the baseOid; if null a null value is returned
	 * @param decodeHex try to decode returned hex to ASCII
	 * @param stripCnt Strip this many elements (separated by .) from the start of OIDs
	 * @return a Map which maps the OIDs to their corresponding values
	 * @throws TimeoutException if the hosts times out
	 */
	public Map getAllMap(String baseOid, boolean decodeHex, int stripCnt, boolean oidToModuleMap) throws TimeoutException
	{
		return getAllMap(baseOid, decodeHex, stripCnt);
	}

	/**
	 * <p> Snmpwalk the given OID and return the entire subtree as a
	 * Map; the OIDs are mapped to a {@link java.util.List List} of
	 * values.  </p>
	 *
	 * <p> Note: the baseOid prefix will be removed from any returned
	 * OIDs.  </p>
	 *
	 * @param baseOid Override the baseOid; if null a null value is returned
	 * @return a Map which maps the OIDs to a List of corresponding values
	 * @throws TimeoutException if the hosts times out
	 */
	public Map getAllMapList(String baseOid) throws TimeoutException {
		return getAllMapList(baseOid, 0);
	}

	/**
	 * <p> Snmpwalk the given OID and return the entire subtree as a
	 * Map; the OIDs are mapped to a {@link java.util.List List} of
	 * values.  </p>
	 *
	 * <p> Note: the baseOid prefix will be removed from any returned
	 * OIDs.  </p>
	 *
	 * @param baseOid Override the baseOid; if null a null value is returned
	 * @param stripCnt Strip this many elements (separated by .) from the end OIDs
	 * @return a Map which maps the OIDs to a List of corresponding values
	 * @throws TimeoutException if the hosts times out
	 */
	public Map getAllMapList(String baseOid, int stripCnt) throws TimeoutException {
		List l = getAll(baseOid);
		return listToMapList(l, stripCnt);
	}
	
	/**
	 * <p> Convert a list of two-element String arrays to a Map of
	 * Lists, stripping the first stripCnt elements (separated by .)
	 * from the first String in the array.  </p>
	 *
	 * <p> If the String array contains 3 elements, the third will be
	 * prepended to the first after stripping.  </p>
	 */
	protected Map listToMapList(List l, int stripCnt) {
		if (l == null) return null;
		Map m = new HashMap();
		for (Iterator it = l.iterator(); it.hasNext();) {
			String[] s = (String[])it.next();

			s[0] = strip(s[0], '.', stripCnt, false);
			s[0] = convertToIfIndex(s);

			List vl;
			if ( (vl=(List)m.get(s[0])) == null) m.put(s[0], vl=new ArrayList());
			vl.add(s[1]);
		}
		return m;
	}

	// Strip elements from string s
	protected String strip(String s, char sep, int cnt, boolean front) {
		if (cnt > 0) {
			int p = 0, k = 0;
			for (int i=0; i < cnt; i++) {
				k = s.indexOf(sep, p);
				if (k < 0) break;
				p = k+1;
			}
			if (front) {
				if (p > 0) s = s.substring(0, p-1);
			} else {
				s = s.substring(p, s.length());
			}
		}
		return s;
	}


	/**
	 * Get the ifIndex from the String array. Subclasses can override
	 * this to do special processing; the default is just to return the
	 * first element.
	 */
	protected String convertToIfIndex(String[] s) {
		return convertToIfIndex(s, 0);
	}

	/**
	 * Get the ifIndex from the String array. Subclasses can override
	 * this to do special processing; the default is just to return the
	 * <i>i</i>th element.
	 *
	 * @param idx Index in string array of the ifindex to be converted
	 */
	protected String convertToIfIndex(String[] s, int idx) {
		return s[idx];
	}

	/**
	 * Extract the OID part of the ifindex; this value should be
	 * suitable for adding to an OID for collecting data for a specific
	 * ifindex.
	 */
	public String extractIfIndexOID(String ifindex) {
		return ifindex;
	}

	/**
	 * Remove any module-specific parts from the sysname.
	 */
	public String extractSysname(String sysname, String module) {
		return sysname;
	}

	/**
	 * <p> Snmpwalk the given OID and return the entire subtree.  </p>
	 *
	 * <p> Note: the baseOid prefix will be removed from any returned
	 * OIDs.  </p>
	 *
	 * @return an ArrayList containing String arrays of two elements; OID and value
	 * @throws TimeoutException if the hosts times out
	 */
	public ArrayList getAll() throws TimeoutException	{
		return getAll(false, true);
	}

	/**
	 * <p> Snmpwalk the given OID and return the entire subtree.  </p>
	 *
	 * <p> Note: the baseOid prefix will be removed from any returned
	 * OIDs.  </p>
	 *
	 * @param baseOid Override the baseOid; if null a null value is returned
	 * @return an ArrayList containing String arrays of two elements; OID and value
	 * @throws TimeoutException if the hosts times out
	 */
	public ArrayList getAll(String baseOid) throws TimeoutException	{
		return getAll(baseOid, false, true);
	}

	/**
	 * <p> Snmpwalk the given OID and return the entire subtree.  </p>
	 *
	 * <p> Note: the baseOid prefix will be removed from any returned
	 * OIDs.  </p>
	 *
	 * @param decodeHex Try to decode returned hex to ASCII
	 * @return an ArrayList containing String arrays of two elements; OID and value
	 * @throws TimeoutException if the hosts times out
	 */
	public ArrayList getAll(boolean decodeHex) throws TimeoutException {
		return getAll(decodeHex, true);
	}

	/**
	 * <p> Snmpwalk the given OID and return the entire subtree.  </p>
	 *
	 * <p> Note: the baseOid prefix will be removed from any returned
	 * OIDs.  </p>
	 *
	 * @param baseOid Override the baseOid; if null a null value is returned
	 * @param decodeHex Try to decode returned hex to ASCII
	 * @return an ArrayList containing String arrays of two elements; OID and value
	 * @throws TimeoutException if the hosts times out
	 */
	public ArrayList getAll(String baseOid, boolean decodeHex) throws TimeoutException {
		return getAll(baseOid, decodeHex, true);
	}

	/**
	 * <p> Snmpwalk the given OID and return the entire subtree.  </p>
	 *
	 * <p> Note: the baseOid prefix will be removed from any returned
	 * OIDs.  </p>
	 *
	 * @param baseOid Override the baseOid; if null a null value is returned
	 * @param decodeHex Try to decode returned hex to ASCII
	 * @param stripCnt Strip this many elements (separated by .) from the start of OIDs
	 * @return an ArrayList containing String arrays of two elements; OID and value
	 * @throws TimeoutException if the hosts times out
	 */
	public ArrayList getAll(String baseOid, boolean decodeHex, int stripCnt) throws TimeoutException {
		return getAll(baseOid, 0, decodeHex, true, true, stripCnt);
	}

	/**
	 * <p> Snmpwalk the given OID and return the entire subtree.  </p>
	 *
	 * <p> Note: the baseOid prefix will be removed from any returned
	 * OIDs.  </p>
	 *
	 * @param decodeHex Try to decode returned hex to ASCII
	 * @param getNext Send GETNEXT in first packet, this will not work if you specify an exact OID
	 * @return an ArrayList containing String arrays of two elements; OID and value
	 * @throws TimeoutException if the hosts times out
	 */
	public ArrayList getAll(boolean decodeHex, boolean getNext) throws TimeoutException	{
		return getAll(baseOid, decodeHex, getNext);
	}

	/**
	 * <p> Snmpwalk the given OID and return the entire subtree.  </p>
	 *
	 * <p> Note: the baseOid prefix will be removed from any returned
	 * OIDs.  </p>
	 *
	 * @param baseOid Override the baseOid; if null a null value is returned
	 * @param decodeHex Try to decode returned hex to ASCII
	 * @param getNext Send GETNEXT in first packet, this will not work if you specify an exact OID
	 * @return an ArrayList containing String arrays of two elements; OID and value
	 * @throws TimeoutException if the hosts times out
	 */
	public ArrayList getAll(String baseOid, boolean decodeHex, boolean getNext) throws TimeoutException {
		return getAll(baseOid, 0, decodeHex, getNext, 0);
	}

	/**
	 * <p> Snmpwalk the given OID and return the entire subtree.  </p>
	 *
	 * <p> Note: the baseOid prefix will be removed from any returned
	 * OIDs.  </p>
	 * 
	 * @param baseOid Override the baseOid; if null a null value is returned
	 * @param getCnt The maximum number of OIDs to get; 0 or less means get as much as possible
	 * @param decodeHex Try to decode returned hex to ASCII
	 * @param getNext Send GETNEXT in first packet, this will not work if you specify an exact OID
	 * @param stripCnt Strip this many elements (separated by .) from the start of OIDs
	 * @return an ArrayList containing String arrays of two elements; OID and value
	 * @throws TimeoutException if the hosts times out
	 */
	public ArrayList getAll(String baseOid, int getCnt, boolean decodeHex, boolean getNext, int stripCnt) throws TimeoutException {
		return getAll(baseOid, getCnt, decodeHex, getNext, true, stripCnt);
	}
	
	/**
	 * <p> Snmpwalk the given OID and return the entire subtree.  </p>
	 *
	 * @param baseOid Override the baseOid; if null a null value is returned
	 * @param getCnt The maximum number of OIDs to get; 0 or less means get as much as possible
	 * @param decodeHex Try to decode returned hex to ASCII
	 * @param getNext Send GETNEXT in first packet, this will not work if you specify an exact OID
	 * @param stripPrefix Strip baseOid prefix from response OIDs if true
	 * @param stripCnt Strip this many elements (separated by .) from the start of OIDs
	 * @return an ArrayList containing String arrays of two elements; OID and value
	 * @throws TimeoutException if the hosts times out
	 */
	public ArrayList getAll(String baseOid, int getCnt, boolean decodeHex, boolean getNext, boolean stripPrefix, int stripCnt) throws TimeoutException {
		if (baseOid == null) return null;
		if (baseOid.charAt(0) == '.') baseOid = baseOid.substring(1, baseOid.length());

		String cacheKey = host+":"+cs_ro+":"+baseOid+":"+decodeHex+":"+getNext+":"+stripPrefix+":"+stripCnt;
		if (cache.containsKey(cacheKey)) {
			return new ArrayList((Collection)cache.get(cacheKey));
		}

		ArrayList l = getAllJavaSnmp(baseOid, getCnt, decodeHex, getNext, stripPrefix, stripCnt, socketTimeout);
		cache.put(cacheKey, l);
		return l;
	}

	private ArrayList getAllJavaSnmp(String baseOid, int getCnt, boolean decodeHex, boolean getNext, boolean stripPrefix, int stripCnt, int timeout) throws TimeoutException {
		ArrayList l = new ArrayList();

		try {
			checkSnmpContext();
			if (timeout < 1) timeout = 1000; // Prevent infinite waiting for response
			comInterface.setSocketTimeout(timeout);
			
			// Should we get the entire subtree?
			boolean getAll = getCnt == 0;

			SNMPVarBindList	var = null;
			boolean timedOut = false;
			try {
				if (getNext) {
					if (getAll) {
						// Do our own subtree walk routine, to avoid a known bug in drexel snmp
						var = new SNMPVarBindList();
						String nextoid = baseOid;
						while (true) {
							SNMPVarBindList nextpair = comInterface.getNextMIBEntry(nextoid);
							SNMPObject snmpobj = nextpair.getSNMPObjectAt(0);
							if (snmpobj instanceof SNMPNull) break;
							SNMPSequence pair = (SNMPSequence)snmpobj;
							SNMPObjectIdentifier snmpOID = (SNMPObjectIdentifier)pair.getSNMPObjectAt(0);
							nextoid = snmpOID.toString();
							if (!nextoid.startsWith(baseOid) || nextoid.equals(baseOid)) break;
							
							var.addSNMPObject(pair);
						}
					} else {
						var = new SNMPVarBindList();
						String nextoid = baseOid;
						for (int i=0; i < getCnt; i++) {
							SNMPVarBindList nextpair = comInterface.getNextMIBEntry(nextoid);
							SNMPObject snmpobj = nextpair.getSNMPObjectAt(0);
							if (snmpobj instanceof SNMPNull) break;
							SNMPSequence pair = (SNMPSequence)snmpobj;
							SNMPObjectIdentifier snmpOID = (SNMPObjectIdentifier)pair.getSNMPObjectAt(0);
							nextoid = snmpOID.toString();

							var.addSNMPObject(pair);
						}
					}
				} else {
					var = comInterface.getMIBEntry(baseOid);
				}
			} catch (SocketTimeoutException exp) {
				timedOut = true;
			} catch (SNMPBadValueException exp) {
				System.err.println("SNMPBadValueException: " + exp);
				return l;
			} catch (SNMPException exp) {
				if (!(exp instanceof SNMPGetException && exp.getMessage() != null && exp.getMessage().indexOf("not available for retrieval") >= 0)) {
					System.err.println("SNMPException: " + exp);
				}
				return l;
			}

			if (timedOut) {
				timeoutCnt++;
				if (timeoutCnt >= retries) {
					throw new TimeoutException("Timed out " + timeoutCnt + " times, giving up");
				} else {
					// Re-try operation, but back off on the timeout value
					return getAllJavaSnmp(baseOid, getCnt, decodeHex, getNext, stripPrefix, stripCnt, timeout*backoff);
				}
			}
			timeoutCnt = 0;

			for (int i=0; i < var.size(); i++) {
				SNMPSequence pair = (SNMPSequence)(var.getSNMPObjectAt(i));
				SNMPObjectIdentifier snmpOID = (SNMPObjectIdentifier)pair.getSNMPObjectAt(0);
				SNMPObject snmpValue = pair.getSNMPObjectAt(1);

				String oid = snmpOID.toString();
				String data;
				if (!decodeHex && snmpValue instanceof SNMPOctetString) {
					data = toHexString((byte[])snmpValue.getValue());					
				} else {
					data = snmpValue.toString();
				}
				data = data.trim();
				if (data.length() == 0 && !(snmpValue instanceof SNMPOctetString)) {
					// Skip empty variables which are not strings
					continue;
				}
				String strippedOid = stripPrefix && oid.startsWith(baseOid) ? oid.substring(baseOid.length()) : oid;
				String[] s = {
					strippedOid.length() > 0 && strippedOid.charAt(0) == '.' ? strippedOid.substring(1) : strippedOid,
					data
				};
				s[0] = strip(s[0], '.', stripCnt, true);
				l.add(s);				
			}

		} catch (IOException e) {
			outl("  *ERROR*: Host: " + host + " IOException: " + e.getMessage() );
			e.printStackTrace(System.err);
		}
		getCnt = 0;
		return l;
	}

	private String toHexString(byte[] bytes) {
		StringBuffer sb = new StringBuffer();
		int[] ints = new int[bytes.length];
		for (int i=0; i < ints.length; i++) ints[i] = bytes[i] < 0 ? 256 + bytes[i] : bytes[i];
		for (int i=0; i < ints.length; i++) sb.append((i>0?":":"")+(ints[i]<16?"0":"")+Integer.toString(ints[i], 16));
		return sb.toString();
	}

	private ArrayList getAllWesthawk(String baseOid, int getCnt, boolean decodeHex, boolean getNext, int stripCnt) throws TimeoutException {
		ArrayList l = new ArrayList();

		/*
		try {
			checkSnmpContext();

			BlockPdu pdu = new BlockPdu(context);

			pdu.addOid(baseOid);
			pdu.setPduType(getNext ? BlockPdu.GETNEXT : BlockPdu.GET);

			boolean sentGetNext = getNext;
			String oid = baseOid;

			// Should we get the entire subtree?
			boolean getAll = getCnt == 0;

			while (true) {
				try {
					varbind vb;
					while ( (vb=pdu.getResponseVariableBinding()) != null) {
						oid = vb.getOid().getValue();
						if (!baseOid.equals(oid) && !oid.startsWith(baseOid+".")) break;

						// Reset timeoutCnt
						timeoutCnt = 0;

						// Behandle svaret vi har fått
						String data;
						{
							AsnObject o = vb.getValue();
							if (o instanceof AsnOctets) {
								AsnOctets ao = (AsnOctets)o;
								data = (decodeHex ? ao.toDisplayString() : ao.toHex());

								//outl("OID: " + oid + " S: " + data + " HEX: " + ao.toHex() );
							} else {
								 data = o.toString();
							}
							data = data.trim();
						}
						//outl("Base: " + baseOid);
						//outl("Oid : " + oid);

						// If the returned OID is of greater length than the baseOid, remove the baseOid prefix;
						// otherwise, use the empty string
						String[] s = {
							oid.length() == baseOid.length() ? "" : oid.substring(baseOid.length()+1, oid.length()),
							data.trim()
						};
						s[0] = strip(s[0], '.', stripCnt, true);
						l.add(s);

						if (!getAll && --getCnt == 0) break;

						pdu = new BlockPdu(context);
						pdu.setPduType(BlockPdu.GETNEXT);
						pdu.addOid(oid);
						if (getNextDelay > 0) {
							try {
								//System.err.println("Sleeping " + getNextDelay + " ms.");
								Thread.currentThread().sleep(getNextDelay);
							} catch (InterruptedException e) {
							}
						}
					}

				} catch (PduException e) {
					String m = e.getMessage();
					if (m.equals("No such name error")) {
						if (!sentGetNext) {
							pdu = new BlockPdu(context);
							pdu.setPduType(BlockPdu.GETNEXT);
							pdu.addOid(oid);
							sentGetNext = true;
							continue;
						}
					}
					else if (m.equals("Timed out")) {
						gotTimeout = true;
						timeoutCnt++;
						if (timeoutCnt >= timeoutLimit) {
							throw new TimeoutException("Too many timeouts, giving up");
						} else {
							// Re-try operation
							continue;
						}
					} else {
						outl("  *ERROR*: Host: " + host + " PduExecption: " + e.getMessage() );
					}
				}

				// Ferdig å hente meldinger
				break;

			} // while
		} catch (IOException e) {
			outl("  *ERROR*: Host: " + host + " IOException: " + e.getMessage() );
		}
		*/
		getCnt = 0;
		return l;
	}

	/**
	 * Check if the SnmpContext is still valid and update it if necessary.
	 *
	 * @return true if the SnmpContext was updated
	 */
	protected boolean checkSnmpContext() throws IOException {
		if (comInterface == null || !valid) {
			if (comInterface != null) comInterface.closeConnection();
			InetAddress hostAddress = InetAddress.getByName(host);
			comInterface = new SNMPv1CommunicationInterface(snmpVersion, hostAddress, cs_ro);
			if (this.socketTimeout > 0) comInterface.setSocketTimeout(this.socketTimeout);
			timeoutCnt = 0;
			valid = true;
			return true;
		}
		return false;
	}

	/**
	 * Check if the SnmpContext is still valid and update it if necessary.
	 *
	 * @return true if the SnmpContext was updated
	 */
	/*
	protected boolean checkSnmpContext2() throws IOException {
		if (context == null || !context.getHost().equals(host)) {
			if (context != null) context.destroy();
			//Exception e = new Exception("["+super.toString()+"] ["+Integer.toHexString(Thread.currentThread().hashCode())+"]");
			//e.printStackTrace(System.err);
			context = new SnmpContext(host, 161);
			//System.err.println("+++Creating context: " + context);
			context.setCommunity(cs_ro);
			timeoutCnt = 0;
			return true;
		} else if (!context.getCommunity().equals(cs_ro)) {
			context.setCommunity(cs_ro);
		}
		return false;
	}
	*/

	/**
	 * Deallocate any resources used.
	 */
	public void destroy() {
		if (comInterface != null) {
			try {
				comInterface.closeConnection();
			} catch (SocketException exp) {
			}
			comInterface = null;
		}
	}

	/**
	 * Deallocate any resources used.
	 */
	/*
	public void destroy2() {
		//Exception e = new Exception("["+super.toString()+"] ["+Integer.toHexString(Thread.currentThread().hashCode())+"]: " + context);
		//e.printStackTrace(System.err);
		if (context != null) {
			//System.err.println("---Destroying context: " + context);
			context.destroy();
			context = null;
		}
	}
	*/

	/**
	 * Check which version of SNMP the active device supports and set it active.
	 */
	public int checkSnmpVersion() {
		// First we check if the device can support SNMPv2
		onlyAskModule("0");
		setSnmpVersion(2);
		int snmpVersion = 1;
		try {
			getNext("1", 1, false, true);
			snmpVersion = 2;
		} catch (Exception e) {
			setSnmpVersion(1);
		} finally {
			onlyAskModule(null);
		}
		return snmpVersion;
	}

	public void finalize() {
		destroy();
	}

	private static void out(String s) { System.out.print(s); }
	private static void outl(String s) { System.out.println(s); }

	private static void err(String s) { System.err.print(s); }
	private static void errl(String s) { System.err.println(s); }

	/**
	 * @return The backoff factor
	 * @see #setBackoff(int)
	 */
	public int getBackoff() {
		return backoff;
	}

	/**
	 * Sets the backoff factor for retries.
	 * 
	 * <p>Whenever a request times out, the timeout limit 
	 * of each retry attempt will be multiplied by this factor.
	 * If set to 1, no timeout backoff will occur.</p>
	 * 
	 *  <p>The default factor is 2.</p>
	 * 
	 * @param backoff An integer backoff factor.
	 */
	public void setBackoff(int backoff) {
		this.backoff = backoff;
	}
}

