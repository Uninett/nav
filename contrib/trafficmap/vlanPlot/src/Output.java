/*
 * $Id$ 
 *
 * Copyright 2000-2005 Norwegian University of Science and Technology
 * 
 * This file is part of Network Administration Visualized (NAV)
 * 
 * NAV is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 * 
 * NAV is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with NAV; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 *
 *
 * Authors: Kristian Eide <kreide@gmail.com>
 */

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.URL;
import java.net.URLConnection;
import java.util.Enumeration;
import java.util.Hashtable;
import java.util.Vector;


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



















