/*******************
*
* $Id: BoksData.java,v 1.2 2002/11/22 21:33:59 kristian Exp $
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


public class BoksData
{
	public String ip;
	public String cs_ro;
	public String boksId;
	public String boksTypegruppe;
	public String boksType;
	public String sysName;
	public String kat;
	public int vekt;
}
