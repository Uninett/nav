/*******************
*
* $Id: BoksReport.java,v 1.2 2002/11/22 21:33:59 kristian Exp $
* This file is part of the NAV project.
* Logging of CAM/CDP data
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
