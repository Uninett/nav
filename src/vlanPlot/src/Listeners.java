/*
 * NTNU ITEA Nettnu prosjekt
 *
 * Skrvet av: Kristian Eide
 *
 */

import java.util.*;
import java.net.*;

import java.awt.*;
import java.awt.event.*;

import java.text.*;


class AdminListener implements ActionListener
{
	Com com;
	private Button moveMode;
	private Button saveBoksXY;

	public AdminListener(Com InCom)
	{
		com = InCom;
	}

	public void setMoveMode(Button moveMode) { this.moveMode=moveMode; }
	public void setSaveBoksXY(Button saveBoksXY) { this.saveBoksXY=saveBoksXY; }

	public void actionPerformed(ActionEvent e)
	{
		//String s = e.getActionCommand();
		Object o = e.getSource();

		if (o.equals(moveMode)) {
			// Det er kun lov å trykke denne knappen i bynettView-modus
			if (com.getNet().getBynettView()) {
				Admin adm = com.getAdmin();
				boolean b = (adm.getMoveMode()) ? false : true;
				setMoveMode(b);
			}
		} else
		if (o.equals(saveBoksXY)) {
			// Det er kun lov å trykke denne knappen i bynettView-modus
			if (com.getNet().getBynettView()) {
				Output outp = new Output(com);
				outp.saveBoksXY(com.getNet().getNettelHash(), com.getNet().getVisGruppeid() );
			}
		}
	}

	public void setMoveMode(boolean b)
	{
		// Skru av eller på move-mode
		Admin adm = com.getAdmin();
		adm.setMoveMode(b);
		moveMode.setLabel( (b)?"Off":"Move" );
	}

}

class Keyl implements KeyListener
{
	Com com;

	public Keyl(Com InCom)
	{
		com = InCom;
	}


	public void keyPressed(KeyEvent evt)
	{}

	public void keyReleased(KeyEvent evt)
	{
		if (evt.getKeyCode() == KeyEvent.VK_ENTER)
		{
			com.d("Trykker 'Enter'", 8);
			//t.flytt();
			//t.repaint();
		}
	}

	public void keyTyped(KeyEvent evt)
	{}
}

class Mouse implements MouseListener
{
	Com com;
	boolean overNet = false;
	boolean overLogo = false;
	boolean button1 = false;
	boolean button2 = false;
	boolean meta = false;


	public Mouse(Com InCom)
	{
		com = InCom;
	}

	public boolean isOverNet()
	{
		return overNet;
	}

	public void mouseClicked(MouseEvent e)
	{
		if ((e.getModifiers() & InputEvent.BUTTON1_MASK) != 0)
		{
			button1 = true;
		}
		if ( ((e.getModifiers() & InputEvent.BUTTON2_MASK) != 0) || ((e.getModifiers() & InputEvent.BUTTON3_MASK) != 0) )
		{
			button2 = true;
		}

		/*
		if (com.getNet().isBynettClicked(e.getX(), e.getY() ))
		{
			com.getNet().setVisNettel(null);
			com.getNet().setVisGruppe(0);
			com.getNet().refreshNettel();

		} else
		if (com.getNet().isKjernenettClicked(e.getX(), e.getY() ))
		{
			com.getNet().setVisNettel(null);
			com.getNet().setVisGruppe(1);
			com.getNet().refreshNettel();

		} else
		if (com.getNet().isTestnettClicked(e.getX(), e.getY() ))
		{
			com.getNet().setVisNettel(null);
			com.getNet().setVisGruppe(2);
			com.getNet().refreshNettel();
		} else
		*/

		int x = e.getX();
		int y = e.getY();

		if (!overNet && button1 && !button2 && y < 100) {
			// Klikket på ikonet
			com.showURL(Net.netLink);
			return;
		}
		if (com.getNet().isBackKnappClicked(e.getX(), e.getY() )) {
			com.d("Reverse history...",2);
			com.getNet().reverseHistory();
		}


		if (!com.getAdmin().getMoveMode() )
		{
			if (overNet)
			{
				Enumeration enu = com.getNet().getNettelHash().elements();

				//int x = e.getX(); //int x = com.getMouseX();
				//int y = e.getY(); //int y = com.getMouseY();

				//System.out.println("x: " + com.getMouseX() + " x2: " + e.getX() );

				//for (int i = v.size()-1; i >= 0; i--)
				boolean overNettel = false;
				while (enu.hasMoreElements())
				{
					//Nettel n = (Nettel)v.elementAt(i);
					Nettel n = (Nettel)enu.nextElement();

					if (n.contains(x, y))
					{
						overNettel = true;
						com.d("Klikket: " + n.getName(),3);
						if (button1)
						{ // venstre-klikk på nettel/link
							if (n.getIsClickable() )
							{
								n.disablePopup();
								if (n.getKat().equals("gw")) n.setVlan(0);

								com.d("------------------------------------------------------------------------", 1);
								com.d("Aktivert klikk: " + n.getName() + " Vlan: " + n.getVlan(), 1 );

								com.getNet().setVisNettel(n);
								com.getNet().refreshNettel();
								return;
							}
						} else
						if (button2 && n.getIsClickable() && (n.getKat().equals("gw") || n.getKat().equals("sw")) )
						{ // høyre-klikk på nettel/link
							n.disablePopup();
							boolean router = true;
							if (n.getKat().equals("sw"))
							{
								router = false;
							}

							if (n.containsNettel(x, y))
							{ // høyre-klikket på nettel
								PopupMenus activeMenu;
								if (n.getKat().equals("gw"))
								{
									activeMenu = com.getGwMenu();
								} else
								{
									activeMenu = com.getSwMenu();
								}

								activeMenu.setNettelName(n.getName() );
								activeMenu.setIfName("" );
								activeMenu.setIsRouter(router);
								com.setActiveMenu(activeMenu );

								activeMenu.show(com.getNet(), x, y);

							} else
							{ // høyre-klikket på link
								Link l = n.getLink(x, y);
								PopupMenus activeMenu;
								if (n.getKat().equals("gw"))
								{
									activeMenu = com.getLinkGwMenu();
								} else
								{
									activeMenu = com.getLinkMenu();
								}

								activeMenu.setNettelName(n.getName() );
								activeMenu.setIfName(l.getIfName() );
								activeMenu.setIsRouter(router);
								activeMenu.setCapacity(l.getCapacity());
								//if (n.getKat().equals("gw")) activeMenu.setIpRom(l.getIpRomV());
								com.setActiveMenu(activeMenu );

								activeMenu.show(com.getNet(), x, y);

							}

						}
					}

				} // while

				if (!overNettel && button2) {
					com.d("  Show vlanMenu", 4);
					// Høyreklikk, da viser vi vlan-menyen hvis vi er på vlan-vandring
					if (com.getNet().getVlanVandring()) com.getNet().showVlanPopupMenu(x, y);
				}

			} // !overNet

		}

	}

	public void mouseEntered(MouseEvent e)
	{
		if (e.getSource() == com.getNet()) {
			overNet = true;
		} else if (e.getSource() == com.getLogo()) {
			overLogo = true;
		}
	}

	public void mouseExited(MouseEvent e)
	{
		if (e.getSource() == com.getNet()) {
			overNet = false;
		} else if (e.getSource() == com.getLogo()) {
			overLogo = false;
		}
	}

	public void mousePressed(MouseEvent e)
	{
		if ((e.getModifiers() & InputEvent.BUTTON1_MASK) != 0)
		{
			button1 = true;
		}
		if ( ((e.getModifiers() & InputEvent.BUTTON2_MASK) != 0) || ((e.getModifiers() & InputEvent.BUTTON3_MASK) != 0) )
		{
			button2 = true;
		}
		if ( ((e.getModifiers() & InputEvent.ALT_GRAPH_MASK) != 0) || (e.getClickCount() >= 3) )
		{
			meta = true;
			com.d("Trippel-click!", 1);
		}

		com.d("Buttons pressed: b1: " + button1 + " b2: " + button2 + " meta: " + meta + " Clicks: " + e.getClickCount(), 2);

		if (overNet)
		{
			//if (com.getAdmin().getMoveNettel() && button1)
			if (com.getAdmin().getMoveMode() )
			{
				{ // sjekk om noen av nettel-boxene er klikket
					Enumeration enu = com.getNet().getNettelHash().elements();

					int x = com.getMouseX();
					int y = com.getMouseY();

					//for (int i = v.size()-1; i >= 0; i--)
					while (enu.hasMoreElements())
					{
						//Nettel n = (Nettel)v.elementAt(i);
						Nettel n = (Nettel)enu.nextElement();

						if (n.boksContains(x, y))
						{
							n.setClicked(true);
							com.setClicked(n.getBoksid());
							com.d("Klikket Nettel: " + n.getName() + ", id: " + n.getBoksid(), 3);
							return;
						}
					}
				}

				{ // sjekk om noen av gruppene er klikket
					Vector v = com.getNet().getGrp();

					int x = com.getMouseX();
					int y = com.getMouseY();

					for (int i = v.size()-1; i >= 0; i--)
					{
						Grp grp = (Grp)v.elementAt(i);

						if (grp.contains(x, y))
						{
							grp.setClicked(true);
							com.setClickedGrp(i);
							//System.out.println("Clicked: " + i);
							return;
						}
					}
				}

			}
		} 
		/*
		else
		if (overLogo)
		{
			if (button1 && button2 || meta )
			{
				meta = false;
				// har brukeren tilgang til admin?
				if (com.getAdmin().getHasAdmin()) {
					com.d("Aktiverer admin-meny", 1);

					AdminPanel ap = com.getAdminPanel();
					ap.showMenu();
				}
			}
		}
		*/

	}

	public void mouseReleased(MouseEvent e)
	{
//		if ((e.getModifiers() & InputEvent.BUTTON1_MASK) != 0)
		{
			button1 = false;
		}
//		if ( ((e.getModifiers() & InputEvent.BUTTON2_MASK) != 0) || ((e.getModifiers() & InputEvent.BUTTON3_MASK) != 0) )
		{
			button2 = false;
		}
		if ( ((e.getModifiers() & InputEvent.SHIFT_MASK) != 0) || (e.getClickCount() < 3) )
		{
			meta = false;
		}

		com.d("Buttons released: b1: " + button1 + " b2: " + button2 + " meta: " + meta + " Clicks: " + e.getClickCount(), 2);



		if (com.getClicked() != 0)
		{
			//Vector v = com.getNet().getNettel();
			//Nettel n = (Nettel)v.elementAt(com.getClicked() );
			Nettel n = (Nettel)com.getNet().getNettelHash().get(""+com.getClicked());
			com.d("Unklikket Nettel: " + n.getName(), 3);
			n.setClicked(false);
			com.setClicked(0);
		}
		if (com.getClickedGrp() >= 0)
		{
			Vector v = com.getNet().getGrp();
			Grp grp = (Grp)v.elementAt(com.getClickedGrp() );
			grp.setClicked(false);
			com.setClickedGrp(-1);
		}


	}


}



class MouseMove implements MouseMotionListener
{
	Com com;
	boolean overBox = false;
	Nettel overBoxNettel;

	public MouseMove(Com InCom)
	{
		com = InCom;
	}

	public void mouseDragged(MouseEvent e)
	{
		com.d("Mouse dragged to: X: " + e.getX() + " Y: " + e.getY(), 7);
		if (com.getClicked() != 0)
		{
			//Vector v = com.getNet().getNettel();
			//Nettel n = (Nettel)v.elementAt(com.getClicked() );
			Nettel n = (Nettel)com.getNet().getNettelHash().get(""+com.getClicked());

			n.setMove(e.getX(), e.getY() );

		} else if (com.getClickedGrp() != -1) {
			Vector v = com.getNet().getGrp();
			Grp grp = (Grp)v.elementAt(com.getClickedGrp() );

			grp.setMove(e.getX(), e.getY() );

		}
	}

	public void mouseMoved(MouseEvent e)
	{
		com.setMouseX(e.getX() );
		com.setMouseY(e.getY() );

		//if (com.getMouse().isOverNettel() )
		// Vi ønsker ikke å si ifra at muspekeren har beveget på seg når vi er i move-mode
		if (!com.getAdmin().getMoveMode())
		{

			if (overBox)
			{
				if (!overBoxNettel.contains(e.getX(), e.getY() ))
				{
					com.d("Beveget ut fra: " + overBoxNettel.getName() + " Vlan: " + overBoxNettel.getVlan(), 8 );
					overBoxNettel.setMouseOver(false, e.getX(), e.getY() );
					//com.getNet().repaint();
					overBox = false;
				} else
				{
					overBoxNettel.setMouseOver(true, e.getX(), e.getY() );
				}
			}
			if (!overBox)
			{
				Enumeration enu = com.getNet().getNettelHash().elements();

				int x = e.getX(); //int x = com.getMouseX();
				int y = e.getY(); //int y = com.getMouseY();

				//System.out.println("x: " + com.getMouseX() + " x2: " + e.getX() );

				//for (int i = v.size()-1; i >= 0; i--)
				while (enu.hasMoreElements())
				{
					//Nettel n = (Nettel)v.elementAt(i);
					Nettel n = (Nettel)enu.nextElement();

					if (n.contains(x, y))
					{
						overBox = true;
						overBoxNettel = n;
						n.setMouseOver(true, x, y);
						com.d("Beveget over: " + n.getName() + " Vlan: " + n.getVlan(), 8 );
						break;
						//com.getNet().setVisNettel(n.getId() );
						//com.getNet().setVisNettel(n);
						//com.getNet().repaint();
						//return;
					}
				}
			}

		}




	}

}

class PopupMenuListener implements ActionListener
{
	Com com;
	//private final String SERVER_URL = "http://bigbud.itea.ntnu.no";
	//private final String SERVER_URL = "http://la.itea.ntnu.no";

    //private final String CRICKETURL = SERVER_URL+"/~cricket/"; // husk avsluttende slash
    //private final String CGIBINURL  = SERVER_URL+"/public/perl/";
    //private final String NETFLOW_URL = "http://manwe.itea.ntnu.no/";

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

		/*
		Menu m = (Menu)mi.getParent();
		if (m instanceof PopupMenus) {
			PopupMenus pm = (PopupMenus)m;
			if (pm.getMenuType() == PopupMenus.VLAN_MENU) {
				procVlan(e);
			}
			*/
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
		String nettelName = activeMenu.getNettelName();
		String ifName = activeMenu.getIfName();
		String ifPrefix = (activeMenu.getCapacity() >= 1000.0) ? "giga-" : "";
		String cricketUrl = "";

		// Litt formatering av ifName er nødvendig
		ifName = ifName.toLowerCase();

		String kommando = e.getActionCommand();
		if (kommando.equals(com.getNet().linkMenuText[0] ))
		{ // Last
			kommando = "Octets";
		} else
		if (kommando.equals(com.getNet().linkMenuText[1] ))
		{ // Pakker
			kommando = "Packets";
		} else
		if(kommando.equals(com.getNet().linkMenuText[2] ))
		{ // Dropp
			kommando = "Drops";
		} else
		if(kommando.equals(com.getNet().linkMenuText[3] ))
		{ // Feil
			kommando = "Errors";
		} else
		if(kommando.equals(com.getNet().gwMenuText[0] ))
		{ // CPU Last
			kommando = "cpu";
		} else
		if(kommando.equals(com.getNet().gwMenuText[1] ))
		{ // Nettliste
			//String gwName = com.getGwMenu().getNettelName();
			//showURL(CGIBINURL+"nettliste.pl?gw=" + nettelName);
			return;
		} else
		if(kommando.equals(com.getNet().swMenuText[0] ))
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
				cricketUrl = "index.cgi?target=%2F"+ifPrefix+"router-interfaces%2F" + nettelName + "%2F" + ifName.replace('/','_') + "&ranges=d%3Aw&view=" + kommando;
			} else
			{
				cricketUrl = "index.cgi?target=%2F"+ifPrefix+"switch-ports%2F" + nettelName + "%2F" + ifName + "&ranges=d%3Aw&view=" + kommando;
			}
		}

		showURL(Input.cricketURL + cricketUrl);

/*
		String kommando = e.getActionCommand();
		if (kommando.equals(com.getNet().linkMenuText[0] ))
		{ // Last
			String nettelName = com.getLinkMenu().getNettelName();
			String ifName = com.getLinkMenu().getIfName();
	    	TilURL(CRICKETURL+"index.cgi?target=%2Frouter-interfaces%2F" + nettelName + "%2F" + ifName + "&ranges=d%3Aw&view=Octets");

		} else
		if (kommando.equals(com.getNet().linkMenuText[1] ))
		{ // Pakker
			String nettelName = com.getLinkMenu().getNettelName();
			String ifName = com.getLinkMenu().getIfName();
	    	TilURL(CRICKETURL+"index.cgi?target=%2Frouter-interfaces%2F" + nettelName + "%2F" + ifName + "&ranges=d%3Aw&view=Packets");

		} else
		if(kommando.equals(com.getNet().linkMenuText[2] ))
		{ // Dropp
			String nettelName = com.getLinkMenu().getNettelName();
			String ifName = com.getLinkMenu().getIfName();
	    	TilURL(CRICKETURL+"index.cgi?target=%2Frouter-interfaces%2F" + nettelName + "%2F" + ifName + "&ranges=d%3Aw&view=Drops");

		} else
		if(kommando.equals(com.getNet().linkMenuText[3] ))
		{ // Feil
			String nettelName = com.getLinkMenu().getNettelName();
			String ifName = com.getLinkMenu().getIfName();
	    	TilURL(CRICKETURL+"index.cgi?target=%2Frouter-interfaces%2F" + nettelName + "%2F" + ifName + "&ranges=d%3Aw&view=Errors");

		} else
		if(kommando.equals(com.getNet().nettelMenuText[0] ))
		{ // CPU Last
			String nettelName = com.getNettelMenu().getNettelName();
	    	TilURL(CRICKETURL+"index.cgi?target=%2Frouters%2F" + nettelName + "&ranges=d%3Aw&view=cpu");

		} else
		if(kommando.equals(com.getNet().nettelMenuText[1] ))
		{ // Nettliste
			String nettelName = com.getNettelMenu().getNettelName();
			TilURL(CGIBINURL+"nettliste.pl?gw=" + nettelName);
		}
*/
    }

	private void procNetflow(ActionEvent e)
	{
		PopupMenus activeMenu = com.getActiveMenu();
		/*
		String nettelName = activeMenu.getNettelName();
		String ifName = activeMenu.getIfName();
		*/
		String netflowUrl = "";
		String ip = e.getActionCommand();

		// bytt ut slash i ip
		{
			final String slash = "%2F";
			int index = ip.indexOf("/");
			ip = ip.substring(0, index) + slash + ip.substring(index+1, ip.length());
		}

		//Vector ipRom = activeMenu.getIpRom();

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

	    //report.html?router=All&ip=129.241.103.1%2F24&list=10&from=20010109&to=20010109
	    //report2.html?router=All&ip=129.241.103.1%2F24&list=10&from=5&to=2355

		showURL(Input.netflowURL + netflowUrl);
	}

	public void showURL(String url)
	{
		com.showURL(url);
	}



}


class NetComponentListener extends ComponentAdapter
{
	Net net;
	public NetComponentListener(Net net)
	{
		this.net = net;
	}

	public void componentResized(ComponentEvent e)
	{
		net.refreshNettel();

		//for (int i=0;i<5;i++) System.err.println("****!!!!!!!!!Component shown!!!!!!!!********");
	}
}








