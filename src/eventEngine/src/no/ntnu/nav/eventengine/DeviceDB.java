package no.ntnu.nav.eventengine;

import java.util.*;

public class DeviceDB
{
	HashMap deviceMap = new HashMap();
	Set deviceidSet;
	boolean updateMode;

	public DeviceDB()
	{

	}

	public Device getDevice(int deviceid)
	{
		return (Device)deviceMap.get(new Integer(deviceid));
	}

	public void putDevice(Device d)
	{
		if (!updateMode) return;
		deviceMap.put(d.getDeviceidI(), d);
		touchDevice(d);
	}
	public void touchDevice(Device d) {
		if (!updateMode) return;
		deviceidSet.remove(d.getDeviceidI());
	}
	public boolean isTouchedDevice(Device d) {
		if (!updateMode) return false;
		return deviceMap.containsKey(d.getDeviceidI()) && !deviceidSet.contains(d.getDeviceidI());
	}

	public void startDBUpdate() {
		deviceidSet = ((HashMap)deviceMap.clone()).keySet();
		updateMode = true;
	}

	public void endDBUpdate() {
		if (!updateMode) return;
		outld("devDB size: " + deviceMap.size());
		outld("Clone size: " + deviceidSet.size());
		updateMode = false;
	}

	public Alert alertFactort() {

		return null;
	}

	public void postAlert(Alert a) {


	}

	private static void outd(Object o) { System.out.print(o); }
	private static void outld(Object o) { System.out.println(o); }

	private static void err(Object o) { System.err.print(o); }
	private static void errl(Object o) { System.err.println(o); }
}