package no.ntnu.nav.getDeviceData.deviceplugins.HP;

import java.util.*;

import no.ntnu.nav.logger.*;
import no.ntnu.nav.SimpleSnmp.*;
import no.ntnu.nav.ConfigParser.*;
import no.ntnu.nav.netboxinfo.*;
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
 * <p>
 * <ui>
 *  <li>hpSerial</li>
 *  <li>hpHwVer</li>
 *  <li>hpSwVer</li>
 *  <li>hpPortType</li>
 *  <li>hpVlan</li>
 * </ul>
 * </p>
 *
 * <p>
 * <b>Note:</b> Both hpSerial and hpPortType are required for any OID fetching to take place.
 * </p>
 */

public class HP implements DeviceHandler
{
	private static String[] canHandleOids = {
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
	private void processHP(Netbox nb, String netboxid, String ip, String cs_ro, String type, SwportContainer sc) throws TimeoutException {

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

		// We always want the serial as well as the port type (since we
		// don't use ifIndex)
		if (!nb.canGetOid("hpSerial") ||
				!nb.canGetOid("hpPortType")) {
			return;
		}

		List l;

		// Module data
		l = sSnmp.getNext(nb.getOid("hpSerial"), 1, true, false);
		if (l != null) {
			for (Iterator it = l.iterator(); it.hasNext();) {
				String[] s = (String[])it.next();
				if (s.length < 3) Log.d("PROCESS_HP", "Missing 3rd element from hpSerial on: " + nb + " (" + nb.getType() + ")");
				sc.swModuleFactory(Integer.parseInt(s[2])).setSerial(s[1]);
				Log.d("PROCESS_HP", "Module: " + s[2] + " Serial: " + s[1]);
			}
		}

		l = sSnmp.getNext(nb.getOid("hpHwVer"), 1, true, false);
		if (l != null) {
			for (Iterator it = l.iterator(); it.hasNext();) {
				String[] s = (String[])it.next();
				sc.swModuleFactory(Integer.parseInt(s[2])).setHwVer(s[1]);
			}
		}

		l = sSnmp.getNext(nb.getOid("hpSwVer"), 1, true, false);
		if (l != null) {
			for (Iterator it = l.iterator(); it.hasNext();) {
				String[] s = (String[])it.next();
				sc.swModuleFactory(Integer.parseInt(s[2])).setSwVer(s[1]);
			}
		}

		l = sSnmp.getNext(nb.getOid("hpStackName"), 1, true, false);
		if (l != null && !l.isEmpty()) {
			String[] s = (String[])l.get(0);
			if (s[1].length() > 0) NetboxInfo.put(nb.getNetboxidS(), null, "stackName", s[1]);
		}

		// Switch port data
		l = sSnmp.getAll(nb.getOid("hpPortType"));
		if (l != null) {
			for (Iterator it = l.iterator(); it.hasNext();) {
				String[] portType = (String[])it.next();
				if (portType.length < 4) {
					Log.w("PROCESS_HP", "netboxid: " + netboxid + " Module/port number missing");
					continue;
				}
				
				String ifindex = portType[0];
				Swport swp = sc.swModuleFactory(Integer.parseInt(portType[2])).swportFactory(ifindex);

				//System.err.println("ifindex: " + ifindex + ", p0: " + portType[0] + ", p1: " + portType[1] + ", p2: " + portType[2]);

				try {
					swp.setPort(new Integer(Integer.parseInt(portType[3])));
				} catch (NumberFormatException e) {
					Log.w("PROCESS_HP", "netboxid: " + netboxid + " NumberFormatException on ifindex: " + ifindex);
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

					swp.setMedia(media);
					swp.setDuplex(duplex);

				} catch (NumberFormatException e) {
					Log.w("PROCESS_HP", "netboxid: " + netboxid + " ifindex: " + ifindex + " NumberFormatException for port type: " + portType[1]);
				}
			}
		}

		Map vlanMap = sSnmp.getAllMapList(nb.getOid("hpVlan"), 1);
		if (vlanMap != null) {
			for (Iterator it = vlanMap.entrySet().iterator(); it.hasNext();) {
				Map.Entry me = (Map.Entry)it.next();
				String ifindex = (String)me.getKey();
				List vlanList = (List)me.getValue();
				Swport swp = sc.swportFactory(ifindex);

				// Vlan
				if (vlanList.size() > 1) {
					swp.setTrunk(true);
					for (Iterator k=vlanList.iterator(); k.hasNext();) {
						swp.addTrunkVlan((String)k.next());
					}
				} else {
					int vlan = 0;
					try {
						vlan = Integer.parseInt((String)vlanList.get(0));
						swp.setVlan(vlan);
					} catch (NumberFormatException e) {
						Log.w("PROCESS_HP", "Cannot parse vlan: " + vlanList.get(0));
					}
				}
			}
		}
	}

}
