package no.ntnu.nav.getDeviceData.deviceplugins.CiscoGw;

import java.util.*;
import java.util.regex.*;

import no.ntnu.nav.logger.*;
import no.ntnu.nav.SimpleSnmp.*;
import no.ntnu.nav.ConfigParser.*;
import no.ntnu.nav.util.*;
import no.ntnu.nav.getDeviceData.Netbox;
import no.ntnu.nav.getDeviceData.deviceplugins.*;
import no.ntnu.nav.getDeviceData.dataplugins.*;
import no.ntnu.nav.getDeviceData.dataplugins.Module.*;
import no.ntnu.nav.getDeviceData.dataplugins.Gwport.*;
import no.ntnu.nav.getDeviceData.dataplugins.Swport.*;

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
			"ifAlias"
		});

		if (!oidsNotSupported.isEmpty()) {
			return false;
		}

		// Check for router OID
		oidsNotSupported = nb.oidsNotSupported(new String[] {
			"ipAdEntIfIndex",
			"ipAdEntIfNetMask",
		});

		if (!oidsNotSupported.isEmpty()) {
			if (nb.getCat().equals("GW")) {
				Log.w("PROCESS_CGW", "Oidkeys " + oidsNotSupported + " are required, but not supported by " + nb.getSysname() + ", type " + nb.getType() + ", unable to fetch data!");
			}
			return false;
		}

		// Fetch HSRP
		MultiMap hsrpIpMap = util.reverse(sSnmp.getAllMap(nb.getOid("cHsrpGrpVirtualIpAddr")));

		// Prefices and mapping to ifindex
		MultiMap prefixMap = util.reverse(sSnmp.getAllMap(nb.getOid("ipAdEntIfIndex")));
		if (prefixMap != null) {
			Map netmaskMap = sSnmp.getAllMap(nb.getOid("ipAdEntIfNetMask"));
			
			// From Mib-II
			Map speedMap = sSnmp.getAllMap(nb.getOid("ifSpeed"));
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


			List l = sSnmp.getAll(nb.getOid("ifAlias"), true);
			for (Iterator it = l.iterator(); it.hasNext();) {
				String[] s = (String[])it.next();
				String ifindex = s[0];
				String descr = s[1];

				// Ignore any admDown interfaces
				String link = (String)admStatusMap.get(ifindex);
				if (!"1".equals(link)) continue;

				String interf = (String)ifDescrMap.get(ifindex);
				if (!masterinterfSet.contains(interf) &&
						(interf == null || interf.startsWith("EOBC") || interf.equals("Vlan0") ||
						 !prefixMap.containsKey(ifindex))) continue;

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
						Log.w("MATCH-MODULE", "Supervisor not found and could not match module pattern to if: " + interf);
					}
					if (mc.getModule(module) == null && mc.getModule(0) != null) {
						Log.w("MATCH-MODULE", "No module match from interf, defaulting to module 0");
						module = 0;
					}
				}
				if (mc.getModule(module) == null) {
					// Not allowed to create module
					Log.w("MATCH-MODULE", "Module " + module + " does not exist on netbox " + nb.getSysname() + ", skipping");
					continue;
				}
				GwModule gwm = gwc.gwModuleFactory(module);

				String nettype = "null";
				String netident = "null";
				String orgid = "null";
				String usageid = "null";
				String vlan = "null";
				String description = "null";

				// Parse the description (ifAlias)
				try {
					s = descr.split(",");
					for (int i=0; i < s.length; i++) if (s[i] != null) s[i] = s[i].trim();

					// Try to recognize NTNU description
					if (descr.startsWith("lan") || descr.startsWith("stam") || descr.startsWith("core")) {
						nettype = "lan";
						orgid = s[1];
						usageid = s[2];
						netident = orgid+","+usageid;
						if (s.length >= 4) netident += s[3];
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

				// Create Gwport
				Gwport gwp = gwm.gwportFactory(ifindex, (String)ifDescrMap.get(ifindex));

				// We can now ignore this ifindex as an swport
				sc.ignoreSwport(ifindex);

				// Check if masterindex
				if (subinterfMap.containsKey(interf)) {
					gwp.setMasterinterf((String)subinterfMap.get(interf));
				}

				// Set speed from Mib-II
				double speed = speedMap.containsKey(ifindex) ? Long.parseLong((String)speedMap.get(ifindex)) / 1000000.0 : 0.0;
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
		return true;
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
