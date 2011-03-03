/*
 * PortBoks
 * 
 * $LastChangedRevision$
 *
 * $LastChangedDate$
 *
 * Copyright 2002-2004 Norwegian University of Science and Technology
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

import java.io.*;
import java.util.*;
import java.net.*;
import java.text.*;

/**
 * Describes a netbox behind a port.
 *
 * @version $LastChangedRevision$ $LastChangedDate$
 * @author Kristian Eide &lt;kreide@online.no&gt;
 */

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
