/*******************
*
* This file is part of the NAV project.
* Loging of CAM/CDP data
*
* Copyright (c) 2003 by NTNU, ITEA nettgruppen
* Authors: Kristian Eide <kreide@online.no>
*
*******************/

import java.io.*;
import java.util.*;
import java.net.*;
import java.text.*;

public class PortBoks implements Comparable
{
	String ifindex;

	String to_netboxid;
	String remoteIf;
	String source;

	public PortBoks(String ifindex, String to_netboxid, String source)
	{
		this.ifindex = ifindex.trim();
		this.to_netboxid = to_netboxid.trim();
		this.source = source.trim();
	}

	public String getIfindex() { return ifindex; }
	public String getToNetboxid() { return to_netboxid; }

	public String getSource() { return source; }

	public void setRemoteIf(String s) { remoteIf = s; }
	public String getRemoteIf() { return remoteIf; }

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

		return ifindex.compareTo(pm.ifindex);
	}

	public String toString() { return ifindex+":"+to_netboxid;  }
}
