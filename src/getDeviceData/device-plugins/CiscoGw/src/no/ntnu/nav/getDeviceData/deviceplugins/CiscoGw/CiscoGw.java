package no.ntnu.nav.getDeviceData.deviceplugins.CiscoGw;

import java.net.InetAddress;
import java.net.UnknownHostException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import no.ntnu.nav.ConfigParser.ConfigParser;
import no.ntnu.nav.SimpleSnmp.SimpleSnmp;
import no.ntnu.nav.SimpleSnmp.TimeoutException;
import no.ntnu.nav.getDeviceData.Netbox;
import no.ntnu.nav.getDeviceData.dataplugins.DataContainer;
import no.ntnu.nav.getDeviceData.dataplugins.DataContainers;
import no.ntnu.nav.getDeviceData.dataplugins.Arp.Util;
import no.ntnu.nav.getDeviceData.dataplugins.Gwport.GwModule;
import no.ntnu.nav.getDeviceData.dataplugins.Gwport.Gwport;
import no.ntnu.nav.getDeviceData.dataplugins.Gwport.GwportContainer;
import no.ntnu.nav.getDeviceData.dataplugins.Gwport.Prefix;
import no.ntnu.nav.getDeviceData.dataplugins.Gwport.Vlan;
import no.ntnu.nav.getDeviceData.dataplugins.Module.Module;
import no.ntnu.nav.getDeviceData.dataplugins.Module.ModuleContainer;
import no.ntnu.nav.getDeviceData.dataplugins.Swport.SwportContainer;
import no.ntnu.nav.getDeviceData.deviceplugins.DeviceHandler;
import no.ntnu.nav.logger.Log;
import no.ntnu.nav.util.HashMultiMap;
import no.ntnu.nav.util.MultiMap;
import no.ntnu.nav.util.util;

/**
 * <p>
 * DeviceHandler for collecting gwport data from Cisco routers.
 * </p>
 *
 * <p>
 * This plugin handles the following OID keys:
 * </p>
 *
 * <p>
 * <ui>
 *  <li>ipAdEntIfIndex</li>
 *  <li>...</li>
 * </ul>
 * </p>
 */

public class CiscoGw implements DeviceHandler
{
	
	private static String[] canHandleOids = {
		"ipAdEntIfIndex",
		"cIpAddressIfIndex",
		"cIpAddressPrefix",
	};

	private static String[] supportedCatids = {
		"GSW",
		"GW",
	};

	private SimpleSnmp sSnmp;

	public int canHandleDevice(Netbox nb) {
		if (!Arrays.asList(supportedCatids).contains(nb.getCat()))
			return NEVER_HANDLE;
		int v = nb.isSupportedOids(canHandleOids) ? ALWAYS_HANDLE : NEVER_HANDLE;
		Log.d("CGW_CANHANDLE", "CHECK_CAN_HANDLE", "Can handle device: " + v);
		return v;
	}

	public void handleDevice(Netbox nb, SimpleSnmp sSnmp, ConfigParser cp, DataContainers containers) throws TimeoutException
	{
		//This is a hack. It seems that kongsvinger-gw.uninett.no and c6500-h-1.hiof.no is passed twice,
		//the second time nb.getOid returns null on all oids previously supported and thus the code will fail.
		if(nb.getOid("sysname") == null)
			return;
		
		Log.setDefaultSubsystem("CGW_DEVHANDLER");

		ModuleContainer mc;
		{
			DataContainer dc = containers.getContainer("ModuleContainer");
			if (dc == null) {
				Log.w("NO_CONTAINER", "No ModuleContainer found, plugin may not be loaded");
				return;
			}
			if (!(dc instanceof ModuleContainer)) {
				Log.w("NO_CONTAINER", "Container is not a ModuleContainer! " + dc);
				return;
			}
			mc = (ModuleContainer)dc;
		}
		
		GwportContainer gwc;
		{
			DataContainer dc = containers.getContainer("GwportContainer");
			if (dc == null) {
				Log.w("NO_CONTAINER", "No GwportContainer found, plugin may not be loaded");
				return;
			}
			if (!(dc instanceof GwportContainer)) {
				Log.w("NO_CONTAINER", "Container is not a GwportContainer! " + dc);
				return;
			}
			gwc = (GwportContainer)dc;
		}

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
		gwc.copyTranslateFrom(mc);

		String netboxid = nb.getNetboxidS();
		String ip = nb.getIp();
		String cs_ro = nb.getCommunityRo();
		String type = nb.getType();
		String sysName = nb.getSysname();
		String cat = nb.getCat();
		this.sSnmp = sSnmp;

		boolean fetch = processCiscoGw(nb, cp, netboxid, ip, cs_ro, type, mc, gwc, sc);
			
		// Commit data
		if (fetch) {
			if (mc.isCommited()) gwc.setEqual(mc);
			gwc.commit();
		}
	}

	/*
	 * CiscoGw
	 *
	 */
	private boolean processCiscoGw(Netbox nb, ConfigParser cp, String netboxid, String ip, String cs_ro, String type, ModuleContainer mc, GwportContainer gwc, SwportContainer sc) throws TimeoutException {

		/*

A) For hver ruter (kat=GW eller kat=GSW)
-----------------------------------------
1) Finn alle adresserom og deres mapping til ifindex
   (.1.3.6.1.2.1.4.20.1.2). Legges i hash.

2) I interfacetabellen ignorer alle ifindex som er adminstrativt ned,
   dvs ifAdminStatus=Down.

3) I interfacetabellen finn alle ifindex med ifAdminStatus=Up.
   Av disse:

   3.1   LAG GWPORT RECORD
	 Lag gwport record dersom

            a) * ifindex ligger i adresseromhash.
                 (Her er har vi altså ip adresserom)
               OG   
               * interf NOT like 'EOBC%' AND interf <> 'Vlan0'
                 (EOBC kommer med fra 6509 native, de ønsker vi ikke)  
         ELLER
            b) interfacet er et masterinterface med subinterface
               under seg. Se 3.2b) for indikasjon.

           
   3.2   SETT MASTERINDEX
         (Masterindex er kun et hjelpemiddel for å fortelle cricket
         at den skal hente last fra masterinterface dersom det
         ikke er octet-telling på subinterfacet)              

         For en opprettet gwport, sett gwport.masterindex dersom:

            a) ifInOctet=0 
         OG 
            b) ifdescr indikerer subinterface

         Indikasjon på subinterface sees ved å splitte ut det
         før punktum og se om man har funnet et annet interf.
         F.eks:  GigabitEthernet1/0/1.9 er subinterface under
                 GigabitEthernet1/0/1 

   3.3   LAG PREFIKS RECORD
   Lag prefiksrecord når:
            a) ny gwport lages 
         OG 
            b) denne har ip adresserom
               (om ikke adresserom forblir gwport.prefiksid=NULL)
         OG           
            c) prefikset ikke allerede er opprettet
               (sett uansett gwport.prefiksid)

    3.4 SETT VLAN-verdi i prefiks - første forsøk

        Sett prefiks.vlan basert på ruterdata om mulig:
         
        a) Dersom gwport.interf = 'Vlanx' 
           (vi har et virtuelt interface på en RSM/MSFC)
          => sett prefiks.vlan = x

        b) Dersom gwport.interf inneholder '.' (punktum)
           (vi har et subinterface)
          => hent vlan fra subintvlan-MIB og sett prefiks.vlan
             (har ikke funnet en slik MIB...)

   3.5  TOLK DESCRIPTION
        Hent description-felt-streng fra ruterport (ifalias) 
        
        3.5.1 Dersom konvensjon er forsøkt fulgt dvs at man
              gjenkjenner nettype=(lan,link,elink,stam,tun):

              a) Sett det man klarer i prefiksrecord av:
                 * nettype
                 * nettident
                 * orgid
                 * anvid
                 * komm
                 * samband
                 Dersom orgid,anvid ikke kan settes 
                 => warning til NAVlogg.

            b) SETT VLAN - andre forsøk
               * Dersom prefiks.vlan ikke er satt 
               OG 
               * Dersom vlan er angitt i description 5. felt, 
                 dvs etter kommanter
               => sett prefiks.vlan i henhold til dette.

        3.5.2 Konvensjon er ikke fulgt:

                * Sett nettype=ukjent
                * Sett nettident = descriptionstreng (max 20? tegn).


4) LAG GWPORTER FOR EVT HSRP-ADRESSER
   Sjekk om det finnes hsrp-adresser for ruteren
   * Dersom det finnes hsrp-adresser så lages det gwport for disse
     - Her settes gwport.hsrp=true.
     - gwport.prefiksid knytter seg til aktuelle prefiks
       (som skal være opprettet)
		*/
		
		
		boolean ipv4Supported = true;
		boolean ciscoIpv6Supported = true;
		boolean ietfIpv6Supported = true;
		boolean ipv6Supported;
		
		// Check for standard OID support
		Set oidsNotSupported = nb.oidsNotSupported(new String[] {
			"ifSpeed",
			"ifAdminStatus",
			"ifDescr",
			"ifInOctets",
		});

		if (!oidsNotSupported.isEmpty()) {
			if (nb.getCat().equals("GW") || nb.getCat().equals("GSW")) {
				Log.w("PROCESS_CGW", "Oidkeys " + oidsNotSupported + " are required, but not supported by " + nb.getSysname() + ", type " + nb.getType() + ", unable to fetch data!");
			}
			return false;
		}

		// Check for router OID IPv4
		oidsNotSupported = nb.oidsNotSupported(new String[] {
			"ipAdEntIfIndex",
			"ipAdEntIfNetMask",
		});

		if (!oidsNotSupported.isEmpty()) {
			if (nb.getCat().equals("GW") || nb.getCat().equals("GSW")) {
				Log.w("PROCESS_CGW", "Oidkeys " + oidsNotSupported + " are required for IPv4, but not supported by " + nb.getSysname() + ", type " + nb.getType() + ", unable to fetch IPv4 data!");
			}
			ipv4Supported = false;
		}
		
		// Check for router OID IPv6
		oidsNotSupported = nb.oidsNotSupported(new String[] {
			"cIpAddressIfIndex",
			"cIpAddressPrefix",
		});
		
		if(!oidsNotSupported.isEmpty()) {
			ciscoIpv6Supported = false;
			if(nb.isSupportedAllOids(new String[]{"cIpAddressIfIndex"}))
				System.out.println(nb.getSysname() + ": Support cIpAddressIfIndex but NOT cIpAddressPrefix!");
		}
		
		
		oidsNotSupported = nb.oidsNotSupported(new String[] {
			"ipv6AddrPfxLength",
		});
		
		if(!oidsNotSupported.isEmpty()) {
			ietfIpv6Supported = false;
		}
		
		ipv6Supported = ciscoIpv6Supported || ietfIpv6Supported;
		
		if(!ipv6Supported) {
			if (nb.getCat().equals("GW") || nb.getCat().equals("GSW"))
				Log.w("PROCESS_CGW", "Oidkeys " + oidsNotSupported + ", cIpAddressPrefix, are required for IPv6, but not supported by " + nb.getSysname() + ", type " + nb.getType() + ", unable to fetch IPv6 data!");
		}
		
		if(!ipv4Supported && !ipv6Supported) {		
			Log.w("PROCESS_CGW","Neither IPv4 nor IPv6 OIDs supported by " + nb.getSysname() + ", type " + nb.getType() + ", unable to fetch data!");
			return false;
		}
	
		// Fetch HSRP
		MultiMap hsrpIpMap = null;
		if(ipv4Supported)
			hsrpIpMap = util.reverse(sSnmp.getAllMap(nb.getOid("cHsrpGrpVirtualIpAddr")));
			//TODO: Need HSRP MIB for IPv6! NB: an if sentence at the end of the for loop from hell
			//		 assumes that IPv6 will be on short format as returned by ipv6Formatter in hsrpIpMap.
			//		26/6/07: MIB not released yet

		// Prefices and mapping to ifindex
		Map ipMap = null;
		MultiMap prefixMap = null;
		if(ipv4Supported)
			ipMap = sSnmp.getAllMap(nb.getOid("ipAdEntIfIndex"));
		
		if(ipMap != null)
			prefixMap = util.reverse(ipMap);
		
		if(ciscoIpv6Supported) {
			/* Entries in the cIpAddressTable are indexed by IP address type
			 * and IP address.  IP address type 2 = IPv6.  16 sub ids 
			 * (bytes) are needed to represent an IPv6 address.  Thus, we
			 * append .2.16 to cIpAddressIfIndex to retrieve only IPv6 
			 * addresses (and to conveniently strip the unneeded prefix).
			 */
			ipMap = sSnmp.getAllMap(nb.getOid("cIpAddressIfIndex") + ".2.16");
			MultiMap ipv6TemporaryPrefixMap = util.reverse(ipMap);
			
			if(prefixMap == null)
				prefixMap = new HashMultiMap();
			
			for(Iterator it = ipv6TemporaryPrefixMap.keySet().iterator(); it.hasNext();) {
				String ifIndex = (String)it.next();
				Set values = ipv6TemporaryPrefixMap.get(ifIndex);
				
				for(Iterator jt = values.iterator(); jt.hasNext();)
					prefixMap.put(ifIndex, ipv6Formatter((String)jt.next()));
			}
		}
		
		if(ietfIpv6Supported) {
			ipMap = sSnmp.getAllMap(nb.getOid("ipv6AddrPfxLength"));
			for(Iterator it = ipMap.keySet().iterator(); it.hasNext();) {
				String key = (String)it.next();
				String idx = key.substring(0,key.indexOf("."));
				String decIp = key.substring(key.indexOf(".")+1);
				prefixMap.put(idx, ipv6Formatter(decIp));
			}
		}
			
		boolean addedGwport = false;
		if (prefixMap != null) {
			Map netmaskMap = null;
			Map ipv6NetmaskLengthMap = new HashMap();
			
			if(ipv4Supported)
				netmaskMap = sSnmp.getAllMap(nb.getOid("ipAdEntIfNetMask"));
			
			if(ciscoIpv6Supported) {
				Map netmaskIpv6TemporaryMap = sSnmp.getAllMap(nb.getOid("cIpAddressPrefix") + ".2.16");
				for(Iterator it = netmaskIpv6TemporaryMap.keySet().iterator(); it.hasNext();) {
					String decIp = (String)it.next(); //ex 32.1.7.0.0.0.255.244.0.0.0.0.0.0.0.1
					String decMask = (String)netmaskIpv6TemporaryMap.get(decIp); //ex 1.3.6.1.4.1.9.10.86.1.1.1.1.5.14.2.16.32.1.7.0.0.0.255.244.0.0.0.0.0.0.0.0.64
					
					String hexIp = ipv6Formatter(decIp);
					int maskLength = Integer.parseInt(decMask.substring(decMask.lastIndexOf('.')+1));
					
					//link local addresses returns a subnetmask with length 0, for a 'proper'
					//method, use cIpv6InterfaceIdentifierLength.
					if(maskLength == 0)
						maskLength = 64;

					String hexMask = getIpv6Mask(decIp,maskLength);
					netmaskMap.put(hexIp,hexMask);
					ipv6NetmaskLengthMap.put(hexIp,new Integer(maskLength));
				}
			}
			
			if(ietfIpv6Supported) {
				Map ipPfxLengthMap = sSnmp.getAllMap(nb.getOid("ipv6AddrPfxLength"));
				for(Iterator it = ipPfxLengthMap.keySet().iterator(); it.hasNext();) {
					String key = (String)it.next();
					String decIp = key.substring(key.indexOf(".")+1);
					
					String hexIp = ipv6Formatter(decIp);
					int maskLength = Integer.parseInt((String)ipPfxLengthMap.get(key));
					
					//see last method
					if(maskLength == 0)
						maskLength = 64;
					
					String hexMask = getIpv6Mask(decIp, maskLength);
					netmaskMap.put(hexIp, hexMask);
					ipv6NetmaskLengthMap.put(hexIp,new Integer(maskLength));
				}
			}


			// Collect ospf
			Map ospfMap = new HashMap();
			String ospfOid = nb.getOid("ospfIfMetricMetric");
			if (ospfOid != null) {
				for (Iterator it = prefixMap.keySet().iterator(); it.hasNext();) {
					String ifidx = (String)it.next();
					for(Iterator pIt = prefixMap.get(ifidx).iterator(); pIt.hasNext();) {
						String ifip = (String)pIt.next();
						if(ifip.indexOf(":") < 0) { //only IPv4 addresses
							List l = sSnmp.getAll(ospfOid+"."+ifip+".0.0", false, false);
							//TODO: Denne må fungere med IPv6, molde-gw.uninett.no svarer på
							//både IPv6 og ospf. Finner ikke OSPFV3-MIB
							if (l != null && !l.isEmpty()) {
								ospfMap.put(ifidx, ((String[])l.get(0))[1]);
						}
						}
					}
				}
			}

			// From Mib-II
			Map speedMap = sSnmp.getAllMap(nb.getOid("ifSpeed"));
			Map highSpeedMap = sSnmp.getAllMap(nb.getOid("ifHighSpeed"));
			//Map operStatusMap = sSnmp.getAllMap(nb.getOid("ifOperStatus"));
			Map admStatusMap = sSnmp.getAllMap(nb.getOid("ifAdminStatus"));


			/*  ifAlias = description
					Hvis $netttype = 'lan' eller 'stam' : 
					  lan,$org,$anv[$n,$kommentar,$vlan] 
					Hvis $netttype = 'link': 
					   link,$tilruter[,$kommentar,$vlan] 
					Hvis $netttype = 'elink': 
					   elink,$tilruter,$tilorg[,$kommentar,$vlan] 
					$netttype = 'loopback' utgår, ingen description her.
			*/

			Map ifAliasMap = sSnmp.getAllMap(nb.getOid("ifAlias"), true);
			Map ifDescrMap = sSnmp.getAllMap(nb.getOid("ifDescr"), true);

			// Masterindex
			Set masterinterfSet = new HashSet();
			Map subinterfMap = new HashMap();

			// Only create masterindex if inOctets = 0
			Map ifInOctetsMap = sSnmp.getAllMap(nb.getOid("ifInOctets"));

			// Create a reverse map for masterindex processing
			MultiMap ifInterfMM = util.reverse(ifDescrMap);

			// Find all masterinterfaces
			//IPv6 OK
			for (Iterator it = ifDescrMap.entrySet().iterator(); it.hasNext();) {
				Map.Entry me = (Map.Entry)it.next();
				String ifindex = (String)me.getKey();
				String interf = (String)me.getValue();
				String masterinterf = interf.split("\\.")[0];

				if (ifInOctetsMap.containsKey(ifindex) &&
						Long.parseLong((String)ifInOctetsMap.get(ifindex)) == 0 &&
						interf.indexOf(".") >= 0 &&
						ifInterfMM.containsKey(masterinterf)) {
					
					masterinterfSet.add(masterinterf);
					subinterfMap.put(interf, masterinterf);
				}
			}

			List l = sSnmp.getAll(nb.getOid("ifDescr"), true);
			for (Iterator it = l.iterator(); it.hasNext();) {
				String[] s = (String[])it.next();
				String ifindex = s[0];
				String interf = s[1];

				if (!masterinterfSet.contains(interf) &&
					(interf == null || interf.startsWith("EOBC") || interf.equals("Vlan0") ||
					 !prefixMap.containsKey(ifindex))) continue;

				// Ignore any admDown interfaces
				String link = (String)admStatusMap.get(ifindex);
				if (!"1".equals(link)) continue;

				// Determine and create the module
				int module = 1;
				String modulePattern = ".*?(\\d+)/.*";
				if (interf.matches(modulePattern)) {
					Matcher m = Pattern.compile(modulePattern).matcher(interf);
					m.matches();
					module = Integer.parseInt(m.group(1));
				} else {
					boolean sup = false;
					for (Iterator modIt = mc.getModules(); modIt.hasNext();) {
						Module mod = (Module)modIt.next();
						String modDescr = mod.getDescr();
						if (modDescr != null && modDescr.toLowerCase().indexOf("supervisor") >= 0) {
							module = mod.getModule();
							sup = true;
							break;
						}
					}
					if (!sup) {
						Log.w("CGW_MATCH-MODULE", "Supervisor not found and could not match module pattern to if: " + interf);
					}
					if (mc.getModule(module) == null && mc.getModule(0) != null) {
						Log.w("CGW_MATCH-MODULE", "No module match from interf, defaulting to module 0");
						module = 0;
					}
				}
				if (mc.getModule(module) == null) {
					// Create module 1
					Log.w("CGW_MATCH-MODULE", "Module " + module + " does not exist on netbox " + nb.getSysname() + ", default to 1");
					module = 1;
					/*
					// Not allowed to create module
					Log.w("CGW_MATCH-MODULE", "Module " + module + " does not exist on netbox " + nb.getSysname() + ", skipping");
					continue;
					*/
				}
				GwModule gwm = gwc.gwModuleFactory(module);

				String nettype = Vlan.UNKNOWN_NETTYPE;
				/*
				String netident = "null";
				String orgid = "null";
				String usageid = "null";
				String vlan = "null";
				String description = "null";
				*/
				String netident = null;
				String orgid = null;
				String usageid = null;
				String vlan = null;
				String description = null;
				int convention = Vlan.CONVENTION_NTNU;

				// Parse the description (ifAlias)
				String descr = null;
				if (ifAliasMap != null) {
					descr = (String)ifAliasMap.get(ifindex);
					try {
						s = descr.split(",");
						for (int i=0; i < s.length; i++) if (s[i] != null) s[i] = s[i].trim();

						// Try to recognize NTNU description
						// FIXME!!!! Nettype should be core when descr starts with stam or core
						if (descr.startsWith("lan") || descr.startsWith("stam") || descr.startsWith("core")) {
							nettype = "lan";
							orgid = s[1];
							usageid = s[2];
							netident = orgid+","+usageid;
							if (s.length >= 4) netident += ","+s[3];
							if (s.length >= 5) description = s[4];
							if (s.length >= 6) vlan = s[5];
						} else if (descr.startsWith("link")) {
							nettype = "link";
							netident = nb.getSysname()+","+s[1];
							if (s.length >= 3) description = s[2];
							if (s.length >= 4) vlan = s[3];
						} else if (descr.startsWith("elink")) {
							nettype = "elink";
							netident = nb.getSysname()+","+s[1];
							orgid = s[2];
							if (s.length >= 4) description = s[3];
							if (s.length >= 5) vlan = s[4];
						} else if (ifDescrMap.containsKey(ifindex) && ((String)ifDescrMap.get(ifindex)).startsWith("Loopback")) {
							nettype = "loopback";
						} else if (s.length > 1) {
							// Interpret as UNINETT description
							convention = Vlan.CONVENTION_UNINETT;
							nettype = Vlan.UNKNOWN_NETTYPE;
							netident = s[1];
							description = s[0];
						} else {
							nettype = Vlan.UNKNOWN_NETTYPE;
							netident = descr;
						}
					} catch (Exception e) {
						Log.w("PROCESS_CGW", "Cannot parse ifAlias (ifindex " + ifindex + " on " + nb.getSysname() + "): " + descr);
						nettype = Vlan.UNKNOWN_NETTYPE;
						netident = descr;
					}
				}

				String pattern = "[Vv][Ll][Aa][Nn](\\d+).*";
				if (interf.matches(pattern)) {
					Matcher m = Pattern.compile(pattern).matcher(interf);
					m.matches();
					vlan = m.group(1);
				}

				// Check that vlan is number:
				if (vlan != null && !"null".equals(vlan) && !isNumber(vlan)) {
					Log.w("PROCESS_CGW", "Vlan ("+vlan+") from ifAlias (ifindex " + ifindex + " on " + nb.getSysname() + ") is not a number");
					vlan = null;
				}

				// Create Vlan
				Vlan vl;
				if (vlan != null && !"null".equals(vlan)) {
					vl = gwm.vlanFactory(netident, Integer.parseInt(vlan));
				} else {
					vl = gwm.vlanFactory(netident);
				}
				vl.setNettype(nettype);
				vl.setOrgid(orgid);
				vl.setUsageid(usageid);
				vl.setDescription(description);
				vl.setConvention(convention);

				// Create Gwport
				Gwport gwp = gwm.gwportFactory(ifindex, (String)ifDescrMap.get(ifindex));
				addedGwport = true;

				// We can now ignore this ifindex as an swport
				sc.ignoreSwport(ifindex);

				// Set port name (ifAlias)
				gwp.setPortname(descr);
				
				// Set OSPF
				if (ospfMap.containsKey(ifindex)) {
					String ospf = (String)ospfMap.get(ifindex);
					if (ospf == null || ospf.length() == 0) {
						System.err.println("Error, ospf is empty for " + nb.getSysname() + " ifindex: " + ifindex);
						Log.e("PROCESS_CGW", "OSPF is empty for " + nb.getSysname() + " ifindex: " + ifindex);
					} else {
						try {
							gwp.setOspf(Integer.parseInt((String)ospfMap.get(ifindex)));
						} catch (NumberFormatException e) {
							System.err.println("Malformed OSPF: " + ospfMap.get(ifindex));
						}
					}
				}

				// Check if masterindex
				if (subinterfMap.containsKey(interf)) {
					gwp.setMasterinterf((String)subinterfMap.get(interf));
				}

				// Set speed from Mib-II
				double speed;
				// If the ifSpeed value is maxed out (a 32 bit unsigned value), get the speed value from ifHighSpeed (if available)
				if (speedMap.containsKey(ifindex) && Long.parseLong((String)speedMap.get(ifindex)) == 4294967295L && highSpeedMap != null && highSpeedMap.containsKey(ifindex)) {
					speed = Long.parseLong((String)highSpeedMap.get(ifindex));
					Log.d("PROCESS_CGW", "Set gwport speed from ifHighSpeed for ifindex " + ifindex);
				} else {
					speed = speedMap.containsKey(ifindex) ? Long.parseLong((String)speedMap.get(ifindex)) / 1000000.0 : 0.0;
				}
				gwp.setSpeed(speed);

				// Create prefices
				for (Iterator prefixIt = prefixMap.get(ifindex).iterator(); prefixIt.hasNext();) {
					String gwip = (String)prefixIt.next();
					String mask = (String)netmaskMap.get(gwip);
					if(Util.shouldIgnoreIp(Util.getInetAddress(gwip), cp))
						continue;
					
					if(gwip.indexOf(":") < 0) { //gwip == IPv4
						boolean hsrp = hsrpIpMap != null && hsrpIpMap.containsKey( Prefix.ipToHex(gwip) );
						Prefix p = gwp.prefixFactory(gwip, hsrp, mask, vl);
					}
					else { //gwip == IPv6
						boolean hsrp = hsrpIpMap != null && hsrpIpMap.containsKey(gwip);
						int masklen = ((Integer)ipv6NetmaskLengthMap.get(gwip)).intValue();
						//it was decided that prefices with masklen==128 is uninteresting for us.
						if(masklen == 128)
							continue;
						Prefix p = gwp.prefixFactory(gwip, hsrp, mask, masklen, vl);
					}
				}
				
			}
		}
		return addedGwport;
	}
	
	/**
	 * @param ipv6 ipv6 address in decimal, dot separated, long notation.
	 * @param maskLength length of the netmask.
	 * 
	 * @return ipv6 netmask in hex, colon separated, short notation.
	 */
	private static String getIpv6Mask(String ipv6, int maskLength) {
		StringBuilder ipMaskBuilder = new StringBuilder();
		String[] decIp = ipv6.split("\\.");
		int maskBlocks = maskLength/8;
		int remainingBits = maskLength % 8;
		int lastMaskValue = 0;
		for(int i = 0; i < remainingBits; i++)
			lastMaskValue += (int)Math.pow(2.0, 7.0-i);
		
		for(int i = 0; i < decIp.length; i++) {
			if(i < maskBlocks)
				ipMaskBuilder.append(decIp[i] + ".");
			else if(i == maskBlocks && lastMaskValue > 0)
				ipMaskBuilder.append((lastMaskValue & Integer.parseInt(decIp[i])) + ".");
			else
				ipMaskBuilder.append("0.");
		}
		ipMaskBuilder.deleteCharAt(ipMaskBuilder.length()-1);
		
		return ipv6Formatter(ipMaskBuilder.toString());
	}

	/* 
	 * Converts an Ipv6 in decimal, dot separated, long notation to
	 * hex, colon separated, short notation.
	 * 
	 * Does not verify if the input IPv6 address is valid!
	 * 
	 * example input: 254.128.0.0.0.0.0.0.0.0.0.0.158.39.0.66
	 * 	       output: fe80::9e27:42
	 */	
	private static String ipv6Formatter(String ipv6) {
		String[] address = ipv6.split("\\.");
		StringBuilder longAddressBuilder = new StringBuilder(ipv6.length());

		int counter = 0;
		//convert to hex, group nybbles to hexlets, zero padding
		for(int i = 0; i < address.length; i++) {
			if(counter % 2 == 0)
				longAddressBuilder.append(":");
			int number = Integer.parseInt(address[i]);
			String hex = Integer.toHexString(number);
			if(hex.length() == 1)
				longAddressBuilder.append("0");
			longAddressBuilder.append(hex);
			counter ++;
		}
		longAddressBuilder.deleteCharAt(0);
		
		//longaddress is now on the format 2001:0700:0000:fff7:0000:0000:0000:0001
		
		//remove leading zeros, find the largest group of consecutive zero-groups and
		//replace the group with "::".
		String[] longAddress = longAddressBuilder.toString().split(":");
		int[] longestConsecutiveZeroes = new int[8];
		int maxIndex = -1;
		int max = -1;

		for(int j = 0; j < longestConsecutiveZeroes.length; j++) {
			for(int i = j; i < longAddress.length; i++) {
				if(longAddress[i].equals("0000"))
					longestConsecutiveZeroes[j]++;
				else {
					j = i;
					break;
				}	
			}
		}
		
		for(int i = 0; i < longestConsecutiveZeroes.length; i++)
			if(longestConsecutiveZeroes[i] > 0 && longestConsecutiveZeroes[i] >= max) {
				max = longestConsecutiveZeroes[i];
				maxIndex = i;
			}

		StringBuilder shortAddressBuilder = new StringBuilder();
		for(int i = 0; i < longAddress.length; i++) {
			if(i == maxIndex)
				shortAddressBuilder.append(":");
			if(maxIndex >= 0 && i >= maxIndex && i < maxIndex + longestConsecutiveZeroes[maxIndex]) //note < and not <=
				continue;

			int leadingZeros = 0;
			for(int j = 0; j < longAddress[i].length()-1; j++) //-1 in case all zeros
				if(longAddress[i].charAt(j) == '0')
					leadingZeros++;
				else
					break;

			for(int k = 0; k < longAddress[i].length(); k++) {
				if(leadingZeros > 0 && k < leadingZeros)
					continue;
				shortAddressBuilder.append(longAddress[i].charAt(k));
			}
			shortAddressBuilder.append(":");	

		}
		shortAddressBuilder.deleteCharAt(shortAddressBuilder.length()-1);
		if(shortAddressBuilder.charAt(shortAddressBuilder.length()-1) == ':') //if the last nibble is 0 (indicating netmask)
			shortAddressBuilder.append(":");
		
		return shortAddressBuilder.toString();
	}

	private static boolean isNumber(String s) {
		try {
			Integer.parseInt(s);
		} catch (NumberFormatException e) {
			return false;
		}
		return true;
	}

}
