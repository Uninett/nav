/*******************
*
* $Id: PortBoks.java,v 1.3 2002/11/23 00:32:01 kristian Exp $
* This file is part of the NAV project.
* Loging of CAM/CDP data
*
* Copyright (c) 2002 by NTNU, ITEA nettgruppen
* Authors: Kristian Eide <kreide@online.no>
*
*******************/

import java.io.*;
import java.util.*;
import java.net.*;
import java.text.*;

import java.sql.*;

import no.ntnu.nav.ConfigParser.*;
import no.ntnu.nav.Database.*;
import no.ntnu.nav.SimpleSnmp.*;


public class PortBoks implements Comparable
{
	String modul;
	String port;
	String boksid;
	String source;

	String ifindex;

	String remoteIf;
	String remoteModul = "";
	String remotePort = "";

	public PortBoks(String modul, String port, String boksid, String source)
	{
		this.modul=modul.trim();
		this.port=port.trim();
		this.boksid=boksid.trim();
		this.source=source.trim();
	}

	public String getModulS() { return ((modul.length()==1)?" ":"")+getModul(); }
	public String getPortS() { return ((port.length()==1)?" ":"")+getPort(); }

	public String getModul() { return modul; }
	public String getPort() { return port; }
	public String getBoksId() { return boksid; }

	public String getSource() { return source; }

	public void setIfindex(String s) { ifindex = s; }
	public String getIfindex() { return ifindex; }

	public void setRemoteIf(String s) { remoteIf = s; }
	public String getRemoteIf() { return remoteIf; }

	public void setRemoteMp(String[] s) {
		if (s.length != 2) return;
		remoteModul = s[0].trim();
		remotePort = s[1].trim();
		if (remoteModul.length() == 0 && remotePort.length() > 0) {
			System.err.println("setRemoteMp: remoteModul blank, remotePort: " + remotePort);
			remotePort = "";
		}
	}
	public String getRemoteModul() { return remoteModul; }
	public String getRemotePort() { return remotePort; }

	private Integer sortVal() {
		int v = 0;
		if (source.equals("CDP")) v += 1 << 3;
		if (source.equals("MAC")) v += 1 << 2;
		if (source.equals("DUP")) v += 1 << 1;
		return new Integer(v);
	}

	public int compareTo(Object o) {
		PortBoks pm = (PortBoks)o;

		int c = sortVal().compareTo(pm.sortVal());
		if (c != 0) return c;

		c = modul.compareTo(pm.modul);
		if (c != 0) return c;

		return port.compareTo(pm.port);
	}

	public String toString() { return modul+":"+port+":"+boksid; }
}
