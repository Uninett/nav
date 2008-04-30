package no.ntnu.nav.getDeviceData.dataplugins.Arp;

import java.net.InetAddress;
import java.util.Map;

import no.ntnu.nav.getDeviceData.dataplugins.DataContainer;
import no.ntnu.nav.getDeviceData.dataplugins.DataHandler;

/**
 * An interface for device plugins to store ARP data.
 * 
 * @author gogstad
 *
 */
public class ArpContainer implements DataContainer {
	
	private static final int PRIORITY_ARP = PRIORITY_NORMAL;
	
	private ArpHandler ah;
	private boolean commit = false;
	private Map<InetAddress,String> ipMacMap;
	
	
	protected ArpContainer(ArpHandler ah) {
		this.ah = ah;
	}
	
	public void commit() {
		commit = true;
	}

	public DataHandler getDataHandler() {
		return ah;
	}

	public String getName() {
		return "ArpContainer";
	}

	public int getPriority() {
		return PRIORITY_ARP;
	}
	
	public void setIpMacMap(Map<InetAddress,String> map) {
		this.ipMacMap = map;
	}

	public Map<InetAddress,String> getIpMacMap() {
		return ipMacMap;
	}
	
	public boolean isCommited() {
		return commit;
	}
	
}
