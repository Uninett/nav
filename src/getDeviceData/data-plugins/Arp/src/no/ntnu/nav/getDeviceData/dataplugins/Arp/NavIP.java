package no.ntnu.nav.getDeviceData.dataplugins.Arp;

import java.net.InetAddress;
import java.net.UnknownHostException;
import java.util.Arrays;

/**
 * 
 * java.net.InetAddress wrapper class.
 *
 * This class was introduced when prefixcaching was implemented
 * in ARPHandler and is therefore not widely used (nor developed).
 * 
 * @author gogstad
 *
 */
public class NavIP implements Comparable<NavIP>{
	
	private InetAddress prefixAddress;
	private int prefixLength;
	
	public NavIP(byte[] ip, int prefixLength) {
		try {
			this.prefixAddress = InetAddress.getByAddress(ip);
			this.prefixLength = prefixLength;
		} catch (UnknownHostException e) {
			e.printStackTrace();
		}
	}
	
	public NavIP(String ip, int prefixLength) {
		this.prefixAddress = Util.getInetAddress(ip);
		this.prefixLength = prefixLength;
	}
	
	public NavIP(InetAddress ip, int prefixLength) {
		this.prefixAddress = ip;
		this.prefixLength = prefixLength;
	}
	
	public InetAddress getPrefixAddress() {
		return prefixAddress;
	}

	public void setPrefixAddress(InetAddress prefixAddress) {
		this.prefixAddress = prefixAddress;
	}

	public int getPrefixLength() {
		return prefixLength;
	}

	public void setPrefixLength(int prefixLength) {
		this.prefixLength = prefixLength;
	}

	public int compareTo(NavIP o) {
		if(Arrays.equals(prefixAddress.getAddress(), o.prefixAddress.getAddress()))
			return 0;
		if(prefixLength > o.getPrefixLength())
			return -1;
		else
			return 1;
	}
	

}
