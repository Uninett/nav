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
import java.awt.Color;
import java.awt.Font;
import java.awt.FontMetrics;
import java.awt.Graphics;
import java.awt.Polygon;
import java.util.Vector;

class PopupMessage
{
	// BEgin configurasjon
	final int spaceX = 3; // mellomrom på hver side
	final int spaceY = 3; // mellomrom fra toppen og bunnen
	// End configuration

	Font font;
	Vector message = new Vector();
	Canvas notify;
	Polygon p = new Polygon();

	int x = 0,y = 0, sizeX, sizeY, height;
	int beginY, stepY;
	boolean calcDimension = false;
	boolean calcXY = false;
	boolean isVisible = false;

	public PopupMessage(Canvas InNotify, Font InFont)
	{
		font = InFont;
		notify = InNotify;
	}

	public void addMessage(String s)
	{
		if (s != null)
		{
			// masse kode for å behandle \n (linjeskift) rett
			int index = 0;
			index = s.indexOf("\n");

			while (index != -1)
			{
				message.addElement(s.substring(0, index) );
				s = s.substring(index+1, s.length() );
				index = s.indexOf("\n");
			}

			message.addElement(s);
			calcDimension = false;
		}
	}

	public void removeMessage(int n)
	{
		message.removeElementAt(n);
		calcDimension = false;
	}

	public void replaceMessage(String s, int n)
	{
		if (s != null)
		{
			message.setElementAt(s, n);
			calcDimension = false;
		}
	}

	public String getMessage()
	{
		StringBuffer sb = new StringBuffer();
		for (int i=0; i < message.size(); i++) {
			String s = (String)message.elementAt(i);
			sb.append(s);
			if (i != message.size()-1) sb.append("\n");
		}
		return sb.toString();
	}

	public int getX() { return x; }
	public int getY() { return y; }

	private void calcDimension(Graphics g)
	{
		g.setFont(font);
		FontMetrics fontMetrics = g.getFontMetrics(font);

		// bestem høyde/bredde
		int height = fontMetrics.getHeight()*message.size();
		//int fontWidth = fontMetrics.stringWidth((String)message.elementAt(0) );
		int fontWidth=0;
		for (int i = 0; i < message.size(); i++) {
			int stringWidth;
			if ( (stringWidth=fontMetrics.stringWidth((String)message.elementAt(i))) > fontWidth) {
				//fontWidth = fontMetrics.stringWidth((String)message.elementAt(i) );
				fontWidth = stringWidth;
			}
		}

		sizeX = spaceX + fontWidth + spaceX;
		//sizeY = spaceY + height + spaceY;
		sizeY = height + spaceY;

		this.height = fontMetrics.getHeight();

		calcDimension = true;

	}

	private void calcXY()
	{
		int canvasX = notify.getMinimumSize().width;
		//int canvasY = notify.getMinimumSize().height;

		if (x+sizeX > canvasX) {
			x -= (x+sizeX-canvasX+1);
		}

		if (y-sizeY < 0) {
			y += (sizeY+22);
		}

		p = new Polygon();
		p.addPoint(x, y-sizeY);
		p.addPoint(x+sizeX, y-sizeY);
		p.addPoint(x+sizeX, y);
		p.addPoint(x, y);

		beginY = y-sizeY+height;
		stepY = height;

		calcXY = true;
	}

	public void show(int InX, int InY, Graphics g)
	{
		hide();

		if (x == InX && y == InY) {
			calcXY = true;
		} else {
			x = InX;
			y = InY;
			calcXY = false;
		}

		if (!calcDimension) {
			calcDimension(g);
		}
		if (!calcXY) {
			calcXY();
		}

		isVisible = true;
		notify.repaint(x, y-sizeY, sizeX+1, sizeY+1);
	}

	public void hide()
	{
		if (isVisible) {
			isVisible = false;
			notify.repaint(x, y-sizeY, sizeX+1, sizeY+1);
		}
	}

	public void drawSelf(Graphics g)
	{
		if (!isVisible) return;

		g.setFont(font);
		g.setColor(new Color(255, 255, 225) );
		g.fillPolygon(p);
		g.setColor(Color.black);
		g.drawPolygon(p);

		for (int i = 0; i < message.size(); i++) {
			g.drawString((String)message.elementAt(i), x+spaceX, beginY+stepY*i);
		}
	}
}



