package no.ntnu.nav.getDeviceData.dataplugins.Arp;

import java.net.InetAddress;
import java.net.UnknownHostException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;

import no.ntnu.nav.ConfigParser.ConfigParser;
import no.ntnu.nav.logger.Log;


/**
 * Util class, mainly helper methods for InetAddress and ARPHandler
 * 
 * @author gogstad
 * @author janivala
 *
 */
public class Util {
	
	/**
	 * @return Returns a InetAddress instance of the argument ip.
	 */
	public static InetAddress getInetAddress(String ip) {
		InetAddress returnIp = null;

		if(isIpv6(ip)) {
			String[] longAddress = Util.ipv6ShortToLong(ip).split(":");
			ArrayList<String> nybbleArrayBuilder = new ArrayList<String>(32);
			for(String hexlet: longAddress) {
				String nybble1 = hexlet.substring(0, 2);
				String nybble2 = hexlet.substring(2);
				nybbleArrayBuilder.add(nybble1);
				nybbleArrayBuilder.add(nybble2);
			}
			String[] nybbleArray = nybbleArrayBuilder.toArray(new String[nybbleArrayBuilder.size()]);
			try {
				returnIp = InetAddress.getByAddress(Util.convertToUnsignedByte(nybbleArray, 16));
			} catch (UnknownHostException e) {
				e.printStackTrace();
				return null;
			}
		}
		else {
			try {
				String[] ipArray = ip.split("\\.");
				returnIp = InetAddress.getByAddress(Util.convertToUnsignedByte(ipArray, 10));
			} catch (UnknownHostException e) {
				e.printStackTrace();
				return null;
			}
		}
		return returnIp;
	}

	/**
	 * Checks whether or not the argument ip is listed in getDeviceData.conf under
	 * "ignoreprefices".
	 * 
	 */
	public static boolean shouldIgnoreIp(InetAddress ip, ConfigParser cp) {
		String ignorePreficesString = (String)cp.get("ignoreprefices");
		Map<InetAddress,Integer> ignorePrefices = new HashMap<InetAddress,Integer>();
		
		for(String s: ignorePreficesString.split(",")) {
			String prefix = s.trim();
			if(prefix.split("/").length != 2)
				continue;

			String ipString = prefix.split("/")[0];
			Integer mask = Integer.parseInt(prefix.split("/")[1]);
			InetAddress newIp = getInetAddress(ipString);
			
			if(newIp == null)
				return false;
			
			ignorePrefices.put(newIp,mask);
		}
		
		for(Map.Entry<InetAddress, Integer> me: ignorePrefices.entrySet()) 
			if(isSubnet(me.getKey(), me.getValue(), ip))
				return true;

		return false;
		
	}
	
	public static boolean isIpv6(String ip) {
		return ip.indexOf(":") >= 0;
	}
	
	public static boolean getBit(int value, int bit) {
		return (value & (1 << bit)) != 0;
	}

	public static int getByteValue(byte value) {
		int result = 0;
		result |= value & 0xFF;
		return result;
	}

	/**
	 *  @return Returns true if supernet >> subnet, false if not.
	 */
	public static boolean isSubnet(InetAddress supernet, int prefixLength, InetAddress subnet) {
		byte[] supernetBytes = supernet.getAddress();
		byte[] subnetBytes = subnet.getAddress();
		
		int checkBytes = prefixLength / 8;
		int checkBits = prefixLength % 8;

		for(int i = 0; i < checkBytes; i++)
			if(supernetBytes[i] != subnetBytes[i])
				return false;

		if(checkBits == 0)
			return true;

		int ipPrefixByteVal = Util.getByteValue(supernetBytes[checkBytes]);
		int addrByteVal = Util.getByteValue(subnetBytes[checkBytes]);

		for(int i = 7; i > 7 - checkBits; i--)
			if(getBit(ipPrefixByteVal, i) != getBit(addrByteVal,i))
				return false;

		return true;
	}
	
	/**
	 * Converts an int array of unsigned bytes to a byte
	 * array by using negative numbers for bytes > 127.
	 * (Java's byte type is signed)
	 * 
	 * @param array Array of integers
	 * @return byte array
	 */
	public static byte[] convertToUnsignedByte(int[] array) {
		byte[] result = new byte[array.length];
		
		for(int i = 0; i < array.length; i++) {
			assert array[i] <= 256;
			if(array[i] > 127)
				result[i] = (byte)(array[i]-256);
			else
				result[i] = (byte)array[i];
		}
		
		return result;
	}
	
	/**
	 * Converts an array of unsigned bytes to a byte array, integers > 127
	 * is represented with negative numbers.
	 * 
	 * @param array String array with numbers, support hex
	 * @param radix The base
	 * @return byte array
	 */
	public static byte[] convertToUnsignedByte(String[] array, int radix) {
		int[] result = new int[array.length];
		for(int i = 0; i < array.length; i++)
			result[i] = Integer.parseInt(array[i], radix);
		
		return convertToUnsignedByte(result);
	}
	
	/**
	 * Truncates the MAC address.
	 * 
	 * ie.	input: 03:50:33:6a:ff:ee:00:00
	 * 		output: 03:50:33:6a:ff:ee
	 * 
	 * @param mac Address to be truncated
	 * @return Truncated mac
	 */
	public static String truncateMAC(String mac) {
		String[] nybbles = mac.split(":");
		if(nybbles.length > 6) {
			String[] result = new String[6];
			System.arraycopy(nybbles, 0, result, 0, result.length);
			return stringJoin(result,":");			
		}
		else
			return mac;
	}
	
	/**
	 * Equivalent to python's string.join
	 * 
	 * Joins array with delimiter.
	 * 
	 * ie.	array = ["pim","pom","pam"]
	 * 		delimiter = ":"
	 * 
	 * 		result = "pim:pom:pam"
	 * 
	 * @param array Array to be joined
	 * @param delimiter Delimiter to be used
	 * @return Array joined by delimiter
	 */
	public static String stringJoin(String[] array, String delimiter) {
		if(array.length == 0)
			return "";		
		
		StringBuilder sb = new StringBuilder(array.length*(1+delimiter.length()));
		for(String s: array) {
			sb.append(s);
			sb.append(delimiter);
		}
		sb.delete(sb.length()-delimiter.length(), sb.length());
		return sb.toString();
	}
	
	/**
	 * Converts an IPv6 address on short format to long format.
	 * 
	 * Assumes standard colon notation.
	 * 
	 * @param IPv6 Short format IPv6 address
	 * @return Long format IPv6 address
	 */
	public static String ipv6ShortToLong(String IPv6) {
		String[] array = IPv6.split(":");
		ArrayList<String> resultArray = new ArrayList<String>(16);
		StringBuilder result = new StringBuilder();
		
		for(int i = 0; i < array.length; i++) {
			StringBuilder nybble = new StringBuilder(array[i]);
			if(nybble.length() == 0) {
				for(int j = 0; j < 8-array.length+1; j++)
					resultArray.add("0000");
				continue;
			}
			
			if(nybble.length() < 4) {
				int length = nybble.length();
				for(int j = 0; j < 4-length; j++)
					nybble.insert(0, "0");
			}
			
			resultArray.add(nybble.toString());
		}
		int size = resultArray.size();
		for (int i = 0; i < 8-size; i++)
			resultArray.add("0000");
		
		for(String s: resultArray)
			result.append(s + ":");
		result.deleteCharAt(result.length()-1);
		
		return result.toString();
	}
}
