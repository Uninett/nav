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

import java.awt.event.InputEvent;
import java.awt.event.MouseEvent;
import java.awt.event.MouseListener;
import java.util.Enumeration;
import java.util.Vector;

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

				boolean overNettel = false;
				while (enu.hasMoreElements())
				{
					Nettel n = (Nettel)enu.nextElement();

					if (n.contains(x, y))
					{
						overNettel = true;
						com.d("Klikket: " + n.getName(),3);
						boolean router = !n.getClickKat().equals("sw");

						if (button1)
						{ // venstre-klikk på nettel/link
							if (n.getIsClickable() )
							{
								n.disablePopup();
								if (router) n.setVlan(0);

								com.d("------------------------------------------------------------------------", 1);
								com.d("Aktivert klikk: " + n.getName() + " Vlan: " + n.getVlan() + " Kat: " + n.getKat() +" Router: " + router, 1 );

								com.getNet().setVisNettel(n);
								com.getNet().refreshNettel();
								return;
							}
						} else
						if (button2 && n.getIsClickable() && (n.getKat().equals("gw") || n.getKat().equals("gsw") || n.getKat().equals("sw")) )
						{ // høyre-klikk på nettel/link
							n.disablePopup();

							if (n.containsNettel(x, y))
							{ // høyre-klikket på nettel
								PopupMenus activeMenu;
								com.d("  Right-click on nettel: " + n.getName() + " Vlan: " + n.getVlan(), 1 );
								if (router) {
									activeMenu = com.getGwMenu();
								} else {
									activeMenu = com.getSwMenu();
								}

								activeMenu.setNettelName(n.getName() );
								activeMenu.setFullNettelName(n.getFullName() );
								activeMenu.setIfName("" );
								activeMenu.setIsRouter(router);
								com.setActiveMenu(activeMenu );

								activeMenu.show(com.getNet(), x, y);

							} else
							{ // høyre-klikket på link
								Link l = n.getLink(x, y);
								PopupMenus activeMenu;
								if (router)
								{
									activeMenu = com.getLinkGwMenu();
								} else
								{
									activeMenu = com.getLinkMenu();
								}

								activeMenu.setNettelName(n.getName() );
								activeMenu.setFullNettelName(n.getFullName() );
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
			if (com.getAdmin().getMoveMode() )
			{
				{ // sjekk om noen av nettel-boxene er klikket
					Enumeration enu = com.getNet().getNettelHash().elements();

					int x = com.getMouseX();
					int y = com.getMouseY();

					while (enu.hasMoreElements())
					{
						Nettel n = (Nettel)enu.nextElement();

						if (n.boksContains(x, y))
						{
							n.setClicked(true);
							com.setClicked(n.getBoksid());
							com.d("Admin klikket Nettel: " + n.getName() + ", id: " + n.getBoksid(), 3);
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
							com.d("Admin klikket Grp: " + grp.getName() + ", id: " + grp.getGrpid(), 3);
							return;
						}
					}
				}

			}
		} 
	}

	public void mouseReleased(MouseEvent e)
	{
		button1 = false;
		button2 = false;
		if ( ((e.getModifiers() & InputEvent.SHIFT_MASK) != 0) || (e.getClickCount() < 3) )
		{
			meta = false;
		}

		com.d("Buttons released: b1: " + button1 + " b2: " + button2 + " meta: " + meta + " Clicks: " + e.getClickCount(), 2);



		if (com.getClicked() != 0)
		{
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
