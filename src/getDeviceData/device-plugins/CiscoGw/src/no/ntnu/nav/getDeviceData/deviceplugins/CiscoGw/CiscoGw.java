package no.ntnu.nav.getDeviceData.deviceplugins.CiscoGw;

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
		"ipAdEntIfIndex"
	};

	private static String[] supportedCatids = {
		"GSW",
		"GW",
	};

	private SimpleSnmp sSnmp;

	public int canHandleDevice(Netbox nb) {
		if (!new HashSet(Arrays.asList(supportedCatids)).contains(nb.getCat())) return NEVER_HANDLE;
		int v = nb.isSupportedOids(canHandleOids) ? ALWAYS_HANDLE : NEVER_HANDLE;
		Log.d("CGW_CANHANDLE", "CHECK_CAN_HANDLE", "Can handle device: " + v);
		return v;
	}

	public void handleDevice(Netbox nb, SimpleSnmp sSnmp, ConfigParser cp, DataContainers containers) throws TimeoutException
	{
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

		boolean fetch = processCiscoGw(nb, netboxid, ip, cs_ro, type, mc, gwc, sc);
			
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
	private boolean processCiscoGw(Netbox nb, String netboxid, String ip, String cs_ro, String type, ModuleContainer mc, GwportContainer gwc, SwportContainer sc) throws TimeoutException {

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

		// Check for router OID
		oidsNotSupported = nb.oidsNotSupported(new String[] {
			"ipAdEntIfIndex",
			"ipAdEntIfNetMask",
		});

		if (!oidsNotSupported.isEmpty()) {
			if (nb.getCat().equals("GW") || nb.getCat().equals("GSW")) {
				Log.w("PROCESS_CGW", "Oidkeys " + oidsNotSupported + " are required, but not supported by " + nb.getSysname() + ", type " + nb.getType() + ", unable to fetch data!");
			}
			return false;
		}

		// Fetch HSRP
		MultiMap hsrpIpMap = util.reverse(sSnmp.getAllMap(nb.getOid("cHsrpGrpVirtualIpAddr")));

		// Prefices and mapping to ifindex
		Map ipMap = sSnmp.getAllMap(nb.getOid("ipAdEntIfIndex"));
		MultiMap prefixMap = util.reverse(ipMap);
		boolean addedGwport = false;
		if (prefixMap != null) {
			Map netmaskMap = sSnmp.getAllMap(nb.getOid("ipAdEntIfNetMask"));

			// Collect ospf
			Map ospfMap = new HashMap();
			String ospfOid = nb.getOid("ospfIfMetricMetric");
			if (ospfOid != null) {
				for (Iterator it = prefixMap.keySet().iterator(); it.hasNext();) {
					String ifidx = (String)it.next();
					String ifip = (String)prefixMap.get(ifidx).iterator().next();
					List l = sSnmp.getAll(ospfOid+"."+ifip+".0.0", false, false);
					if (l != null && !l.isEmpty()) ospfMap.put(ifidx, ((String[])l.get(0))[1]);
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

				String pattern = "Vlan(\\d+).*";
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

					boolean hsrp = hsrpIpMap != null && hsrpIpMap.containsKey( Prefix.ipToHex(gwip) );
					Prefix p = gwp.prefixFactory(gwip, hsrp, mask, vl);
				}
				
			}
		}
		return addedGwport;
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
