package no.ntnu.nav.eventengine.deviceplugins.Netel;

import java.util.*;
import java.sql.*;
import no.ntnu.nav.Database.*;

import no.ntnu.nav.eventengine.*;
//import no.ntnu.nav.eventengine.deviceplugins.Box.*;

public class Port
{
	protected static final boolean DEBUG_OUT = true;

	protected int port;
	protected int boksidBehind;
	protected boolean status;


	public Port(ResultSet rs) throws SQLException
	{
		update(rs);
		status = true;
	}

	protected void update(ResultSet rs) throws SQLException
	{
		port = rs.getInt("port");
		boksidBehind = rs.getInt("boksid_behind");
	}

	public int getPort()
	{
		return port;
	}
	public Integer getPortI()
	{
		return new Integer(port);
	}

	public void down()
	{
		status = false;
	}
	public void up()
	{
		status = true;
	}
	public boolean isUp()
	{
		return status;
	}

	public String toString()
	{
		return "Port [port="+port+", boksidBehind="+boksidBehind+"]";
	}



	protected static void outd(Object o) { if (DEBUG_OUT) System.out.print(o); }
	protected static void outld(Object o) { if (DEBUG_OUT) System.out.println(o); }

	protected static void err(Object o) { System.err.print(o); }
	protected static void errl(Object o) { System.err.println(o); }
}