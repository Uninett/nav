/*
 * BoksReport
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

import java.sql.*;

import no.ntnu.nav.ConfigParser.*;
import no.ntnu.nav.Database.*;
import no.ntnu.nav.SimpleSnmp.*;

/**
 * Describes a netbox and the time used for collecting data from it.
 *
 * @version $LastChangedRevision$ $LastChangedDate$
 * @author Kristian Eide &lt;kreide@online.no&gt;
 */

public class BoksReport implements Comparable
{
	int usedTime;
	BoksData bd;

	public BoksReport(int usedTime, BoksData bd)
	{
		this.usedTime = usedTime;
		this.bd = bd;
	}

	public int getUsedTime() { return usedTime; }
	public BoksData getBoksData() { return bd; }

	public int compareTo(Object o)
	{
		return new Integer(((BoksReport)o).getUsedTime()).compareTo(new Integer(usedTime));
	}
}
