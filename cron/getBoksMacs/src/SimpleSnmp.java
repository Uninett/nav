import java.io.*;
import java.util.*;

import uk.co.westhawk.snmp.stack.*;
import uk.co.westhawk.snmp.pdu.*;


public class SimpleSnmp
{
	private final int TIMEOUT_LIMIT = 4;

	private String host = "127.0.0.1";
	private String cs_ro = "community";
	private String baseOid = "1.3";
	private SnmpContext context = null;
	private int timeoutCnt = 0;

	public SimpleSnmp() { }

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

	public ArrayList getAll() throws TimeoutException
	{
		return getAll(false);
	}

	public ArrayList getAll(boolean decodeHex) throws TimeoutException
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

			//SnmpContext context = new SnmpContext(host, 161);
			BlockPdu pdu = new BlockPdu(context);

			pdu.setPduType(BlockPdu.GETNEXT);
			pdu.addOid(baseOid);

			while (true) {
				try {
					varbind vb;
					while ( (vb=pdu.getResponseVariableBinding()) != null) {
						String oid = vb.getOid().getValue();
						if (!oid.startsWith(baseOid)) break;

						// Reset timeoutCnt
						timeoutCnt = 0;

						// Behandle svaret vi har fått
						String data;
						{
							AsnObject o = vb.getValue();
							if (o instanceof AsnOctets && !decodeHex) {
								AsnOctets ao = (AsnOctets)o;
								//outl("OID: " + oid + " S: " + data + " HEX: " + ao.toHex() );
								data = ao.toHex();
							} else {
								 data = o.toString();
							}
						}
						//outl("OID: " + oid + " = " + data );

						String[] s = {
							oid.substring(baseOid.length()+1, oid.length()).trim(),
							//String.valueOf(vb.getValue()).trim()
							data
						};
						l.add(s);

						pdu = new BlockPdu(context);
						pdu.setPduType(BlockPdu.GETNEXT);
						pdu.addOid(oid);
					}

				} catch (PduException e) {
					String m = e.getMessage();
					if (m.equals("Timed out")) {
						timeoutCnt++;
						if (timeoutCnt >= TIMEOUT_LIMIT) {
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
		return l;
	}

	public void destroy()
	{
		if (context != null) {
			outl("Context distroyed..");
			context.destroy();
			context = null;
		}
	}

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
}

