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

import java.awt.Canvas;
import java.awt.Graphics;
import java.awt.Image;
import java.awt.Rectangle;
import java.awt.Toolkit;
import java.awt.image.ImageObserver;
import java.util.Stack;

class NettelIcon implements ImageObserver
{
	Com com;

	String imageName;
	static final String DIR_PREFIX = "icons/";

	private int x;
	private int y;
	private int sizeX;
	private int sizeY;

	Image icon;
	Nettel parent;

	private static Stack updateQ = new Stack();

	public NettelIcon(Com com, String kat, Nettel parent)
	{
		this.com = com;
		this.imageName = kat+".gif";
		this.parent = parent;

		// Hent ikonet
		if (com.getApplet() != null) {
			com.d("Icon URL: " + com.getApplet().getDocumentBase() + ", ImageName: " + imageName,2);
			icon = com.getApplet().getImage(com.getApplet().getDocumentBase(),DIR_PREFIX+imageName);
		} else {
			icon = Toolkit.getDefaultToolkit().getImage(DIR_PREFIX+imageName);
		}
		synchronized (updateQ) {
			if (updateQ.isEmpty()) {
				sizeX = icon.getWidth(this);
				sizeY = icon.getHeight(this);
			} else {
				updateQ.push(this);
			}
		}
	}

	public boolean imageUpdate(Image img, int infoflags, int x, int y, int width, int height)
	{
		if ( (infoflags & ImageObserver.WIDTH) != 0) {
			sizeX = width;
		}

		if ( (infoflags & ImageObserver.HEIGHT) != 0) {
			sizeY = height;
		}

		if (sizeX != -1 && sizeY != -1 && parent != null) parent.recalcLink();

		boolean needMoreUpdates = (sizeX == -1 || sizeY == -1);

		if (!needMoreUpdates) {
			synchronized (updateQ) {
				while (!updateQ.empty()) {
					NettelIcon ni = (NettelIcon)updateQ.pop();
					if (ni.updateDim()) break;
				}
			}
		}
		return needMoreUpdates;
	}

	private boolean updateDim() {
		sizeX = icon.getWidth(this);
		sizeY = icon.getHeight(this);
		boolean needMoreUpdates = (sizeX == -1 || sizeY == -1);
		return needMoreUpdates;		
	}

			   

	public void setX(int x) { this.x = x; }
	public void setY(int y) { this.y = y; }
	public void setXY(int x, int y) { setX(x); setY(y); }


	public int getSizeX() { return sizeX; }
	public int getSizeY() { return sizeY; }

	public void drawSelf(Graphics g, Canvas c)
	{
		if (x < 10 || y < 10) com.d("Error ("+x+","+y+")",1);
		g.drawImage(icon, x, y, c);
	}

	public boolean contains(int x, int y)
	{
		Rectangle r = new Rectangle(this.x, this.y, sizeX, sizeY);
		return r.contains(x, y);
	}
}




















