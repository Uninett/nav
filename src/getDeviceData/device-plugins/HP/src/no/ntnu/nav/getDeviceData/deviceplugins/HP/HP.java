package no.ntnu.nav.getDeviceData.deviceplugins.HP;

import java.util.*;

import no.ntnu.nav.logger.*;
import no.ntnu.nav.SimpleSnmp.*;
import no.ntnu.nav.ConfigParser.*;
import no.ntnu.nav.getDeviceData.deviceplugins.*;
import no.ntnu.nav.getDeviceData.dataplugins.*;
import no.ntnu.nav.getDeviceData.dataplugins.Module.*;
import no.ntnu.nav.getDeviceData.dataplugins.Swport.*;

/**
 * DeviceHandler for collecting switch port data from HP switches.
 */

public class HP implements DeviceHandler
{
	private static boolean VERBOSE_OUT = true;
	private static boolean DEBUG_OUT = true;

	private SimpleSnmp sSnmp;

	public int canHandleDevice(Netbox nb) {
		int v = nb.getTypegroup() != null && nb.getTypegroup().equals("hpsw") ? ALWAYS_HANDLE : NEVER_HANDLE;
		Log.d("HP_CANHANDLE", "CHECK_CAN_HANDLE", "Can handle device: " + v);
		return v;
	}

	public void handleDevice(Netbox nb, SimpleSnmp sSnmp, ConfigParser cp, DataContainers containers) throws TimeoutException
	{
		Log.setDefaultSubsystem("HP_DEVHANDLER");
		
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

		processHP(netboxid, ip, cs_ro, typegroup, type, sc);

		// Commit data
		sc.commit();
	}

	/*
	 * HP
	 *
	 */
	private void processHP(String netboxid, String ip, String cs_ro, String typegroup, String typeid, SwportContainer sc) throws TimeoutException
	{
		typeid = typeid.toLowerCase();

		/*
		HP 2524:
		=====

		Først henter vi ut antall i stack'en med MIB:

		.1.3.6.1.4.1.11.2.14.11.5.1.10.4.1.1

		Denne gir ut et tall for hvert member, 0 er alltid til stedet og er commanderen

	Standard fra MIB-II:

		ifIndex: .1.3.6.1.2.1.2.2.1.1
		ifSpeed: .1.3.6.1.2.1.2.2.1.5
		ifAdminStatus: .1.3.6.1.2.1.2.2.1.7
		ifOperStatus: .1.3.6.1.2.1.2.2.1.8

	HpSwitchPortEntry gir resten:

		HpSwitchPortEntry ::= .1.3.6.1.4.1.11.2.14.11.5.1.7.1.3.1.1
			SEQUENCE {
				hpSwitchPortIndex                  INTEGER,
				hpSwitchPortType                   HpSwitchPortType,
				hpSwitchPortDescr                  DisplayString,
				hpSwitchPortAdminStatus            INTEGER,
				hpSwitchPortEtherMode              INTEGER,
				hpSwitchPortVgMode                 INTEGER,
				hpSwitchPortLinkbeat               INTEGER,
				hpSwitchPortTrunkGroup             INTEGER,
				hpSwitchPortBcastLimit             INTEGER,
				hpSwitchPortFastEtherMode          INTEGER,
				hpSwitchPortFlowControl            INTEGER,
				hpSwitchPortBcastPktLimit          INTEGER,
				hpSwitchPortTrunkType              INTEGER,
				hpSwitchPortTrunkLACPStatus        INTEGER
			}

		Interessante:
				HpSwitchPortType ::= TEXTUAL-CONVENTION
					STATUS      current
					DESCRIPTION "Used to indicate the type of port."
					SYNTAX      INTEGER {
									other(1),
									none(2),
									ethernetCsmacd(6),
									iso88023Csmacd(7),
									fddi(15),
									atm(37),
									propMultiplexor(54),
									ieee80212(55),
									fastEther(62),
									fastEtherFX(69),
									gigabitEthernetSX (117),
									gigabitEthernetLX (118),
									gigabitEthernetT (119),
									gigabitEthernetStk (120)
								}

				hpSwitchPortEtherMode OBJECT-TYPE
					SYNTAX      INTEGER {
									half-duplex(1),
									full-duplex(2)
								}

				hpSwitchPortFastEtherMode OBJECT-TYPE
					SYNTAX      INTEGER {
									half-duplex-10Mbits(1),
									half-duplex-100Mbits(2),
									full-duplex-10Mbits(3),
									full-duplex-100Mbits(4),
									auto-neg(5),
									full-duplex-1000Mbits(6),
									auto-10Mbits(7),
									auto-100Mbits(8),
									auto-1000Mbits(9)
								}

	Vlan:

		.1.3.6.1.4.1.11.2.14.11.5.1.7.1.15.3.1.1

		Gir vlan.port = vlan


		*/


		String stackOid = "1.3.6.1.4.1.11.2.14.11.5.1.10.4.1.1";

		String ifIndexOid = ".1.3.6.1.2.1.2.2.1.1";
		String ifSpeedOid = ".1.3.6.1.2.1.2.2.1.5";
		String ifAdmStatusOid = ".1.3.6.1.2.1.2.2.1.7";
		String ifOperStatusOid = ".1.3.6.1.2.1.2.2.1.8";

		String serialOid = ".1.3.6.1.2.1.47.1.1.1.1.11.1";
		String hwOid = ".1.3.6.1.4.1.11.2.14.11.5.1.1.4.0";
		String swOid = ".1.3.6.1.4.1.11.2.14.11.5.1.1.3.0";

		String portTypeOid = ".1.3.6.1.4.1.11.2.14.11.5.1.7.1.3.1.1.2";
		//String etherModeOid = ".1.3.6.1.4.1.11.2.14.11.5.1.7.1.3.1.1.5";
		//String fastEtherModeOid = ".1.3.6.1.4.1.11.2.14.11.5.1.7.1.3.1.1.10";

		String vlanOid = "1.3.6.1.4.1.11.2.14.11.5.1.7.1.15.3.1.1";

		ArrayList stackList, macList;

		// Henter først antallet i stack'en:
		sSnmp.setParams(ip, cs_ro, stackOid);
		stackList = sSnmp.getAll();

		if (stackList.isEmpty()) stackList.add(new String[] { "", "0" });
		Log.d("PROCESS_HP", "stackList.size: " + stackList.size() );

		for (int i=stackList.size()-1; i >= 0; i--) {
			String[] s = (String[])stackList.get(i);

			String modul = s[1];

			sSnmp.setCs_ro(cs_ro+(!s[1].equals("0")?"@sw"+s[1]:""));

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
				Log.w("PROCESS_HP", "IndexOutOfBoundsException while fetching (serial|hw|sw): " + e.getMessage() );
				e.printStackTrace(System.err);
				return;
			}
			Log.d("PROCESS_HP", "Module: " + modul + " Serial: " + serial + " Hw_ver: " + hw_ver +  " Sw_ver: " + sw_ver);

			SwModule m = sc.swModuleFactory(serial, hw_ver, sw_ver, modul);

			// Get data
			sSnmp.setBaseOid(ifSpeedOid);
			ArrayList ifSpeedList = sSnmp.getAll();

			sSnmp.setBaseOid(ifOperStatusOid);
			ArrayList ifOperStatusList = sSnmp.getAll();

			sSnmp.setBaseOid(ifAdmStatusOid);
			ArrayList ifAdmStatusList = sSnmp.getAll();

			sSnmp.setBaseOid(vlanOid);
			ArrayList vlanList = sSnmp.getAll();

			sSnmp.setBaseOid(portTypeOid);
			ArrayList portTypeList = sSnmp.getAll();

			/*
			if (ifSpeedList.size() != ifOperStatusList.size() || ifSpeedList.size() != portTypeList.size()) {
				errl("processHP: Size mismatch! ifSpeed: " + ifSpeedList.size() + ", ifOperStatus: " + ifOperStatusList.size() + ", portType: " + portTypeList.size());
				break;
			}
			*/

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

			HashMap vlanMap = new HashMap();
			for (int j=0; j < vlanList.size(); j++) {
				String[] vlan = (String[])vlanList.get(j);
				vlan[0] = vlan[0].substring(vlan[0].lastIndexOf(".")+1, vlan[0].length());

				List vl;
				if ( (vl=(List)vlanMap.get(vlan[0])) == null) vlanMap.put(vlan[0], vl=new ArrayList());
				vl.add(vlan[1]);
			}

			//errl("size: " + portTypeList.size());

			for (int j=0; j < portTypeList.size(); j++) {
				String[] portType = (String[])portTypeList.get(j);
				String ifindex = portType[0];

				String speed = (String)speedMap.get(ifindex);
				String operStatus = (String)operStatusMap.get(ifindex);
				String admStatus = (String)admStatusMap.get(ifindex);

				List portVlanList = (List)vlanMap.get(ifindex);
				if (portVlanList == null) {
					Log.w("PROCESS_HP", "Error, vlanList not found for ifindex: " + ifindex);
					continue;
				}

				Integer port;
				try {
					port = new Integer(Integer.parseInt(ifindex));
				} catch (NumberFormatException e) {
					Log.w("PROCESS_HP", "netboxid: " + netboxid + " ifindex: " + ifindex + " NumberFormatException on ifindex: " + ifindex);
					continue;
				}

				long speedNum;
				try {
					speedNum = Long.parseLong(speed);
				} catch (NumberFormatException e) {
					Log.w("PROCESS_HP", "netboxid: " + netboxid + " ifindex: " + ifindex + " NumberFormatException on speed: " + speed);
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
						errl("  processHP: netboxid: " + netboxid + " ifindex: " + ifindex + " Unknown status code: " + n);
						continue;
					}
				} catch (NumberFormatException e) {
					errl("  processHP: netboxid: " + netboxid + " ifindex: " + ifindex + " NumberFormatException for status code: " + operStatus);
					continue;
				}

				char duplex;
				String media;
				try {
					int n = Integer.parseInt(portType[1]);
					switch (n) {
						case   1: // other(1),
							media = "Unknown";
							duplex = 'f'; // full
						break;

						case   2: // none(2),
							media = "None";
							duplex = 'f'; // full
						break;

						case   6: // ethernetCsmacd(6),
							media = "ethernetCsmacd";
							duplex = 'f'; // full
						break;

						case   7: // iso88023Csmacd(7),
							media = "iso88023Csmacd";
							duplex = 'f'; // full
						break;

						case  15: // fddi(15),
							media = "FDDI";
							duplex = 'h'; // half
						break;

						case  37: // atm(37),
							media = "ATM";
							duplex = 'f'; // full
						break;

						case  54: // propMultiplexor(54),
							media = "propMultiplexor";
							duplex = 'f'; // full
						break;

						case  55: // ieee80212(55),
							media = "ieee80212";
							duplex = 'f'; // full
						break;

						case  62: // fastEther(62),
							media = "100BaseTX";
							duplex = 'f'; // full
						break;

						case  69: // fastEtherFX(69),
							media = "100BaseFX";
							duplex = 'f'; // full
						break;

						case 117: // gigabitEthernetSX (117),
							media = "1000BaseSX";
							duplex = 'f'; // full
						break;

						case 118: // gigabitEthernetLX (118),
							media = "1000BaseLX";
							duplex = 'f'; // full
						break;

						case 119: // gigabitEthernetT (119),
							media = "1000BaseTX";
							duplex = 'f'; // full
						break;

						case 120: // gigabitEthernetStk (120)
							media = "1000BaseSTK";
							duplex = 'f'; // full
						break;

						default:
							Log.w("PROCESS_HP", "netboxid: " + netboxid + " ifindex: " + ifindex + " Unknown port type: " + n);
							continue;
					}
				} catch (NumberFormatException e) {
					Log.w("PROCESS_HP", "netboxid: " + netboxid + " ifindex: " + ifindex + " NumberFormatException for port type: " + portType[1]);
					continue;
				}

				Log.d("PROCESS_HP", "Added portData("+netboxid+"): ifindex: " + ifindex + " Modul: " + modul + " Port: " + port + " Link: " + link + " Speed: " + speed + " Duplex: " + duplex + " Media: " + media);

				// PortData(String ifindex, String modul, String port, String status, String speed, String duplex, String media, boolean trunk, String portnavn)
				//PortData pd = new PortData(ifindex, modul, port, status, speedS, duplex, media, false, "");
				Swport sw = m.swportFactory(port, ifindex, link, speedS, duplex, media, false, "");

				// Vlan
				if (portVlanList.size() > 1) {
					sw.setTrunk(true);
					for (Iterator k=portVlanList.iterator(); k.hasNext();) {
						sw.addTrunkVlan((String)k.next());
					}
				} else {
					int vlan = 0;
					try {
						vlan = Integer.parseInt((String)portVlanList.get(0));
					} catch (NumberFormatException e) {
						Log.w("PROCESS_HP", "Cannot parse vlan: " + portVlanList.get(0));
					}
					sw.setVlan(vlan);
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
