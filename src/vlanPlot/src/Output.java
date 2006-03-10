/*
 * NTNU ITEA Nettnu prosjekt
 *
 * Skrvet av: Kristian Eide
 *
 */

import java.util.*;

import java.io.*;
import java.net.*;


class Output
{
	Com com;
	private static final int MAX_BATCH = 30;

	public Output(Com InCom)
	{
		com = InCom;
	}

	public void saveBoksXY(Hashtable nh, int visGruppe)
	{
		boolean allOk = true;
		String begin = "&gruppeid="+visGruppe+"&boks=";
		StringBuffer sb = new StringBuffer(begin);
		int cnt = 0;

		Enumeration e = nh.elements();
		com.d("elements: " + nh.size(), 6);
		while (e.hasMoreElements())
		{
			Nettel n = (Nettel)e.nextElement();

			int id = n.getBoksid();
			int x = n.getX();
			int y = n.getY();

			sb.append(id+","+x+","+y);
			if (++cnt >= MAX_BATCH) {
				if (!sendUpdate(sb.toString())) allOk = false;
				sb = new StringBuffer(begin);
				cnt = 0;
			} else {
				if (e.hasMoreElements()) sb.append("*");
			}
		}

		if (visGruppe == 0) {
			cnt++;
			// Vi må også sende med XY koordinater for gruppene
			Vector group = com.getNet().getGrp();
			if (group.size() > 0) sb.append("&gruppe=");
			for (int i=0; i < group.size(); i++) {
				Grp grp = (Grp)group.elementAt(i);
				sb.append(grp.getId()+","+grp.getX()+","+grp.getY());
				if (i != group.size()-1) sb.append("*");
			}
		}
		if (cnt > 0) {
			if (!sendUpdate(sb.toString())) allOk = false;
		}

		String msg = allOk ? "Data saved" : "Error saving!";
		com.getLeft().setMsg(msg);
	}

/*
	public void saveNettel_old(Hashtable nettel, Vector group)
	{
		Vector link = new Vector();
		Vector net = new Vector();

		Enumeration e = nettel.elements();
		//for (int i = 0; i < nettel.size(); i++)
		while (e.hasMoreElements())
		{
			//Nettel n = (Nettel)nettel.elementAt(i);
			Nettel n = (Nettel)e.nextElement();

			if (n.getType().equals("stam") || n.getType().equals("elink") )
			{
				net.addElement(n);
			} else
			{
				link.addElement(n);
			}
		}

		int[] index = new int[link.size()];
		int[] x = new int[link.size()];
		int[] y = new int[link.size()];
		int[] netIndex = new int[net.size()];
		int[] netX = new int[net.size()];
		int[] netY = new int[net.size()];

		for (int i = 0; i < link.size(); i++)
		{
			Nettel n = (Nettel)link.elementAt(i);
			index[i] = n.getId();
			x[i] = n.getX();
			y[i] = n.getY();
		}
		for (int i = 0; i < net.size(); i++)
		{
			Nettel n = (Nettel)net.elementAt(i);
			netIndex[i] = n.getId();
			if (netIndex[i] < 0) netIndex[i] *= -1;
			netX[i] = n.getX();
			netY[i] = n.getY();
		}


		int[] grpIndex = new int[group.size()];
		int[] grpX = new int[group.size()];
		int[] grpY = new int[group.size()];

		for (int i = 0; i < group.size(); i++)
		{
			Grp g = (Grp)group.elementAt(i);

			grpIndex[i] = g.getId();
			grpX[i] = g.getX();
			grpY[i] = g.getY();
		}

		try
		{

			StringBuffer b = new StringBuffer();

			// lag URL
			b.append("http://bigbud.itea.ntnu.no/vlanPlot/vPServer/vPServer");
			b.append("?section=admin&");
			b.append("request=saveNettelXY&");
			b.append("gruppeId=" + com.getNet().getVisGruppe() + "&");
			b.append("pw=" + com.getAdmin().getPw() + "&");

			// vanlige rutere
			for (int i = 0; i < index.length; i++)
			{
				b.append("nettel" + i + "=" + index[i] + "¤" + x[i] + "¤" + y[i] + "&");
			}

			// net rutere (stam/elink)
			for (int i = 0; i < netIndex.length; i++)
			{
				b.append("net" + i + "=" + netIndex[i] + "¤" + netX[i] + "¤" + netY[i] + "&");
			}

			// grupper
			for (int i = 0; i < grpIndex.length; i++)
			{
				b.append("grp" + i + "=" + grpIndex[i] + "¤" + grpX[i] + "¤" + grpY[i] + "&");
			}

			b.append("send=Send\n");

			System.out.println("URL: " + b.toString() );

			URL url = new URL(b.toString() );
			URLConnection connection = url.openConnection();
			connection.connect();

			BufferedReader in = new BufferedReader(new InputStreamReader(connection.getInputStream()));
			String line;
			while ((line = in.readLine()) != null)
			{
				if (line.equals("Error, wrong user/pw!"))
				{
					// wrong pw
				}
			}



		}
		catch (Exception exp)
		{
			System.out.println("Error (class Output): " + exp.getMessage());
		}



	}
*/

	private boolean sendUpdate(String s)
	{
		String vPServerURL = Input.vPServerURL;

		try
		{
			StringBuffer b = new StringBuffer();

			// lag URL
			b.append(vPServerURL);
			b.append("?section=admin");
			b.append("&request=saveBoksXY");
			b.append("&pw=" + com.getAdmin().getPw() );
			b.append(s);

			System.out.println("URL: " + b.toString() );

			URL url = new URL(b.toString() );
			URLConnection connection = url.openConnection();
			connection.connect();

			BufferedReader in = new BufferedReader(new InputStreamReader(connection.getInputStream()));
			String line;
			while ((line = in.readLine()) != null) {
				if (line.equals("Error, failed authentication!")) {
					com.d("Error, could not save XY, failed authentication!", 1);
					return false;
				}
			}

		} catch (Exception exp) {
			System.out.println("Error (class Output): " + exp.getMessage());
			return false;
		}
		com.d("OK, XY saved!", 1);
		return true;
	}
}



















