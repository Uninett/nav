package no.ntnu.nav.getDeviceData.deviceplugins.ARPLogger;

import java.util.ArrayList;

public class Util {
	
	/**
	 * Converts an int array of unsigned bytes to a byte
	 * array by using negative numbers for bytes > 127.
	 * (Java's byte type is signed)
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
	
	public static byte[] convertToUnsignedByte(String[] array, int radix) {
		int[] result = new int[array.length];
		for(int i = 0; i < array.length; i++)
			result[i] = Integer.parseInt(array[i], radix);
		
		return convertToUnsignedByte(result);
	}

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
