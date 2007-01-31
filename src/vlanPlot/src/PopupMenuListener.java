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

import java.awt.MenuItem;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.text.SimpleDateFormat;
import java.util.Calendar;
import java.util.Date;
import java.util.GregorianCalendar;
import java.util.StringTokenizer;


class PopupMenuListener implements ActionListener
{
	Com com;

	public PopupMenuListener(Com InCom)
	{
		com = InCom;
	}

    public void actionPerformed(ActionEvent e)
    {
		MenuItem mi = (MenuItem)e.getSource();

		if (mi.getName().equals("VLAN_MENU")) {
			procVlan(e);
		} else if (com.getActiveMenu().useCricket() || e.getActionCommand().indexOf("/") == -1) {
			procCricket(e);
		} else {
			procNetflow(e);
		}
	}

	private void procDeviceInfo(ActionEvent ae)
	{
		String cmd = ae.getActionCommand();
		PopupMenus activeMenu = com.getActiveMenu();
		String nettelName = activeMenu.getFullNettelName();
		String url = Input.rootURL + "/browse/";

		if (cmd.equals(Net.gwMenuText[0] ))
		{
			url += nettelName;
		} else
		if (cmd.equals(Net.swMenuText[0] )) {
			url += nettelName;
		}

		com.d("  Showing URL: " + url, 2);
		showURL(url);
	}

	private void procNetworkExplorer(ActionEvent ae)
	{
		String cmd = ae.getActionCommand();
		PopupMenus activeMenu = com.getActiveMenu();
		String nettelName = activeMenu.getFullNettelName();
		String url = Input.rootURL + "/navAdmin/servlet/navAdmin?section=ni&func=visTopologi&searchField=0.sysname&searchFor=";

		if (cmd.equals(Net.gwMenuText[1] ))
		{
			url += nettelName;
		} else
		if (cmd.equals(Net.swMenuText[1] )) {
			url += nettelName;
		}

		url += "#searchtarget";
		com.d("  Showing URL: " + url, 2);
		showURL(url);
	}

	private void procVlan(ActionEvent ae)
	{
		MenuItem mi = (MenuItem)ae.getSource();
		String vlanName = mi.getLabel();
		StringTokenizer st = new StringTokenizer(vlanName);
		try {
			int vlan = Integer.parseInt(st.nextToken());
			com.d("  Request change to vlan: " + vlan, 2);
			com.getNet().changeVisVlan(vlan);
		} catch (NumberFormatException e) {}
	}

	private void procCricket(ActionEvent e)
	{
		PopupMenus activeMenu = com.getActiveMenu();
		String nettelName = activeMenu.getFullNettelName();
		String ifName = activeMenu.getIfName();
		String cricketUrl = "";

		// Litt formatering av ifName er nødvendig
		ifName = ifName.toLowerCase();

		String kommando = e.getActionCommand();
		if (kommando.equals(Net.linkMenuText[0] ))
		{ // Last
			kommando = "Octets";
		} else
		if (kommando.equals(Net.linkMenuText[1] ))
		{ // Pakker
			kommando = "Packets";
		} else
		if(kommando.equals(Net.linkMenuText[2] ))
		{ // Dropp
			kommando = "Drops";
		} else
		if(kommando.equals(Net.linkMenuText[3] ))
		{ // Feil
			kommando = "Errors";
		} else
		if(kommando.equals(Net.gwMenuText[0] ))
		{
			procDeviceInfo(e);
			return;
		} else
		if(kommando.equals(Net.gwMenuText[1] ))
		{
			procNetworkExplorer(e);
			return;
		} else
		if(kommando.equals(Net.gwMenuText[2] ))
		{ // CPU Last
			kommando = "cpu";
		} else
		if(kommando.equals(Net.gwMenuText[2] ))
		{ // Nettliste
			//String gwName = com.getGwMenu().getNettelName();
			//showURL(CGIBINURL+"nettliste.pl?gw=" + nettelName);
			return;
		} else
		if(kommando.equals(Net.swMenuText[0] ))
		{
			procDeviceInfo(e);
			return;
		}
		if(kommando.equals(Net.swMenuText[1] ))
		{
			procNetworkExplorer(e);
			return;
		}
		if(kommando.equals(Net.swMenuText[2] ))
		{
			kommando = "backplane";
		}


		if (activeMenu == com.getGwMenu() )
		{ // gw
			cricketUrl = "index.cgi?target=%2Frouters%2F" + nettelName + "&ranges=d%3Aw&view=" + kommando;

		} else
		if (activeMenu == com.getSwMenu() )
		{ // sw
			cricketUrl = "index.cgi?target=%2Fswitches%2F" + nettelName + "&ranges=d%3Aw&view=" + kommando;

		} else
		if (activeMenu == com.getLinkMenu() || activeMenu == com.getLinkGwMenu())
		{ // link
			if (activeMenu.getIsRouter() )
			{
				cricketUrl = "index.cgi?target=%2Frouter-interfaces%2F" + nettelName + "%2F" + ifName.replace('/','_') + "&ranges=d%3Aw&view=" + kommando;
			} else
			{
				cricketUrl = "index.cgi?target=%2Fswitch-ports%2F" + nettelName + "%2F" + ifName + "&ranges=d%3Aw&view=" + kommando;
			}
		}

		showURL(Input.cricketURL + cricketUrl);


    }

	private void procNetflow(ActionEvent e)
	{
		PopupMenus activeMenu = com.getActiveMenu();

		String netflowUrl = "";
		String ip = e.getActionCommand();

		// bytt ut slash i ip
		{
			final String slash = "%2F";
			int index = ip.indexOf("/");
			ip = ip.substring(0, index) + slash + ip.substring(index+1, ip.length());
		}

		// Sjekk om valgt tid er etter 00:05 dagens dato
		Calendar calendar = new GregorianCalendar();
		calendar.set(Calendar.HOUR, 0);
		calendar.set(Calendar.MINUTE, 4);
		calendar.set(Calendar.SECOND, 59);
		Date midnight = calendar.getTime();
		Date startTid = com.getBeginLastDate();
		Date endTid = com.getEndLastDate();

		if (startTid.before(midnight)) {
			// bruk script for dato
			SimpleDateFormat tid = new SimpleDateFormat("yyyyMMdd");
			int today = Integer.parseInt(tid.format(midnight));
			int start = Integer.parseInt(tid.format(startTid));
			int end = Integer.parseInt(tid.format(endTid));
			start = Math.min(start, today-2);
			end = Math.min(end, today-2);

			netflowUrl = "report.html?router=All&ip=" + ip + "&list=10&from=" + start + "&to=" + end;

		} else {
			// bruk script for siste døgn
			SimpleDateFormat tid = new SimpleDateFormat("HHmm");
			netflowUrl = "report2.html?router=All&ip=" + ip + "&list=10&from=" + tid.format(startTid)+ "&to=" + tid.format(endTid);

		}
		
		showURL(Input.netflowURL + netflowUrl);
	}

	public void showURL(String url)
	{
		com.showURL(url);
	}



}