package no.ntnu.nav.SimpleSnmp;

import java.io.*;
import java.util.*;

import uk.co.westhawk.snmp.stack.*;
import uk.co.westhawk.snmp.pdu.*;

/**
 * <p> Class for quering devices via SNMP. The aim of this class is to
 * provide a very simple API for doing basic SNMP walking.  </p>
 *
 * <p> To use first call setBaseOid(), setCs_ro() and setHost()
 * methods (or use setParams() ), then call the getAll() (or getNext()
 * ) method to retrieve values.  </p>
 * 
 */
public class SimpleSnmp
{
	public static final int IFINDEX_OID = 0;
	public static final int IFINDEX_VALUE = 1;
	public static final int IFINDEX_BOTH = 2;

	private final int DEFAULT_TIMEOUT_LIMIT = 4;
	private int timeoutLimit = 4;

	private String host = "127.0.0.1";
	private String cs_ro = "community";
	private String baseOid = "1.3";
	private SnmpContext context = null;
	private int timeoutCnt = 0;
	private boolean gotTimeout = false;

	private Map cache = new HashMap();

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
		return simpleSnmpFactory(null, null);
	}

	public static SimpleSnmp simpleSnmpFactory(String host, String cs_ro, String baseOid) {
		return simpleSnmpFactory(null, null, host, cs_ro, baseOid);
	}

	public static SimpleSnmp simpleSnmpFactory(String vendor, String type) {
		if ("hp".equals(vendor)) return new SimpleSnmpHP();
		return new SimpleSnmp();
	}

	public static SimpleSnmp simpleSnmpFactory(String vendor, String type, String host, String cs_ro, String baseOid) {
		if ("hp".equals(vendor)) return new SimpleSnmpHP(host, cs_ro, baseOid);
		return new SimpleSnmp(host, cs_ro, baseOid);
	}

	public void setHost(String host) { this.host = host; }
	public void setCs_ro(String cs_ro) { this.cs_ro = cs_ro; }
	protected String getCs_ro() { return cs_ro; }
	public void setBaseOid(String baseOid) { this.baseOid = baseOid; }
	public void setParams(String host, String cs_ro, String baseOid)
	{
		setHost(host);
		setCs_ro(cs_ro);
		setBaseOid(baseOid);
	}

	/**
	 * Set how many times the device can time out before a TimeoutException is thrown.
	 */
	public void setTimeoutLimit(int limit)
	{
		timeoutLimit = Math.max(1,limit);
	}

	/**
	 * Set the timeout limit to the default value (currently 4).
	 */
	public void setDefaultTimeoutLimit()
	{
		timeoutLimit = DEFAULT_TIMEOUT_LIMIT;
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
	 * Specify if the OID, the value or both contain the ifindex. This
	 * is important for certain types, e.g. HP, which need to treat the
	 * ifindex special due to unit stacking.
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
	private String strip(String s, char sep, int cnt, boolean front) {
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
		return getAll(baseOid, 0, decodeHex, true, stripCnt);
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
		if (baseOid == null) return null;
		if (baseOid.charAt(0) == '.') baseOid = baseOid.substring(1, baseOid.length());

		ArrayList l = new ArrayList();
		String cacheKey = host+":"+cs_ro+":"+baseOid+":"+decodeHex+":"+getNext+":"+stripCnt;
		if (cache.containsKey(cacheKey)) {
			l.addAll((Collection)cache.get(cacheKey));
			return l;
		}

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
		getCnt = 0;
		cache.put(cacheKey, l);
		return l;
	}

	/**
	 * Check if the SnmpContext is still valid and update it if necessary.
	 *
	 * @return true if the SnmpContext was updated
	 */
	protected boolean checkSnmpContext() throws IOException {
		if (context == null || !context.getHost().equals(host)) {
			if (context != null) context.destroy();
			context = new SnmpContext(host, 161);
			context.setCommunity(cs_ro);
			timeoutCnt = 0;
			return true;
		} else if (!context.getCommunity().equals(cs_ro)) {
				context.setCommunity(cs_ro);
		}
		return false;
	}

	public void finalize()
	{
		if (context != null) {
			context.destroy();
			context = null;
		}
	}

	private static void out(String s) { System.out.print(s); }
	private static void outl(String s) { System.out.println(s); }

	private static void err(String s) { System.err.print(s); }
	private static void errl(String s) { System.err.println(s); }
}

