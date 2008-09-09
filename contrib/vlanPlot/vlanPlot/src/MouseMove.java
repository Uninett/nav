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

import java.awt.event.MouseEvent;
import java.awt.event.MouseMotionListener;
import java.util.Enumeration;
import java.util.Vector;


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

				int x = e.getX();
				int y = e.getY();

				while (enu.hasMoreElements())
				{
					Nettel n = (Nettel)enu.nextElement();

					if (n.contains(x, y))
					{
						overBox = true;
						overBoxNettel = n;
						n.setMouseOver(true, x, y);
						com.d("Beveget over: " + n.getName() + " Vlan: " + n.getVlan(), 8 );
						break;
					}
				}
			}

		}




	}

}