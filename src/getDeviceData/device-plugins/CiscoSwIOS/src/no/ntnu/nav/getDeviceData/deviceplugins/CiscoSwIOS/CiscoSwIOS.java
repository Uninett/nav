package no.ntnu.nav.getDeviceData.deviceplugins.CiscoSwIOS;

import java.util.*;

import no.ntnu.nav.logger.*;
import no.ntnu.nav.SimpleSnmp.*;
import no.ntnu.nav.ConfigParser.*;
import no.ntnu.nav.getDeviceData.deviceplugins.*;
import no.ntnu.nav.getDeviceData.dataplugins.*;
import no.ntnu.nav.getDeviceData.dataplugins.Module.*;
import no.ntnu.nav.getDeviceData.dataplugins.Swport.*;

/**
 * DeviceHandler for collecting switch port data from IOS switches.
 */

public class CiscoSwIOS implements DeviceHandler
{
	private static boolean VERBOSE_OUT = true;
	private static boolean DEBUG_OUT = true;

	private SimpleSnmp sSnmp;

	public int canHandleDevice(Netbox nb) {
		int v = nb.getTypegroup() != null && nb.getTypegroup().equals("cat-sw") ? ALWAYS_HANDLE : NEVER_HANDLE;
		Log.d("IOS_CANHANDLE", "CHECK_CAN_HANDLE", "Can handle device: " + v);
		return v;
	}

	public void handleDevice(Netbox nb, SimpleSnmp sSnmp, ConfigParser cp, DataContainers containers) throws TimeoutException
	{
		Log.setDefaultSubsystem("IOS_DEVHANDLER");
		
		SwportContainer sc;
		{
			DataContainer dc = containers.getContainer("SwportContainer");
			if (dc == null) {
				Log.w("NO_CONTAINER", "No SwportContainer found, plugin may not be loaded");
				return;
			}
			if (!(dc instanceof SwportContainer)) {
				Log.w("NO_CONTAINER", "Container is not an SwportContainer! " + dc);
				return;
			}
			sc = (SwportContainer)dc;
		}

		String netboxid = nb.getNetboxid();
		String ip = nb.getIp();
		String cs_ro = nb.getCommunityRo();
		String typegroup = nb.getTypegroup();
		String type = nb.getType();
		String sysName = nb.getSysname();
		String cat = nb.getCat();
		this.sSnmp = sSnmp;

		// Just to be sure...
		if (canHandleDevice(nb) <= 0) return;

		processIOS(netboxid, ip, cs_ro, typegroup, type, sc);

		// Commit data
		sc.commit();
	}

	/*
	 * IOS
	 *
	 */
	private void processIOS(String netboxid, String ip, String cs_ro, String typegroup, String typeid, SwportContainer sc) throws TimeoutException
	{
		typeid = typeid.toLowerCase();


		//String stackOid = "1.3.6.1.4.1.11.2.14.11.5.1.10.4.1.1";//?

		String ifIndexOid = ".1.3.6.1.2.1.2.2.1.1";
		String ifSpeedOid = ".1.3.6.1.2.1.2.2.1.5";
		String ifAdmStatusOid = ".1.3.6.1.2.1.2.2.1.7";
		String ifOperStatusOid = ".1.3.6.1.2.1.2.2.1.8";
		//String ifPortOid = ".1.3.6.1.2.1.31.1.1.1.1";

		//String serialOid = ".1.3.6.1.4.1.9.5.1.3.1.1.26";
		//String hwOid = ".1.3.6.1.4.1.9.5.1.3.1.1.18";
		//String swOid = ".1.3.6.1.4.1.9.5.1.3.1.1.20";

		//String portIfOid = ".1.3.6.1.4.1.9.5.1.4.1.1.11";
		String ifPortOid = ".1.3.6.1.2.1.2.2.1.2";
		String ifDuplexOid = ".1.3.6.1.4.1.9.9.87.1.4.1.1.32.0";
		//String portTypeOid = ".1.3.6.1.4.1.11.2.14.11.5.1.7.1.3.1.1.2";
		String portNameOid = ".1.3.6.1.4.1.9.2.2.1.1.28";
		String ifTrunkOid = ".1.3.6.1.4.1.9.9.87.1.4.1.1.6.0";
		String vlanHexOid = ".1.3.6.1.4.1.9.9.46.1.6.1.1.4";
		String vlanOid = ".1.3.6.1.4.1.9.9.68.1.2.2.1.2";


		sSnmp.setHost(ip);
		sSnmp.setCs_ro(cs_ro);
		   
		
		/*
			// Hent serial, hw, sw
			String serial, hw_ver, sw_ver;
			try {
				sSnmp.setBaseOid(serialOid);
				serial = ((String[])sSnmp.getNext(1, true, false).get(0))[1];

				sSnmp.setBaseOid(hwOid);
				hw_ver = ((String[])sSnmp.getNext(1, true, false).get(0))[1];

				sSnmp.setBaseOid(swOid);
				sw_ver = ((String[])sSnmp.getNext(1, true, false).get(0))[1];
			} catch (IndexOutOfBoundsException e) {
				Log.w("PROCESS_IOS", "IndexOutOfBoundsException while fetching (serial|hw|sw): " + e.getMessage() );
				e.printStackTrace(System.err);
				return;
			}
			Log.d("PROCESS_IOS", "Module: " + modul + " Serial: " + serial + " Hw_ver: " + hw_ver +  " Sw_ver: " + sw_ver);
		*/
			// Get data
		/* Ikke miber enda
			sSnmp.setBaseOid(serialOid);
			ArrayList moduleSerialList = sSnmp.getAll();
		*/
			sSnmp.setBaseOid(ifPortOid);
			ArrayList portIfList = sSnmp.getAll();
			
			sSnmp.setBaseOid(ifSpeedOid);
			ArrayList ifSpeedList = sSnmp.getAll();

			sSnmp.setBaseOid(ifOperStatusOid);
			ArrayList ifOperStatusList = sSnmp.getAll();

			sSnmp.setBaseOid(ifAdmStatusOid);
			ArrayList ifAdmStatusList = sSnmp.getAll();

			sSnmp.setBaseOid(ifDuplexOid);
			ArrayList ifDuplexList = sSnmp.getAll();

			sSnmp.setBaseOid(vlanOid);
			ArrayList ifVlanList = sSnmp.getAll();

			sSnmp.setBaseOid(vlanHexOid);
			ArrayList ifVlanHexList = sSnmp.getAll(true);

			sSnmp.setBaseOid(ifTrunkOid);
			ArrayList ifTrunkList = sSnmp.getAll();

			/*
			sSnmp.setBaseOid(portTypeOid);
			ArrayList portTypeList = sSnmp.getAll();
			*/

			sSnmp.setBaseOid(portNameOid);
			ArrayList portNameList = sSnmp.getAll();

			/* Ikke mib-er enda
			HashMap serialMap = new HashMap();
			for (int j=0; j < moduleSerialList.size(); j++) {
			    String[] modserial = (String[])moduleSerialList.get(j);
			    serialMap.put(modserial[0],modserial[1]);
			}
			*/

			HashMap portIfMap = new HashMap();
			for (int j=0; j < portIfList.size(); j++) {
			    String[] portif = (String[])portIfList.get(j);
			    portIfMap.put(portif[0],portif[1]);
			}

			HashMap speedMap = new HashMap();
			for (int j=0; j < ifSpeedList.size(); j++) {
				String[] speed = (String[])ifSpeedList.get(j);
				speedMap.put(speed[0], speed[1]);
			}

			HashMap operStatusMap = new HashMap();
			for (int j=0; j < ifOperStatusList.size(); j++) {
				String[] operStatus = (String[])ifOperStatusList.get(j);
				operStatusMap.put(operStatus[0], operStatus[1]);
			}

			HashMap admStatusMap = new HashMap();
			for (int j=0; j < ifAdmStatusList.size(); j++) {
				String[] admStatus = (String[])ifAdmStatusList.get(j);
				admStatusMap.put(admStatus[0], admStatus[1]);
			}

			HashMap duplexMap = new HashMap();
			for (int j=0; j < ifDuplexList.size(); j++) {
			    String[] duplex = (String[])ifDuplexList.get(j);
			    duplexMap.put(duplex[0], duplex[1]);
			}
			
			HashMap trunkMap = new HashMap();
			for (int j=0; j < ifTrunkList.size(); j++) {
			    String[] trunk = (String[])ifTrunkList.get(j);
			    trunkMap.put(trunk[0], trunk[1]);
			}

			HashMap portNameMap = new HashMap();
			for (int j=0; j < portNameList.size(); j++) {
			    String[] portName = (String[])portNameList.get(j);
			    portNameMap.put(portName[0], portName[1]);
			}
			
			HashMap vlanHexMap = new HashMap();
			for (int j=0; j < ifVlanHexList.size(); j++) {
			    String[] vlanHex = (String[])ifVlanHexList.get(j);
			    vlanHexMap.put(vlanHex[0], vlanHex[1]);
			}
			HashMap vlanMap = new HashMap();
			for (int j=0; j < ifVlanList.size(); j++) {
			    String[] vlan = (String[])ifVlanList.get(j);
			    vlanHexMap.put(vlan[0], vlan[1]);
			}

			//errl("size: " + portTypeList.size());

			Map moduleMap = new HashMap();
			/* Ikke noen mib-er
			for (int j = 0; j < moduleSerialList.size(); j++) {
			    String[] modulenumber = (String[])moduleSerialList.get(j);
			    String modul = modulenumber[0];
			    
			    String serial = (String) serialMap.get(modul);
			    String hw = "";//(String) hwMap.get(modul);
			    String sw = "";//(String) swMap.get(modul);

			    Log.d("PROCESS_CAT", "Module: " + modul + " Serial: " + serial + " Hw_ver: " + hw +  " Sw_ver: " + sw);

			    // Create module
			    Module m = sc.moduleFactory(serial, hw, sw, modul);
			    moduleMap.put(modul, m);

			}
			*/

			for (int j=0; j < portIfList.size(); j++) {
				String[] portIfTuple = (String[])portIfList.get(j);
				String ifindex = portIfTuple[0];
				String portif = portIfTuple[1];

				Integer ifi;
				int special;
				try {
					ifi = new Integer(Integer.parseInt(ifindex));
					special = ifi.intValue() + 1;
				} catch (NumberFormatException e) {
					Log.w("PROCESS_IOS", "netboxid: " + netboxid + " ifindex: " + ifindex + " NumberFormatException on ifi: " + ifindex);
					continue;
				}

				String[] modulport = portif.split("/");
				/*
				  Pattern modulport = Pattern.matches("^(\w+)\/(\d+)$",ifname);
				  String modul = (String)modulport.groups(1);
				  String port = (String)modulport.groups(2);
				*/
				String modul = modulport[0];
				modul = modul.replaceFirst("FastEthernet","Fa");
				modul = modul.replaceFirst("GigabitEthernet","Gi");

				String speed = (String)speedMap.get(ifindex);
				String admStatus = (String)admStatusMap.get(ifindex);
				String operStatus = (String)operStatusMap.get(ifindex);
				String duplex = (String)duplexMap.get(""+special);
				String trunk = (String)trunkMap.get(""+special);
				String vlan = (String)vlanMap.get(ifindex);
				String vlanHex = (String)vlanHexMap.get(ifindex);
				String portname = (String)portNameMap.get(ifindex);
				
				Integer vlanNum;
				try {
				    vlanNum = new Integer(Integer.parseInt(vlan));
				} catch (NumberFormatException e) {
					Log.w("PROCESS_IOS", "netboxid: " + netboxid + " ifindex: " + ifindex + " NumberFormatException on vlan: " + vlan);
					continue;
				}


				Integer port;
				try {
					port = new Integer(Integer.parseInt(modulport[1]));
				} catch (NumberFormatException e) {
					Log.w("PROCESS_IOS", "netboxid: " + netboxid + " ifindex: " + ifindex + " NumberFormatException on port: " + modulport[1]);
					continue;
				}

				long speedNum;
				try {
					speedNum = Long.parseLong(speed);
				} catch (NumberFormatException e) {
					Log.w("PROCESS_IOS", "netboxid: " + netboxid + " ifindex: " + ifindex + " NumberFormatException on speed: " + speed);
					continue;
				}
				String speedS = String.valueOf( (speedNum/1000000) );

				char link = 'd'; // adm down
				try {
					int n = Integer.parseInt(admStatus);
					if (n == 1) {
						// adm up
						n = Integer.parseInt(operStatus);
						if (n == 1) link ='y'; // link up
						else link = 'n'; // link oper down
					}
					else if (n != 2 && n != 0) {
						errl("  processIOS: netboxid: " + netboxid + " ifindex: " + ifindex + " Unknown status code: " + n);
						continue;
					}
				} catch (NumberFormatException e) {
					errl("  processIOS: netboxid: " + netboxid + " ifindex: " + ifindex + " NumberFormatException for status code: " + operStatus);
					continue;
				}

				char duplexS = 'h';
				try {
				    int n = Integer.parseInt(duplex);
				    if(n == 1){
					//full i stedet for half
					duplexS = 'f';
				    }
				} catch (NumberFormatException e) {
					errl("  processIOS: netboxid: " + netboxid + " ifindex: " + special + " NumberFormatException for status code: " + duplex);
					continue;
				}
				boolean trunkB = false;
				try {
				    int n = Integer.parseInt(trunk);
				    if(n == 0){
					//trunk - modul og port
					trunkB = true;
				    }
				} catch (NumberFormatException e) {
					errl("  processIOS: netboxid: " + netboxid + " ifindex: " + special + " NumberFormatException for status code: " + trunk);
					continue;
				}

				String media = "";

				Log.d("PROCESS_IOS", "Added portData("+netboxid+"): ifindex: " + ifindex + " Modul: " + modul + " Port: " + port + " Link: " + link + " Speed: " + speed + " Duplex: " + duplexS + " Media: " + media);


				String serial = "";
				String hw_ver = "";
				String sw_ver = "";

				// Create module
				SwModule m = (SwModule)moduleMap.get(modul);
				if (m == null) {
					m = sc.swModuleFactory(serial, hw_ver, sw_ver, modul);
					moduleMap.put(modul, m);
				}

				// PortData(String ifindex, String modul, String port, String status, String speed, String duplex, String media, boolean trunk, String portnavn)
				//PortData pd = new PortData(ifindex, modul, port, status, speedS, duplex, media, false, "");
				Swport sw = m.swportFactory(port, ifindex, link, speedS, duplexS, "", trunkB, portname);

				// Vlan
				if (trunkB == true){
				    if(vlanHex == null){
					Log.w("PROCESS_IOS", "Error, vlanHex not found for ifindex: " + ifindex);
					continue;
				    } else {
					sw.setHexstring(vlanHex);
				    }
				} else {
				    if(vlan == null){
					Log.w("PROCESS_IOS", "Error, vlan not found for ifindex: " + ifindex);
					continue;
				    } else {
					sw.setVlan(vlanNum.intValue());
				    }
				}
			}
		}

	private static void outa(String s) { System.out.print(s); }
	private static void outla(String s) { System.out.println(s); }

	private static void out(String s) { if (VERBOSE_OUT) System.out.print(s); }
	private static void outl(String s) { if (VERBOSE_OUT) System.out.println(s); }

	private static void outd(String s) { if (DEBUG_OUT) System.out.print(s); }
	private static void outld(String s) { if (DEBUG_OUT) System.out.println(s); }

	private static void err(Object o) { System.err.print(o); }
	private static void errl(Object o) { System.err.println(o); }
	private static void errflush() { System.err.flush(); }

}
