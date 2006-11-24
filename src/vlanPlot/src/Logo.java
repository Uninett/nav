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

import java.awt.Color;
import java.awt.Graphics;
import java.awt.Image;
import java.awt.Canvas;

class Logo extends Canvas
{
	/**
	 * 
	 */
	private static final long serialVersionUID = 1L;
	Com com;
	Image navLogo;
	static final String DIR_PREFIX = "gfx/";

	public Logo(Com InCom)
	{
		com = InCom;

		Mouse mouse = new Mouse(com);
		MouseMove mv = new MouseMove(com);
		addMouseListener(mouse);
		addMouseMotionListener(mv);
		setSize(100, 232);


	}

	public void paint(Graphics g)
	{

		// Linjer
		{
			int xstart = 20;
			int ystart = 8;

		    // Tykkelse på linjer
		    g.setColor(Color.black);
		    g.fillRect(xstart,ystart,30,3);
		    g.fillRect(xstart,ystart+9,30,5);
		    g.fillRect(xstart,ystart+20,30,8);

			// tekst
			g.drawString("<10Mb", xstart+35, ystart+7);
			g.drawString("<100Mb", xstart+35, ystart+17);
			g.drawString("<1Gb", xstart+35, ystart+28);
		}

	    // Fargeskala
	    int xstart = 10;
	    int ystart = 52;
	    int boxSizeX = 15;
	    int boxSizeY = 15;
	    int spaceX = 5;

	    for (int i = LastColor.getAntTrinn()-1; i >= 0; i--)
	    {
		    g.setColor(LastColor.getColorTrinn(i) );
		    g.fillRect(xstart,ystart,boxSizeX,boxSizeY);

		    g.setColor(Color.black);
		    g.drawRect(xstart,ystart,boxSizeX,boxSizeY);

		    g.drawString(LastColor.getStringTrinn(i) ,xstart+boxSizeX+spaceX, ystart+10);

			ystart += boxSizeY;
		}


	}
}

