package no.ntnu.nav.getDeviceData.plugins;

import java.util.*;

public class DeviceData
{
	String sysname;
	String snmpagent;

	//List propertyList;
	List boksDisk = new ArrayList();
	boolean boksDiskUpdated;
	List boksInterface = new ArrayList();
	boolean boksInterfaceUpdated;

	Map netboxinfo = new HashMap();
	boolean netboxinfoUpdated;

	public DeviceData() {

	}

	/**
	 * Set the sysname; if it is not blank the database will be updated if needed
	 *
	 * @param s the new sysname for this boks
	 */
	public void setSysname(String s) { sysname = s; }

	public String getSysname() { return sysname; }

	/**
	 * Set the snmpagent; if it is not blank the database will be updated if needed
	 *
	 * @param s the new snmpagent for this boks
	 */
	public void setSnmpagent(String s) { snmpagent = s; }

	public String getSnmpagent() { return snmpagent; }

	/**
	 * Add this path to the boks; any news paths will be inserted into the database, paths
	 * in the database not added here will be removed.
	 *
	 * @param path The path to add
	 * @param blocksize The blocksize used for the path
	 */
	public void addBoksDisk(String path, int blocksize) { if (path != null) boksDisk.add(new String[] { path, String.valueOf(blocksize) } ); }

	/**
	 * Call this method to enable updating of boksdisk. NOTE: If you call this method but
	 * don't add any paths all paths in the database for this boks will be deleted.
	 */
	public void boksDiskUpdated() { boksDiskUpdated = true; }

	public List getBoksDisk() { return boksDisk; }
	public boolean getBoksDiskUpdated() { return boksDiskUpdated; }

	/**
	 * Add this interface to the boks; any news interfaces will be inserted into the database, interfacess
	 * in the database not added here will be removed.
	 *
	 * @param interf The interface to add
	 */
	public void addBoksInterface(String interf) { if (interf != null) boksInterface.add(interf); }

	/**
	 * Call this method to enable updating of boksinterface. NOTE: If you call this method but
	 * don't add any interfaces all interfaces in the database for this boks will be deleted.
	 */
	public void boksInterfaceUpdated() { boksInterfaceUpdated = true; }

	public List getBoksInterface() { return boksInterface; }
	public boolean getBoksInterfaceUpdated() { return boksInterfaceUpdated; }

	/**
	 *
	 *
	 */
	public void addNetboxinfo(String key, String var, String val) {
		Map m;
		if ( (m=(Map)netboxinfo.get(key)) == null) netboxinfo.put(key, m=new HashMap());

		Set s;
		if ( (s=(Set)m.get(var)) == null) m.put(var, s=new HashSet());

		s.add(val);
	}

	public void netboxinfoUpdated() { netboxinfoUpdated = true; }

	public Map getNetboxinfo() { return netboxinfo; }
	public boolean getNetboxinfoUpdated() { return netboxinfoUpdated; }


}