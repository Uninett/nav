package no.ntnu.nav.getDeviceData.deviceplugins.ARPLogger;

import java.net.InetAddress;
import java.net.UnknownHostException;
import java.util.Arrays;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;

import no.ntnu.nav.ConfigParser.ConfigParser;
import no.ntnu.nav.SimpleSnmp.SimpleSnmp;
import no.ntnu.nav.SimpleSnmp.TimeoutException;
import no.ntnu.nav.getDeviceData.Netbox;
import no.ntnu.nav.getDeviceData.dataplugins.DataContainer;
import no.ntnu.nav.getDeviceData.dataplugins.DataContainers;
import no.ntnu.nav.getDeviceData.dataplugins.Arp.ArpContainer;
import no.ntnu.nav.getDeviceData.dataplugins.Arp.Util;
import no.ntnu.nav.getDeviceData.deviceplugins.DeviceHandler;
import no.ntnu.nav.logger.Log;

/**
 * DeviceHandler for collecting ARP information from routers.
 * Support both IPv4 and IPv6
 * 
 * This plugin uses the following MIBs and OIDs:
 * 
 * IP-MIB for IPv4:
 * 		ipNetToMediaPhysAddress
 * 
 * IPV6-MIB for IPv6:
 * 		ipv6NetToMediaPhysAddress
 * 
 * CISCO-IETF-IP-MIB for IPv6 (and IPv4 if provided):
 * 		cInetNetToMeidaPhysAddress
 * 
 * @author gogstad
 *
 */
public class ARPLogger implements DeviceHandler {
	
	private String requiredIPv4OID = "ipNetToMediaPhysAddress";
	private String requiredCiscoIPv6OID = "cInetNetToMediaPhysAddress";
	private String requiredIetfIPv6OID = "ipv6NetToMediaPhysAddress";
	
	private String[] supportedCategoryIDs = {
			"GW",
			"GSW"
	};

	public int canHandleDevice(Netbox nb) {
		if(!Arrays.asList(supportedCategoryIDs).contains(nb.getCat()))
			return NEVER_HANDLE;

		Map<String,Integer> supportedOidsMap = buildSupportedOidsMap(nb);

		if(supportedOidsMap.isEmpty())
			return NEVER_HANDLE;
		else
			return ALWAYS_HANDLE;

	}
	
	private Map<String,Integer> buildSupportedOidsMap(Netbox nb) {
		Map<String,Integer> supportedOidsMap = new HashMap<String, Integer>();
		//supportedOidsMap<OID,bytes prepended to the IP address, usually is 1 or 3 depending on
		//whether the OID include the type of the ip or not.
		
		if(nb.isSupportedAllOids(new String[] {requiredIPv4OID}))
			supportedOidsMap.put(requiredIPv4OID,1);

		if(nb.isSupportedAllOids(new String[] {requiredCiscoIPv6OID}))
			supportedOidsMap.put(requiredCiscoIPv6OID,3);

		if(nb.isSupportedAllOids(new String[] {requiredIetfIPv6OID}))
			supportedOidsMap.put(requiredIetfIPv6OID,1);
		
		return supportedOidsMap;
	}
	
	public synchronized void handleDevice(Netbox nb, SimpleSnmp sSnmp, ConfigParser cp, DataContainers containers) throws TimeoutException {
		Log.setDefaultSubsystem("ARPLogger");
		
		//This is a hack. It seems that kongsvinger-gw.uninett.no and c6500-h-1.hiof.no is passed twice,
		//the second time nb.getOid returns null on all oids previously supported and thus the code will fail. 
		if(nb.getOid("sysname") == null) {
			Log.w("ARPLogger", "Netbox object (id:" + nb.getNetboxid() + ") for " + nb.getSysname() + " does not respond to .getOid");
			return;
		}
		
		Map<String,Integer> supportedOidsMap = buildSupportedOidsMap(nb);
		
		ArpContainer ac;
		{
			DataContainer dc = containers.getContainer("ArpContainer");
			if (dc == null) {
				Log.w("NO_CONTAINER", "No ArpContainer found, plugin may not be loaded");
				return;
			}
			if (!(dc instanceof ArpContainer)) {
				Log.w("NO_CONTAINER", "Container is not a ArpContainer! " + dc);
				return;
			}
			ac = (ArpContainer)dc;
		}

		ac.setIpMacMap(fetchIpMacMapping(nb,sSnmp,cp,supportedOidsMap));
		ac.commit();
	}
	
	private Map<InetAddress,String> fetchIpMacMapping(Netbox nb, SimpleSnmp sSnmp, ConfigParser cp, Map<String,Integer> supportedOidsMap) {
		Map<InetAddress,String> result = new HashMap<InetAddress, String>();
		
		for(Iterator<String> it = supportedOidsMap.keySet().iterator(); it.hasNext();) {
			String snmpoid = it.next();
					
			int bytesToSkip = supportedOidsMap.get(snmpoid).intValue();
			Map snmpResult = sSnmp.getAllMap(nb.getOid(snmpoid));

			for(Iterator j = snmpResult.keySet().iterator(); j.hasNext();) {
				String row = (String)j.next();
				String mac = Util.truncateMAC((String)snmpResult.get(row));
				
				String[] rowArray = row.split("\\.");
				String[] ipArray = new String[rowArray.length-bytesToSkip];
				System.arraycopy(rowArray, bytesToSkip, ipArray, 0, ipArray.length);
				
				InetAddress ip = null;
				try {
					ip = InetAddress.getByAddress(Util.convertToUnsignedByte(ipArray, 10));
				} catch (UnknownHostException e) {
					Log.e("ARPLogger", "Error while parsing IP address.");
					e.printStackTrace();
				}
				if(!Util.shouldIgnoreIp(ip, cp))
					result.put(ip, mac);
			}
		}
		return result;
	}
}
