package no.ntnu.nav.getDeviceData.deviceplugins.HP;

import java.util.*;

import no.ntnu.nav.logger.*;
import no.ntnu.nav.SimpleSnmp.*;
import no.ntnu.nav.ConfigParser.*;
import no.ntnu.nav.getDeviceData.Netbox;
import no.ntnu.nav.getDeviceData.deviceplugins.*;
import no.ntnu.nav.getDeviceData.dataplugins.*;
import no.ntnu.nav.getDeviceData.dataplugins.Module.*;
import no.ntnu.nav.getDeviceData.dataplugins.Swport.*;

/**
 * <p>
 * DeviceHandler for collecting switch port data from HP switches.
 * </p>
 *
 * <p>
 * This plugin handles the following OID keys:
 * </p>
 *
 * <ui>
 *  <li>From MIB-II</li>
 *  <ul>
 *   <li>ifIndex (not used)</li>
 *   <li>ifSpeed</li>
 *   <li>ifAdminStatus</li>
 *   <li>ifOperStatus</li>
 *  </ul>
 *  <li>HP specific</li>
 *  <ul>
 *   <li>hpStack</li>
 *   <li>hpSerial</li>
 *   <li>hpHwVer</li>
 *   <li>hpSwVer</li>
 *   <li>hpPortType</li>
 *   <li>hpVlan</li>
 *  </ul>
 * </ul>
 * </p>
 *
 * <p>
 * <b>Note:</b> Both hpStack, hpSerial and hpPortType are required for any OID fetching to take place.
 * </p>
 */

public class HP implements DeviceHandler
{
	private static String[] canHandleOids = {
	  // The four MIB-II OIDs are not included here because this plugin uses
		// hpPortType instead of ifIndex to get the ifIndex for each port.
		//		"ifIndex",
		//		"ifSpeed",
		//		"ifAdminStatus",
		//		"ifOperStatus",
		"hpStack",
		"hpSerial",
		"hpHwVer",
		"hpSwVer",
		"hpPortType",
		"hpVlan"
	};

	private SimpleSnmp sSnmp;

	public int canHandleDevice(Netbox nb) {
		int v = nb.isSupportedOids(canHandleOids) ? ALWAYS_HANDLE : NEVER_HANDLE;
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

		String netboxid = nb.getNetboxidS();
		String ip = nb.getIp();
		String cs_ro = nb.getCommunityRo();
		String type = nb.getType();
		String sysName = nb.getSysname();
		String cat = nb.getCat();
		this.sSnmp = sSnmp;

		processHP(nb, netboxid, ip, cs_ro, type, sc);

		// Commit data
		sc.commit();
	}

	/*
	 * HP
	 *
	 */
	private void processHP(Netbox nb, String netboxid, String ip, String cs_ro, String typeid, SwportContainer sc) throws TimeoutException
	{

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

		/*
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
		*/

		// We cannot do anything without the stack OID, and we always want
		// the serial as well as the port type (since we don't use
		// ifIndex)
		if (!nb.canGetOid("hpStack") ||
				!nb.canGetOid("hpSerial") ||
				!nb.canGetOid("hpPortType")) {
			return;
		}

		ArrayList stackList, macList;

		// Get the number of devices in the stack
		sSnmp.setParams(ip, cs_ro, nb.getOid("hpStack"));
		stackList = sSnmp.getAll();

		if (stackList.isEmpty()) stackList.add(new String[] { "", "0" });
		Log.d("PROCESS_HP", "stackList.size: " + stackList.size() );

		for (int i=stackList.size()-1; i >= 0; i--) {
			String[] s = (String[])stackList.get(i);

			String modul = s[1];

			sSnmp.setCs_ro(cs_ro+(!s[1].equals("0")?"@sw"+s[1]:""));

			String serial = null, hwVer = null, swVer = null;
			try {
				sSnmp.setBaseOid(nb.getOid("hpSerial"));
				serial = ((String[])sSnmp.getNext(1, true, false).get(0))[1];

				// Fetch HwVer, SwVer
				if (nb.canGetOid("hpHwVer")) {
					sSnmp.setBaseOid(nb.getOid("hpHwVer"));
					hwVer = ((String[])sSnmp.getNext(1, true, false).get(0))[1];
				}

				if (nb.canGetOid("hpSwVer")) {
					sSnmp.setBaseOid(nb.getOid("hpSwVer"));
					swVer = ((String[])sSnmp.getNext(1, true, false).get(0))[1];
				}

			} catch (IndexOutOfBoundsException e) {
				Log.w("PROCESS_HP", "IndexOutOfBoundsException while fetching (serial|hw|sw): " + e.getMessage() );
				e.printStackTrace(System.err);
				return;
			}
			Log.d("PROCESS_HP", "Module: " + modul + " Serial: " + serial + " HwVer: " + hwVer +  " SwVer: " + swVer);

			SwModule m = sc.swModuleFactory(serial, hwVer, swVer, modul);

			Map speedMap = null;
			if (nb.canGetOid("ifSpeed")) {
				sSnmp.setBaseOid(nb.getOid("ifSpeed"));
				speedMap = sSnmp.getAllMap();
			}

			Map operStatusMap = null;
			if (nb.canGetOid("ifOperStatus")) {
				sSnmp.setBaseOid(nb.getOid("ifOperStatus"));
				operStatusMap = sSnmp.getAllMap();
			}

			Map admStatusMap = null;
			if (nb.canGetOid("ifAdminStatus")) {
				sSnmp.setBaseOid(nb.getOid("ifAdminStatus"));
				admStatusMap = sSnmp.getAllMap();
			}

			Map vlanMap = null;
			if (nb.canGetOid("hpVlan")) {
				sSnmp.setBaseOid(nb.getOid("hpVlan"));
				vlanMap = sSnmp.getAllMapList(1);
			}

			sSnmp.setBaseOid(nb.getOid("hpPortType"));
			List portTypeList = sSnmp.getAll();

			/*
			if (ifSpeedList.size() != ifOperStatusList.size() || ifSpeedList.size() != portTypeList.size()) {
				errl("processHP: Size mismatch! ifSpeed: " + ifSpeedList.size() + ", ifOperStatus: " + ifOperStatusList.size() + ", portType: " + portTypeList.size());
				break;
			}
			*/
			
			for (Iterator it = portTypeList.iterator(); it.hasNext();) {
				String[] portType = (String[])it.next();
				String ifindex = portType[0];

				Integer port;
				try {
					port = new Integer(Integer.parseInt(ifindex));
				} catch (NumberFormatException e) {
					Log.w("PROCESS_HP", "netboxid: " + netboxid + " ifindex: " + ifindex + " NumberFormatException on ifindex: " + ifindex);
					continue;
				}

				//Swport sw = m.swportFactory(port, ifindex, link, speedS, duplex, media, false, "");
				Swport sw = m.swportFactory(port, ifindex);

				if (speedMap != null) {
					String speed = (String)speedMap.get(ifindex);
					long speedNum;
					try {
						speedNum = Long.parseLong(speed);
						sw.setSpeed(String.valueOf( (speedNum/1000000) ));
					} catch (NumberFormatException e) {
						Log.w("PROCESS_HP", "netboxid: " + netboxid + " ifindex: " + ifindex + " NumberFormatException on speed: " + speed);
					}
				}

				if (operStatusMap != null && admStatusMap != null) {
					try {
						int n = Integer.parseInt((String)admStatusMap.get(ifindex));
						char link = 'd'; // adm down
						if (n == 1) {
							// adm up
							n = Integer.parseInt((String)operStatusMap.get(ifindex));
							if (n == 1) link ='y'; // link up
							else link = 'n'; // link oper down
						}
						else if (n != 2 && n != 0) {
							Log.w("PROCESS_HP", "netboxid: " + netboxid + " ifindex: " + ifindex + " Unknown status code: " + n);
						}
						sw.setLink(link);
					} catch (NumberFormatException e) {
						Log.w("PROCESS_HP", "netboxid: " + netboxid + " ifindex: " + ifindex + " NumberFormatException for status code: " + operStatusMap.get(ifindex));
					}
				}

				char duplex;
				String media = null;
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

					sw.setMedia(media);
					sw.setDuplex(duplex);

				} catch (NumberFormatException e) {
					Log.w("PROCESS_HP", "netboxid: " + netboxid + " ifindex: " + ifindex + " NumberFormatException for port type: " + portType[1]);
				}

				if (vlanMap != null) {
					List portVlanList = (List)vlanMap.get(ifindex);
					if (portVlanList == null) {
						Log.w("PROCESS_HP", "Error, vlanList not found for ifindex: " + ifindex);
					}

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
							sw.setVlan(vlan);
						} catch (NumberFormatException e) {
							Log.w("PROCESS_HP", "Cannot parse vlan: " + portVlanList.get(0));
						}
					}
				}

				Log.d("PROCESS_HP", "Netbox " + netboxid + ", added Swport: " + sw);

			}
		}

	}

}
