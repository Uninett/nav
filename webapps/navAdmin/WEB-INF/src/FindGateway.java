/* NTNU ITEA Nettnu prosjekt
 *
 * Skrvet av: Kristian Eide
 *
 */

import java.util.*;


class FindGateway
{
	String[] gw;
	String[] bits;

	String lastGw;
	String lastBits;
	int lastIndex;

	public FindGateway(String[] InGw, String[] InBits)
	{
		gw = InGw;
		bits = InBits;

		//for (int i = 0; i < gw.length; i++)
		//{
		//	System.out.println("" + i + ": " + gw[i] + " bits: " + bits[i]);
		//}
		//System.out.println("");

		padIpArray(gw);

		// sort
		String[][] data = new String[gw.length][2];
		for (int i = 0; i < gw.length; i++)
		{
			data[i][0] = gw[i];
			data[i][1] = bits[i];
		}
		misc.quickSort(data);
		for (int i = 0; i < gw.length; i++)
		{
			gw[i] = data[i][0];
			bits[i] = data[i][1];
		}

		//for (int i = 0; i < gw.length; i++)
		//{
		//	System.out.println("" + i + ": " + gw[i] + " bits: " + bits[i]);
		//}
	}

	public String findGw(String ip)
	{
		ip = padIp(ip);
		for (int i = 0; i < gw.length; i++)
		{
			//System.out.println("gw: " + gw[i] + " ip: " + ip + " compare: " + gw[i].compareTo(ip) );
			if (gw[i].compareTo(ip) > 0)
			{
				return verifyGw(ip, i-1);
			}
		}
		return null;
	}

	public String verifyGw(String ip, int index)
	{
		/*
		IP gwIp = new IP(gw[index]);
		String mask = IP.getMaskFromBits(Integer.parseInt(bits[index]));

		if (gwIp.inSameSubnet(ip, mask) )
		{
			IP lgw = new IP(gw[index]);
			lastGw = lgw.toString();
			lastBits = bits[index];
			lastIndex = index;

			return lastGw;
		} else
		{
			return null;
		}
		*/
		return null;
	}

	public String getLastGw() { return lastGw; }
	public String getLastBits() { return lastBits; }
	public int getLastIndex() { return lastIndex; }

	public static String padIp(String s)
	{
		String[] oct = misc.tokenize(s, ".");
		oct[0] = pad(oct[0], 3);
		oct[1] = pad(oct[1], 3);
		oct[2] = pad(oct[2], 3);
		oct[3] = pad(oct[3], 3);

		return oct[0] + "." + oct[1] + "." + oct[2] + "." + oct[3];
	}

	public static void padIpArray(String[] s)
	{
		for (int i = 0; i < s.length; i++)
		{
			String[] oct = misc.tokenize(s[i], ".");

			oct[0] = pad(oct[0], 3);
			oct[1] = pad(oct[1], 3);
			oct[2] = pad(oct[2], 3);
			oct[3] = pad(oct[3], 3);

			s[i] = oct[0] + "." + oct[1] + "." + oct[2] + "." + oct[3];
		}
	}

	public static String pad(String s, int n)
	{
		for (int i = s.length(); i < n; i++)
		{
			s = "0" + s;
		}
		return s;
	}



/*
	public static void main(String[] args)
	{
		String[] gw = new String[4];
		gw[0] = "129.241.150.1";
		gw[1] = "129.241.75.192";
		gw[2] = "129.241.38.1";
		gw[3] = "129.241.176.64";

		String[] bits = new String[4];
		bits[0] = "24";
		bits[1] = "27";
		bits[2] = "24";
		bits[3] = "26";

		FindGateway fg = new FindGateway(gw, bits);

		String s = fg.findGw("129.241.75.192");

		System.out.println("gw: " + s);



	}
*/



}