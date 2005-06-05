package no.ntnu.nav.getDeviceData.deviceplugins.GetVlanFromInterface;

import java.util.*;
import java.util.regex.*;
import java.sql.ResultSet;
import java.sql.SQLException;

import no.ntnu.nav.logger.*;
import no.ntnu.nav.util.*;
import no.ntnu.nav.SimpleSnmp.*;
import no.ntnu.nav.ConfigParser.*;
import no.ntnu.nav.Database.*;
import no.ntnu.nav.getDeviceData.Netbox;
import no.ntnu.nav.getDeviceData.deviceplugins.*;
import no.ntnu.nav.getDeviceData.dataplugins.*;
import no.ntnu.nav.getDeviceData.dataplugins.Module.*;
import no.ntnu.nav.getDeviceData.dataplugins.Swport.*;

/**
 * <p>
 * Device plugin for extracting VLAN info from the interface name
 * </p>
 *
 * <p>
 * This plugin handles the following OID keys:
 * </p>
 *
 * <ul>
 *	<li>From MIB-II</li>
 *	<ul>
 *	 <li>ifDescr</li>
 *	</ul>
 * </ul>
 * </p>
 *
 */

public class GetVlanFromInterface implements DeviceHandler
{
	private static String[] canHandleOids = {
			"ifDescr", 
	};

	private SimpleSnmp sSnmp;

	public int canHandleDevice(Netbox nb) {
		int v = nb.isSupportedOids(canHandleOids) ? ALWAYS_HANDLE : NEVER_HANDLE;

		Log.d("VLAN_INTERFACE_CANHANDLE", "CHECK_CAN_HANDLE", "Can handle device: " + v);
		return v;
	}

	public void handleDevice(Netbox nb, SimpleSnmp sSnmp, ConfigParser cp, DataContainers containers) throws TimeoutException
	{
		Log.setDefaultSubsystem("VLAN_INTERFACE_DEVHANDLER");

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

		process(nb, netboxid, ip, cs_ro, type, sc);

		// Commit data
		sc.commit();
	}

	private void process(Netbox nb, String netboxid, String ip, String cs_ro, String typeid, SwportContainer sc) throws TimeoutException
	{
		// Set vlan in interface
		Swport trunkPort = null;
		Set vlanSet = new HashSet();

		for (Iterator it = sc.swportIterator(); it.hasNext();) {
			Swport swp = (Swport) it.next();
			String ifdescr = swp.getInterface();
			if (ifdescr == null) continue;

			int vlan;
			int trunkVlan = -1;
			try {
				ResultSet rs = Database.query("SELECT vlan FROM netbox JOIN prefix USING(prefixid) JOIN vlan USING(vlanid) WHERE netboxid="+nb.getNetboxid());
				if (rs.next()) {
					trunkVlan = rs.getInt("vlan");
				}
			} catch (SQLException e) {
			}

			// FastEthernet0.66-802.1Q vLAN subif
			if ( (vlan=extractVlan("FastEthernet0.(\\d+)-802.1Q vLAN subif", ifdescr)) > 0) {
				swp.setVlan(vlan);
			} else
				
			// Do0.66
			if ( (vlan=extractVlan("Do0.(\\d+)", ifdescr)) > 0) {
			    swp.setVlan(vlan);
			} else

			// Vi0.66
			if ( (vlan=extractVlan("Vi0.(\\d+)", ifdescr)) > 0) {
				swp.setVlan(vlan);
			}

			if (vlan == trunkVlan && ifdescr.indexOf("Ethernet") >= 0) {
				trunkPort = swp;
			}

			if (vlan >= 0) {
				vlanSet.add(""+vlan);
			}
		}

		if (trunkPort != null) {
			trunkPort.setTrunk(true);
			for (Iterator it = vlanSet.iterator(); it.hasNext();) {
				String vlan = (String)it.next();
				trunkPort.addTrunkVlan(vlan);
			}
		}
	}

	private int extractVlan(String pattern, String ifdescr) {
		if (ifdescr.matches(pattern)) {
			Matcher m = Pattern.compile(pattern).matcher(ifdescr);
			m.matches();
			try {
				return Integer.parseInt(m.group(1));
			} catch (Exception e) {
			}
		}
		return -1;
	}
}
