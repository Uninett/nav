/*
 * NTNU ITEA Nettnu prosjekt
 *
 * Dette programmet er laget slik at det kan kjøres både som en vanlig
 * applikasjon og som en applet. Merk at programmet må ha nødvendig
 * tilgang dersom det kjøres som applet.
 *
 * Skrvet av: Kristian Eide
 *
 */

import java.applet.*;
import java.util.*;
import java.awt.*;
import java.awt.event.*;
import java.io.*;


public class vlanPlot extends Applet
{

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
//		setLocation(150, 150);
		setSize(800, 600);

		Com com = new Com();

		//com.setDocumentBase(getDocumentBase() );
		com.setApplet(this);

		Keyl keyl = new Keyl(com);
		Mouse mouse = new Mouse(com);
		MouseMove mv = new MouseMove(com);

		com.setKeyl(keyl);
		com.setMouse(mouse);
		com.setMouseMove(mv);

		addKeyListener(keyl);
//		addMouseMotionListener(ml);

		setLayout(new GridLayout(1, 1));
		add(new panel(com));

	}
}

class frame extends Frame
{
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
//		addMouseMotionListener(ml);

		add(new panel(com));
	}
}

class panel extends Panel
{
	int DEBUG_LEVEL = 10;

	Com com;
	Nettel visNettel;

	public panel(Com InCom)
	{
		com = InCom;
		setBackground(Color.white);

		if (System.getProperty("java.vendor").equals("Netscape Communications Corporation")) {
			DEBUG_LEVEL = 0;
		}

		Admin admin = new Admin(com);
		com.setAdmin(admin);
		com.setDebugLevel(DEBUG_LEVEL);
		com.setMainPanel(this);


		// Get Java version number
		try {
			String v = System.getProperty("java.version");
			StringTokenizer st = new StringTokenizer(v, ".");
			if (st.hasMoreTokens()) com.setJavaMajorVersion(Integer.parseInt(st.nextToken()));
			if (st.hasMoreTokens()) com.setJavaMinorVersion(Integer.parseInt(st.nextToken()));
			if (st.hasMoreTokens()) com.setJavaRevisionVersion(Integer.parseInt(st.nextToken()));
			com.d("Running on Java version: " + v, 0);
		} catch (Exception e) {
			com.d("Error getting java version number, assuming 1.0.0", 0);
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




/*
		// OLD GRIDBAG
		// jepp, gridbag må til
		GridBagLayout gridbag = new GridBagLayout();
		setLayout(gridbag);
		GridBagConstraints c = new GridBagConstraints();
		c.fill = GridBagConstraints.BOTH;

		// Left
		Left l = new Left(com);
		c.weightx = 0; c.weighty = 0;
		c.gridx = 1; c.gridy = 1; c.gridwidth = 1; c.gridheight = 1;
		//c.ipady = 100;
		//c.ipady = 100;
		gridbag.setConstraints(l, c);
		add(l, c);
		com.setLeft(l);

		// Net
		Net n = new Net(com);
		c.weightx = 100; c.weighty = 100;
		c.gridx = 2; c.gridy = 1; c.gridwidth = 8; c.gridheight = 1;
		//c.ipady = 100;
		//c.ipady = 0;
		gridbag.setConstraints(n, c);
		add(n, c);
		com.setNet(n);
*/

		if (visNettel != null) {
			com.d("Jumping to boksid: " + visNettel.getBoksid() + ", vlan: " + visNettel.getVlan(), 0);
			n.setVisNettel(visNettel);
		}

		n.addComponentListener(new NetComponentListener(n));
		//n.showBynett();
		//n.refreshNettel();

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


			// Skal vi starte på en bestemt boksid?
			/*
			String gotoBoksid = "271";
			if (gotoBoksid != null && gotoBoksid.length() > 0) {
				String gotoVlan = "g";
				int boksid=0,vlan=0;
				try {
					boksid = Integer.parseInt(gotoBoksid);
					if (gotoVlan != null) vlan = Integer.parseInt(gotoVlan);
				} catch (NumberFormatException e) {}

				visNettel = new Nettel(com, boksid, "", "", "1", vlan);
			}
			*/

		} else {
			com.d("Henter parametere fra HTML-fil", 1);
			vPServerURL = a.getParameter("vPServerURL");
			lastURL = a.getParameter("lastURL");
			cricketURL = a.getParameter("cricketURL");
			netflowURL = a.getParameter("netflowURL");

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






