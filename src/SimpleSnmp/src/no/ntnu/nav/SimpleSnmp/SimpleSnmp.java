package no.ntnu.nav.SimpleSnmp;

import java.io.*;
import java.util.*;

import uk.co.westhawk.snmp.stack.*;
import uk.co.westhawk.snmp.pdu.*;

/**
 * <p>
 * Class for quering devices via SNMP. The aim of this class
 * is to provide a very simple API for doing basic SNMP walking.
 * </p>
 *
 * <p>
 * To use first call setBaseOid(), setCs_ro() and setHost() methods (or use setParams() ), then
 * call the getAll() (or getNext() ) method to retrieve values.
 * 
 */
public class SimpleSnmp
{
	private final int DEFAULT_TIMEOUT_LIMIT = 4;
	private int timeoutLimit = 4;

	private String host = "127.0.0.1";
	private String cs_ro = "community";
	private String baseOid = "1.3";
	private SnmpContext context = null;
	private int timeoutCnt = 0;
	private boolean gotTimeout = false;
	private int getCnt;
	private boolean getNext = false;

        /**
         * Construct an empty SimpleSnmp class.
         */
	public SimpleSnmp() { }

        /**
         * Construct a SimpleSnmp class and set initial parameters.
         */
	public SimpleSnmp(String host, String cs_ro, String baseOid)
	{
		setParams(host, cs_ro, baseOid);
	}

	public void setHost(String host) { this.host = host; }
	public void setCs_ro(String cs_ro) { this.cs_ro = cs_ro; }
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

	/*
	public boolean resetGotTimeout() {
		boolean b = gotTimeout;
		gotTimeout = false;
		return b;
	}
	*/

	/**
	 * Snmpwalk the given OID and return a maximum of cnt entries from the subtree
	 *
	 * @param cnt The maximum number of OIDs to get; 0 or less means get as much as possible
	 * @param decodeHex try to decode returned hex to ASCII
	 * @return an ArrayList containing String arrays of two elements; OID and value
	 * @throws TimeoutException if the hosts times out
	 */
	public ArrayList getNext(int cnt, boolean decodeHex) throws TimeoutException
	{
		getCnt = (cnt < 0) ? 0 : cnt;
		return getAll(decodeHex, true);
	}

	/**
	 * Snmpwalk the given OID and return a maximum of cnt entries from the subtree
	 *
	 * @param cnt The maximum number of OIDs to get; 0 or less means get as much as possible
	 * @param decodeHex try to decode returned hex to ASCII
	 * @param getNext Send GETNEXT in first packet, this will not work if you specify an exact OID
	 * @return an ArrayList containing String arrays of two elements; OID and value
	 * @throws TimeoutException if the hosts times out
	 */
	public ArrayList getNext(int cnt, boolean decodeHex, boolean getNext) throws TimeoutException
	{
		getCnt = (cnt < 0) ? 0 : cnt;
		return getAll(decodeHex, getNext);
	}

	/**
	 * Snmpwalk the given OID and return the entire subtree
	 *
	 * @return an ArrayList containing String arrays of two elements; OID and value
	 * @throws TimeoutException if the hosts times out
	 */
	public ArrayList getAll() throws TimeoutException
	{
		return getAll(false, true);
	}

	/**
	 * Snmpwalk the given OID and return the entire subtree
	 *
	 * @param decodeHex Try to decode returned hex to ASCII
	 * @return an ArrayList containing String arrays of two elements; OID and value
	 * @throws TimeoutException if the hosts times out
	 */
	public ArrayList getAll(boolean decodeHex) throws TimeoutException
	{
		return getAll(decodeHex, true);
	}

	/**
	 * Snmpwalk the given OID and return the entire subtree
	 *
	 * @param decodeHex Try to decode returned hex to ASCII
	 * @param getNext Send GETNEXT in first packet, this will not work if you specify an exact OID
	 * @return an ArrayList containing String arrays of two elements; OID and value
	 * @throws TimeoutException if the hosts times out
	 */
	public ArrayList getAll(boolean decodeHex, boolean getNext) throws TimeoutException
	{
		ArrayList l = new ArrayList();
		if (baseOid.charAt(0) == '.') baseOid = baseOid.substring(1, baseOid.length());

		try {
			if (context == null || !context.getHost().equals(host)) {
				if (context != null) context.destroy();
				//outl("Switched context, host: " + host);
				context = new SnmpContext(host, 161);
				context.setCommunity(cs_ro);
				timeoutCnt = 0;
			} else if (!context.getCommunity().equals(cs_ro)) {
				//outl("Community changed: " + cs_ro);
				context.setCommunity(cs_ro);
			}

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
						if (!oid.startsWith(baseOid)) break;

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

						String[] s = {
							oid.length() == baseOid.length() ? oid : oid.substring(baseOid.length()+1, oid.length()),
							data.trim()
						};
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
		return l;
	}

	/*
	public void destroy()
	{
		if (context != null) {
			outl("Context distroyed..");
			context.destroy();
			context = null;
		}
	}
	*/

	public void finalize()
	{
		if (context != null) {
			outl("Context distroyed by finalize.");
			context.destroy();
			context = null;
		}
	}

	private static void out(String s) { System.out.print(s); }
	private static void outl(String s) { System.out.println(s); }

	private static void err(String s) { System.err.print(s); }
	private static void errl(String s) { System.err.println(s); }
}

