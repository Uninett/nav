package no.ntnu.nav.getDeviceData.deviceplugins.CiscoSwCAT;

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
 * DeviceHandler for collecting the standard Cisco CAT switch port OIDs.
 * </p>
 *
 * <p>
 * This plugin handles the following OID keys:
 * </p>
 *
 * <ul>
 *  <li>From Cisco CAT</li>
 *  <ul>
 *   <li>portIfIndex</li>
 *   <li>ifName</li>
 *   <li>portDuplex</li>
 *   <li>portVlan</li>
 *   <li>portVlansAllowed</li>
 *   <li>portTrunk</li>
 *   <li>portPortName</li>
 *  </ul>
 * </ul>
 * </p>
 *
 */

public class CiscoSwCAT implements DeviceHandler
{
	private static String[] canHandleOids = {
	    "portDuplex", 
	    "portIfIndex", 
	    "portVlan", 
	    "portTrunk", 
	    "portVlansAllowed", 
	    "portPortName",
	};

	private SimpleSnmp sSnmp;

	public int canHandleDevice(Netbox nb) {
		int v = nb.isSupportedOids(canHandleOids) ? ALWAYS_HANDLE : NEVER_HANDLE;

		Log.d("CAT_CANHANDLE", "CHECK_CAN_HANDLE", "Can handle device: " + v);
		return v;
	}

	public void handleDevice(Netbox nb, SimpleSnmp sSnmp, ConfigParser cp, DataContainers containers) throws TimeoutException
	{
		Log.setDefaultSubsystem("CAT_DEVHANDLER");
		
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
		this.sSnmp = sSnmp;

		processCAT(nb, netboxid, ip, cs_ro, type, sc);

		// Commit data
		sc.commit();
	}
	
	private void processCAT(Netbox nb, String netboxid, String ip, String cs_ro, String typeid, SwportContainer sc) throws TimeoutException
	{
		typeid = typeid.toLowerCase();

		List l;

		HashMap modPortIfindex = new HashMap();
                List o = sSnmp.getAll(nb.getOid("portIfIndex"));

                if (o != null) {
		    HashMap ifModule = new HashMap();
		    l = sSnmp.getAll(nb.getOid("ifName"));
		    if (l != null) {
			for (Iterator it = l.iterator(); it.hasNext();) {
			    String[] s = (String[])it.next();

			    String ifindex = s[0];
			    String portif = s[1];
			    
			    String[] modulport = portif.split("/");
			    String module = modulport[0];
			    module = module.replaceFirst("FastEthernet","Fa");
			    module = module.replaceFirst("GigabitEthernet","Gi");
			    sc.swModuleFactory(module);
			}
		    }
		    for (Iterator it = o.iterator(); it.hasNext();) {
			String[] s = (String[])it.next();

			    String modport = s[0];
			    String ifindex = s[1];
			    String[] s2 = s[0].split("\\.");
			    modPortIfindex.put(s[0],s[1]);
			
			    Integer port = (Integer)Integer.getInteger(s2[1]);
			    sc.swportFactory(ifindex).setPort(port);
		    }
			
		    l = sSnmp.getAll(nb.getOid("portDuplex"));
		    if (l != null) {
			for (Iterator it = l.iterator(); it.hasNext();) {
			    String[] s = (String[])it.next();
			    String modport = s[0];
			    String ifindex = (String)modPortIfindex.get(modport);
			    char duplex = (s[1].equals("1") ? 'h' : 'f');
			    sc.swportFactory(ifindex).setDuplex(duplex);
			}
		    }

		    l = sSnmp.getAll(nb.getOid("portPortName"));
		    if (l != null) {
			for (Iterator it = l.iterator(); it.hasNext();) {
			    String[] s = (String[])it.next();
			    String ifindex = (String) modPortIfindex.get(s[0]);
			    sc.swportFactory(ifindex).setPortname(s[1]);
			}
		    }
		    
		    l = sSnmp.getAll(nb.getOid("portVlan"));
		    if (l != null) {
			for (Iterator it = l.iterator(); it.hasNext();) {
			    String[] s = (String[])it.next();
			    String[] s2 = s[0].split("\\.");
			    int vlan = 0;
			    try{
				vlan = Integer.parseInt(s[1]);
			    } catch  (NumberFormatException e) {
					Log.w("PROCESS_CAT", "netboxid: " + netboxid + " ifindex: " + s[0] + " NumberFormatException on vlan: " + s[1]);
			    }
			    String ifindex = (String) modPortIfindex.get(s[0]);
			    sc.swportFactory(ifindex).setVlan(vlan);
			}
		    }
		    
		    l = sSnmp.getAll(nb.getOid("portTrunk"));
		    if (l != null) {
			for (Iterator it = l.iterator(); it.hasNext();) {
			    String[] s = (String[])it.next();
			    boolean trunk = (s[1].equals("1") ? true : false);
			    String ifindex = (String) modPortIfindex.get(s[0]);
			    sc.swportFactory(ifindex).setTrunk(trunk);
			}
		    }
		    
		    l = sSnmp.getAll(nb.getOid("portVlansAllowed"));
		    if (l != null) {
			for (Iterator it = l.iterator(); it.hasNext();) {
			    String[] s = (String[])it.next();
			    String ifindex = (String) modPortIfindex.get(s[0]);
			    sc.swportFactory(ifindex).setHexstring(s[1]);
			}
		    }
		    
		}

	}
}
