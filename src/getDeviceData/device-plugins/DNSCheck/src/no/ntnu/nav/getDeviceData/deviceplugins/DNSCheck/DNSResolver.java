/*
 * $Id$ 
 *
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
 *
 */
package no.ntnu.nav.getDeviceData.deviceplugins.DNSCheck;

import java.net.InetAddress;
import java.net.UnknownHostException;
import java.util.Hashtable;

import javax.naming.NameNotFoundException;
import javax.naming.NamingException;
import javax.naming.directory.Attribute;
import javax.naming.directory.Attributes;
import javax.naming.directory.DirContext;
import javax.naming.directory.InitialDirContext;

import no.ntnu.nav.logger.Log;

/**
 * A class containing useful DNS resolving methods.
 * Written for getDeviceData's DNSCheck device-plugin.
 * 
 * @version $Id$
 * @author Morten Brekkevold &lt;morten.brekkevold@uninett.no&gt;
 *
 */
public class DNSResolver {

	/**
	 * <p>Attempts to do a DNS reverse lookup for an IP address.</p>
	 * 
	 * <p>First, a regular lookup using java.net is attempted.  This fails
	 * on many systems, and when it does, we try using a JNDI directory lookup
	 * method instead.</p> 
	 * 
	 * @param ip A String containing a properly formatted IP address.
	 * @return A String containing a FQDN host name for the given IP address.
	 *         If the FQDN cannot be determined, the supplied IP address is 
	 *         returned.
	 */
	public static String reverseLookup(String ip) {
		String name =  null;
		try {
			name = javaReverseLookup(ip);
		} catch (UnknownHostException e) {
			Log.e("DNS_REVERSE", "Tried to lookup invalid IP address " + ip);
			return ip;
		}
		if (name.equals(ip)) {
			Log.d("DNS_REVERSE", "InetAddress reverse lookup failed for " + ip + ", trying JNDI lookup");
			try {
				name = jndiReverseLookup(ip);
			} catch (UnknownHostException e) {
				Log.e("DNS_REVERSE", "Tried to lookup invalid IP address " + ip + " twice. This should really never happen!.");
				return ip;
			} catch (NamingException e) {
				if (!(e instanceof NameNotFoundException)) {
					Log.e("DNS_REVERSE", "Unknown JNDI related exception occurred: " + e);
					e.printStackTrace();
				}
				return ip;
			}
		}
		return name;
	}

	/**
	 * <p>Attempt to do a DNS reverse lookup for an IP address, using the 
	 * regular ways of java.net.InetAddress.</p>
	 * 
	 * @param ip A String containing a properly formatted IP address.
	 * @return A String containing a FQDN host name for the given IP address.
	 *         If the FQDN cannot be determined, the supplied IP address is 
	 *         returned.
	 * @throws UnknownHostException If the supplied IP address was not a valid
	 *         IP or host name.
	 */
	public static String javaReverseLookup(String ip) throws UnknownHostException {
		InetAddress address = InetAddress.getByName(ip);
		String name = address.getCanonicalHostName();
		return name;
	}

	/**
	 * <p>Attempt to do a DNS reverse lookup for an IP address, using the JNDI
	 * directory lookup method.</p>
	 * 
	 * @param ip A String containing a properly formatted IP address.
	 * @return A String containing a FQDN host name for the given IP address.
	 * @throws NamingException When the reverse cannot be resolved for some reason.
	 * @throws UnknownHostException If the supplied IP address was not a valid
	 *         IP or host name.
	 */
	public static String jndiReverseLookup(String ip) throws NamingException, UnknownHostException {
		InetAddress address = InetAddress.getByName(ip);

		// Build the lookup string
		String addrstring = "";
		byte[] addrBytes = address.getAddress();
        if (addrBytes.length == 4) {
        	// IPv4 address
    		for (int i=addrBytes.length-1 ; i>=0; i--)
    			addrstring += (addrBytes[i] & 0xFF) + ".";  // build reverse IPv4 address
    		addrstring += "in-addr.arpa";
        } else if (addrBytes.length == 16) {
        	// IPv6 address
    		for (int i=addrBytes.length-1 ; i>=0; i--) { // build reverse IPv6 address
    			String hex = Integer.toHexString(addrBytes[i] & 0xFF);
    			if (hex.length() == 1)
    				hex = "0" + hex;
    			addrstring += hex.charAt(1) + "." + hex.charAt(0) + ".";
    		}
    		addrstring += "ip6.arpa";       
        } // We don't know how to handle any other address lengths, so we'll just fail miserably further down the trail...

		Hashtable env = new Hashtable();
		env.put("java.naming.factory.initial", "com.sun.jndi.dns.DnsContextFactory");

		// Look up a PTR record in the directory
        DirContext ictx = null;
		Attributes attrs = null;
		ictx = new InitialDirContext(env);
		attrs = ictx.getAttributes(addrstring, new String[] {"PTR"});
		Attribute ptr = attrs.get("PTR");
		String hostname = (String) ptr.get(0);
		// Reverse records typically end with a period, we'll chop this off..
		if (hostname.endsWith("."))
			return hostname.substring(0, hostname.length()-1);
		else 
			return hostname;
	}
}
