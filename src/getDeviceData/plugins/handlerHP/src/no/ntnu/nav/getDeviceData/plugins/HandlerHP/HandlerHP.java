package no.ntnu.nav.getDeviceData.plugins.HandlerHP;

import no.ntnu.nav.SimpleSnmp.*;
import no.ntnu.nav.ConfigParser.*;
import no.ntnu.nav.getDeviceData.plugins.*;
import java.util.*;

public class HandlerHP implements DeviceHandler
{
	private static boolean VERBOSE_OUT = false;

	private SimpleSnmp sSnmp;

	public int canHandleDevice(BoksData bd)
	{
		return bd.getTypegruppe().equals("hpsw") ? 1 : 0;
	}

	public void handle(BoksData bd, SimpleSnmp sSnmp, ConfigParser cp, DeviceDataList ddList) throws TimeoutException
	{
		String boksid = bd.getBoksid();
		String ip = bd.getIp();
		String cs_ro = bd.getCommunityRo();
		String boksTypegruppe = bd.getTypegruppe();
		String boksType = bd.getType();
		String sysName = bd.getSysname();
		String kat = bd.getKat();
		this.sSnmp = sSnmp;

		// Just to be sure...
		if (canHandleDevice(bd) <= 0) return;

		List swportDataList = processHP(boksid, ip, cs_ro, boksTypegruppe, boksType);

		for (Iterator it=swportDataList.iterator(); it.hasNext();) {
			SwportData swpd = (SwportData)it.next();
			ddList.addSwportData(swpd);
		}
	}


	/*
	 * HP
	 *
	 */
	private ArrayList processHP(String boksid, String ip, String cs_ro, String typegruppe, String typeid) throws TimeoutException
	{
		ArrayList l = new ArrayList();
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


		*/


		String stackOid = "1.3.6.1.4.1.11.2.14.11.5.1.10.4.1.1";

		String ifIndexOid = ".1.3.6.1.2.1.2.2.1.1";
		String ifSpeedOid = ".1.3.6.1.2.1.2.2.1.5";
		String ifAdminStatusOid = ".1.3.6.1.2.1.2.2.1.7";
		String ifOperStatusOid = ".1.3.6.1.2.1.2.2.1.8";

		String portTypeOid = ".1.3.6.1.4.1.11.2.14.11.5.1.7.1.3.1.1.2";
		//String etherModeOid = ".1.3.6.1.4.1.11.2.14.11.5.1.7.1.3.1.1.5";
		//String fastEtherModeOid = ".1.3.6.1.4.1.11.2.14.11.5.1.7.1.3.1.1.10";

		// Angir om vi har funnet en boks bak porten, gjør vi det skal CAM-data ikke logges på porten
		HashSet foundBoksBak = new HashSet();

		ArrayList stackList, macList;

		// Henter først antallet i stack'en:
		sSnmp.setParams(ip, cs_ro, stackOid);
		stackList = sSnmp.getAll();

		//outld("processHP: stackList.size: " + stackList.size() );

		for (int i=stackList.size()-1; i >= 0; i--) {
			String[] s = (String[])stackList.get(i);

			String modul = String.valueOf(stackList.size()-i);

			//outld("processHP:   modul: " + modul);

			// Get data
			sSnmp.setParams(ip, cs_ro+(!s[1].equals("0")?"@"+s[1]:""), ifSpeedOid);
			ArrayList ifSpeedList = sSnmp.getAll();

			sSnmp.setParams(ip, cs_ro+(!s[1].equals("0")?"@"+s[1]:""), ifOperStatusOid);
			ArrayList ifOperStatusList = sSnmp.getAll();

			sSnmp.setParams(ip, cs_ro+(!s[1].equals("0")?"@"+s[1]:""), portTypeOid);
			ArrayList portTypeList = sSnmp.getAll();

			/*
			if (ifSpeedList.size() != ifOperStatusList.size() || ifSpeedList.size() != portTypeList.size()) {
				outle("processHP: Size mismatch! ifSpeed: " + ifSpeedList.size() + ", ifOperStatus: " + ifOperStatusList.size() + ", portType: " + portTypeList.size());
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

			for (int j=0; j < portTypeList.size(); j++) {
				String[] portType = (String[])portTypeList.get(j);
				String ifindex = portType[0];

				String speed = (String)speedMap.get(ifindex);
				String operStatus = (String)operStatusMap.get(ifindex);

				String port = ifindex;

				long speedNum;
				try {
					speedNum = Long.parseLong(speed);
				} catch (NumberFormatException e) {
					outle("  processHP: boksid: " + boksid + " ifindex: " + ifindex + " NumberFormatException on speed: " + speed);
					continue;
				}
				String speedS = String.valueOf( (speedNum/1000000) );

				String status;
				try {
					int n = Integer.parseInt(operStatus);
					if (n == 1) {
						status = "up";
					} else if (n == 2) {
						status = "down";
					} else if (n == 0) {
						// FIXME
						status = "down";
					} else {
						outle("  processHP: boksid: " + boksid + " ifindex: " + ifindex + " Unknown status code: " + n);
						continue;
					}
				} catch (NumberFormatException e) {
					outle("  processHP: boksid: " + boksid + " ifindex: " + ifindex + " NumberFormatException for status code: " + operStatus);
					continue;
				}


				String duplex, media;
				try {
					int n = Integer.parseInt(portType[1]);
					switch (n) {
						case   1: // other(1),
							media = "Unknown";
							duplex = "full";
						break;

						case   2: // none(2),
							media = "None";
							duplex = "full";
						break;

						case   6: // ethernetCsmacd(6),
							media = "ethernetCsmacd";
							duplex = "full";
						break;

						case   7: // iso88023Csmacd(7),
							media = "iso88023Csmacd";
							duplex = "full";
						break;

						case  15: // fddi(15),
							media = "FDDI";
							duplex = "half";
						break;

						case  37: // atm(37),
							media = "ATM";
							duplex = "full";
						break;

						case  54: // propMultiplexor(54),
							media = "propMultiplexor";
							duplex = "full";
						break;

						case  55: // ieee80212(55),
							media = "ieee80212";
							duplex = "full";
						break;

						case  62: // fastEther(62),
							media = "100BaseTX";
							duplex = "full";
						break;

						case  69: // fastEtherFX(69),
							media = "100BaseFX";
							duplex = "full";
						break;

						case 117: // gigabitEthernetSX (117),
							media = "1000BaseSX";
							duplex = "full";
						break;

						case 118: // gigabitEthernetLX (118),
							media = "1000BaseLX";
							duplex = "full";
						break;

						case 119: // gigabitEthernetT (119),
							media = "1000BaseTX";
							duplex = "full";
						break;

						case 120: // gigabitEthernetStk (120)
							media = "1000BaseSTK";
							duplex = "full";
						break;

						default:
							outle("  processHP: boksid: " + boksid + " ifindex: " + ifindex + " Unknown port type: " + n);
						continue;
					}
				} catch (NumberFormatException e) {
					outle("  processHP: boksid: " + boksid + " ifindex: " + ifindex + " NumberFormatException for port type: " + portType[1]);
					continue;
				}


				outl("  Added portData("+boksid+"): ifindex: " + ifindex + " Modul: " + modul + " Port: " + port + " Status: " + status + " Speed: " + speed + " Duplex: " + duplex + " Media: " + media);

				// SwportData(String ifindex, String modul, String port, String status, String speed, String duplex, String media, boolean trunk, String portnavn)
				SwportData pd = new SwportData(ifindex, modul, port, status, speedS, duplex, media, false, "");
				l.add(pd);
			}
		}

		return l;
	}


	private static void oute(String s) { System.err.print(s); }
	private static void outle(String s) { System.err.println(s); }

	private static void outa(String s) { System.out.print(s); }
	private static void outla(String s) { System.out.println(s); }

	private static void out(String s) { if (VERBOSE_OUT) System.out.print(s); }
	private static void outl(String s) { if (VERBOSE_OUT) System.out.println(s); }

}