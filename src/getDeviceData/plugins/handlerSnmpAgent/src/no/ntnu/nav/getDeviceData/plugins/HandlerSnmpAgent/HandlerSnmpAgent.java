package no.ntnu.nav.getDeviceData.plugins.HandlerSnmpAgent;

import no.ntnu.nav.SimpleSnmp.*;
import no.ntnu.nav.ConfigParser.*;
import no.ntnu.nav.getDeviceData.plugins.*;
import java.util.ArrayList;

public class HandlerSnmpAgent implements DeviceHandler
/**
 * Retrieves SNMP Agent sysObjectID.
 *
 * This small plugin is non-exclusive and retrieves the sysObjectID from
 * all devices that handles SNMP.
 * 
 */
{
	public int canHandleDevice(BoksData bd)
	{
    String ip = bd.getIp();
    if(ip == null || ip.equals("")) {
      return 0;
    }
    
    String community = bd.getCommunityRo();
    if(community == null || community.equals("")) {
      return 0;
    }
    
    return -100; // Not exclusive, high priority
   
	}

	public void handle(BoksData bd, SimpleSnmp snmp, ConfigParser cp, DeviceDataList ddList) throws TimeoutException
	{
		String ip = bd.getIp();
		String community = bd.getCommunityRo();

    // Prepare the snmp connectin
    snmp.setBaseOid(".1.3.6.1.2.1.1.2"); // sysObjectID
    snmp.setHost(ip);
    snmp.setCs_ro(community);

    ArrayList result = snmp.getNext(1, true);
    String agent;
    try {
      String[] row = (String[])result.get(0);
      agent = row[1];
    } catch (Exception e) {
      agent = "";
    }
    DeviceData dd = new DeviceData();
    dd.setSnmpagent(agent);
    ddList.setDeviceData(dd);
  }
}
