package no.ntnu.nav.eventengine.deviceplugins.Netel;

import java.util.*;
import java.sql.*;
import no.ntnu.nav.Database.*;

import no.ntnu.nav.eventengine.*;
//import no.ntnu.nav.eventengine.deviceplugins.Box.*;

public class Port
{
	protected static final boolean DEBUG_OUT = true;

	public final static int DIRECTION_NONE = 0;
	public final static int DIRECTION_BLOCKED = 1;
	public final static int DIRECTION_DOWN = 2;
	public final static int DIRECTION_UP = 3;
	public final static int DIRECTION_UNKNOWN = 4;


	protected int ifindex;
	protected int port;
	protected int boxidBehind;
	protected boolean status;
	protected Vlan[] vlan;

	private class Vlan
	{
		public int vlan;
		public int direction;

		public Vlan(int vlan, char direction)
		{
			this.vlan = vlan;
			this.direction = charToDirection(direction);
		}

		private int charToDirection(char c)
		{
			switch (c) {
				case 'b': return DIRECTION_BLOCKED;
				case 'n': return DIRECTION_DOWN;
				case 'o': return DIRECTION_UP;
				case 'u': return DIRECTION_UNKNOWN;
				case 'x': return DIRECTION_UNKNOWN;
			}
			errl("Port.Vlan.charToDirection: Warning, unknown direction: " + c);
			return DIRECTION_UNKNOWN;
		}
		private char directionToChar(int d)
		{
			switch (d) {
				case DIRECTION_BLOCKED: return 'b';
				case DIRECTION_DOWN: return 'n';
				case DIRECTION_UP: return 'o';
			}
			return 'x';
		}

		public String toString()
		{
			return vlan+"("+directionToChar(direction)+")";
		}
	}


	public Port(ResultSet rs) throws SQLException
	{
		update(rs);
		status = true;
	}

	void update(ResultSet rs) throws SQLException
	{
		// These are needed for knowing when we are done with the port
		int parentDeviceid = rs.getInt("parent_deviceid");
		String moduleName = rs.getString("name");

		ifindex = rs.getInt("ifindex");
		port = rs.getInt("port");
		boxidBehind = rs.getInt("to_netboxid");

		List vl = new ArrayList();
		do {
			char dir = rs.getString("direction") == null ? 'x' : rs.getString("direction").charAt(0);
			vl.add(new Vlan(rs.getInt("vlan"), dir));
			//errl("Debug   Port: New vlan: " + vl.get(vl.size()-1));
		} while (rs.next() && rs.getInt("parent_deviceid") == parentDeviceid && rs.getString("name").equals(moduleName) && rs.getInt("ifindex") == ifindex);
		rs.previous();

		vlan = new Vlan[vl.size()];
		for (int i=0; i < vl.size(); i++) vlan[i] = (Vlan)vl.get(i);
	}

	Integer getKey()
	{
		return new Integer(ifindex);
	}
	static Integer getKey(ResultSet rs) throws SQLException
	{
		return new Integer(rs.getInt("ifindex"));
	}

	public int getIfindex()
	{
		return ifindex;
	}
	public Integer getIfindexI()
	{
		return new Integer(ifindex);
	}
	public int getPort()
	{
		return port;
	}
	public Integer getPortI()
	{
		return new Integer(port);
	}
	public int getBoxidBehind()
	{
		return boxidBehind;
	}

	public int vlanDirection(int vl)
	{
		// FIXME: This should not be necessary if vlan-avled is working properly
		if (vlan.length == 1 && vlan[0].vlan == 1) return vlan[0].direction;

		for (int i=0; i < vlan.length; i++) {
			if (vlan[i].vlan == vl) return vlan[i].direction;
		}
		return DIRECTION_NONE;
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
		StringBuffer sb = new StringBuffer("Port [ifindex="+ifindex+", port="+port+", boxidBehind="+boxidBehind);
		if (vlan.length > 0) sb.append(", vlans=");
		for (int i=0; i < vlan.length; i++) {
			sb.append(vlan[i]+",");
		}
		sb.setCharAt(sb.length()-1, ']');
		return sb.toString();
	}



	protected static void outd(Object o) { if (DEBUG_OUT) System.out.print(o); }
	protected static void outld(Object o) { if (DEBUG_OUT) System.out.println(o); }

	protected static void err(Object o) { System.err.print(o); }
	protected static void errl(Object o) { System.err.println(o); }
}
