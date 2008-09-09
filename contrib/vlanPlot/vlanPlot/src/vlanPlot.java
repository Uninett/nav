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

/*
 * Dette programmet er laget slik at det kan kjøres både som en vanlig
 * applikasjon og som en applet. Merk at programmet må ha nødvendig
 * tilgang dersom det kjøres som applet.
 *
 */

import java.applet.Applet;
import java.awt.Color;
import java.awt.Cursor;
import java.awt.Frame;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.GridLayout;
import java.awt.Panel;
import java.awt.Scrollbar;
import java.awt.event.WindowAdapter;
import java.awt.event.WindowEvent;
import java.net.MalformedURLException;
import java.net.URL;
import java.util.StringTokenizer;


public class vlanPlot extends Applet
{

	/**
	 * 
	 */
	private static final long serialVersionUID = 1L;

	// For å kjøre programmet som applikasjon
	public static void main(String[] args)
	{
		Frame f = new frame();
		//f = new frame();
		f.show();
	}

	// For å kjøre programmet som applet
	public void init()
	{
		// Make sure we fetch config from vPServer each time the applet is initialized
		Net.setConfig = false;

		setSize(800, 600);

		Com com = new Com();

		com.setApplet(this);

		Keyl keyl = new Keyl(com);
		Mouse mouse = new Mouse(com);
		MouseMove mv = new MouseMove(com);

		com.setKeyl(keyl);
		com.setMouse(mouse);
		com.setMouseMove(mv);

		addKeyListener(keyl);

		setLayout(new GridLayout(1, 1));
		add(new panel(com));
	}
}

class frame extends Frame
{
	/**
	 * 
	 */
	private static final long serialVersionUID = 1L;

	public frame()
	{
		addWindowListener(new WindowAdapter()
		{
			public void windowClosing(WindowEvent e)
			{
				System.exit(0);
			}
		} );

		setLocation(150, 150);
		setSize(800, 620);

		Com com = new Com();

		Keyl keyl = new Keyl(com);
		Mouse mouse = new Mouse(com);
		MouseMove mv = new MouseMove(com);

		com.setKeyl(keyl);
		com.setMouse(mouse);
		com.setMouseMove(mv);

		addKeyListener(keyl);

		add(new panel(com));
	}
}

class panel extends Panel
{
	/**
	 * 
	 */
	private static final long serialVersionUID = 1L;

	int DEBUG_LEVEL = 10;

	Com com;
	Nettel visNettel;

	public panel(Com InCom)
	{
		com = InCom;
		setBackground(Color.white);

		/*
		if (System.getProperty("java.vendor").equals("Netscape Communications Corporation")) {
			DEBUG_LEVEL = 0;
		}
		*/
		System.out.println("Jave vendor: " + System.getProperty("java.vendor"));
		if (System.getProperty("java.vendor").toLowerCase().indexOf("Microsoft") < 0) {
			//DEBUG_LEVEL = 0;
		}

		Admin admin = new Admin(com);
		com.setAdmin(admin);
		com.setDebugLevel(DEBUG_LEVEL);
		com.setMainPanel(this);


		// Get Java version number
		String v = null;
		try {
			v = System.getProperty("java.version");
			StringTokenizer st = new StringTokenizer(v, "_");
			st = new StringTokenizer(st.nextToken(), ".");
			if (st.hasMoreTokens()) com.setJavaMajorVersion(Integer.parseInt(st.nextToken()));
			if (st.hasMoreTokens()) com.setJavaMinorVersion(Integer.parseInt(st.nextToken()));
			if (st.hasMoreTokens()) com.setJavaRevisionVersion(Integer.parseInt(st.nextToken()));
			com.d("Running on Java version: " + v, 0);
		} catch (Exception e) {
			com.d("Error getting java version number, assuming 1.0.0 ("+v+")", 0);
		}

		// Sett parametere fra HTML-filen, hvis dette er en applet, ellers brukes default-verdier
		initParameters();

		// jepp, gridbag må til
		GridBagLayout gridbag = new GridBagLayout();
		setLayout(gridbag);
		GridBagConstraints c = new GridBagConstraints();
		c.fill = GridBagConstraints.BOTH;

		// Left
		Left l = new Left(com); //l.setSize(100, 100);
		c.weightx = 0; c.weighty = 100;
		c.gridx = 1; c.gridy = 1; c.gridwidth = 1; c.gridheight = 3;
		//c.ipadx = 100;
		//c.ipady = 100;
		gridbag.setConstraints(l, c);
		add(l, c);
		com.setLeft(l);

		// Top scrollbar
		Scrollbar topScroll = new Scrollbar(Scrollbar.HORIZONTAL, 0, 1, 0, 1); // init, visible, min, max
		c.weightx = 0; c.weighty = 0;
		c.gridx = 2; c.gridy = 1; c.gridwidth = 8; c.gridheight = 1;
		c.ipadx = 0;
		gridbag.setConstraints(topScroll, c);
		add(topScroll, c);
		com.setTopScroll(topScroll);

		// Middle scrollbar
		Scrollbar midScroll = new Scrollbar(Scrollbar.VERTICAL, 0, 1, 0, 1);
		c.weightx = 0; c.weighty = 0;
		c.gridx = 10; c.gridy = 1; c.gridwidth = 1; c.gridheight = 3;
		//c.ipadx = 0;
		gridbag.setConstraints(midScroll, c);
		add(midScroll, c);
		com.setMidScroll(midScroll);

		// Bottom scrollbar
		Scrollbar bottomScroll = new Scrollbar(Scrollbar.HORIZONTAL, 0, 1, 0, 1);
		c.weightx = 0; c.weighty = 0;
		c.gridx = 2; c.gridy = 3; c.gridwidth = 8; c.gridheight = 1;
		//c.ipadx = 0;
		gridbag.setConstraints(bottomScroll, c);
		add(bottomScroll, c);
		com.setBottomScroll(bottomScroll);

		// Net
		Net n = new Net(com);
		c.weightx = 100; c.weighty = 100;
		c.gridx = 2; c.gridy = 2; c.gridwidth = 8; c.gridheight = 1;
		//c.ipadx = 600;
		//c.ipady = 0;
		gridbag.setConstraints(n, c);
		add(n, c);
		com.setNet(n);


		if (visNettel != null) {
			com.d("Jumping to boksid: " + visNettel.getBoksid() + ", vlan: " + visNettel.getVlan(), 0);
			n.setVisNettel(visNettel);
		}

		n.addComponentListener(new NetComponentListener(n));

	}

	private void initParameters()
	{
		Applet a = com.getApplet();
		String vPServerURL, lastURL, cricketURL, netflowURL;

		if (a == null) {
			com.d("Ikke applet, bruker default-parametere", 1);
			vPServerURL = Input.vPServerURLDefault;
			lastURL = Input.lastURLDefault;
			cricketURL = Input.cricketURLDefault;
			netflowURL = Input.netflowURLDefault;

		} else {
			com.d("Henter parametere fra HTML-fil", 1);
			vPServerURL = a.getParameter("vPServerURL");
			lastURL = a.getParameter("lastURL");
			cricketURL = a.getParameter("cricketURL");
			netflowURL = a.getParameter("netflowURL");

			Input.sessionid = a.getParameter("nav_sessid");
			Input.authuser = a.getParameter("user");

			// Skal vi starte på en bestemt boksid?
			String gotoBoksid = a.getParameter("gotoBoksid");
			if (gotoBoksid != null && gotoBoksid.length() > 0) {
				String gotoVlan = a.getParameter("gotoVlan");
				int boksid=0,vlan=0;
				try {
					boksid = Integer.parseInt(gotoBoksid);
					if (gotoVlan != null) vlan = Integer.parseInt(gotoVlan);
				} catch (NumberFormatException e) {}

				visNettel = new Nettel(com, boksid, "", "", "1", vlan);
			}

		}
		Input.vPServerURL = vPServerURL;
		Input.lastURL = lastURL;
		Input.cricketURL = cricketURL;
		Input.netflowURL = netflowURL;
		try {
			URL url = new URL(vPServerURL);
			Input.rootURL = url.getProtocol()+"://"+url.getHost();
		} catch (MalformedURLException e) {
		}
	}

	public void setWaitCursor()
	{
		setCursor(Cursor.getPredefinedCursor(Cursor.WAIT_CURSOR) );
	}
	public void setDefaultCursor()
	{
		setCursor(Cursor.getPredefinedCursor(Cursor.DEFAULT_CURSOR) );
	}
}






