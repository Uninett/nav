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
import java.awt.Polygon;
import java.util.Vector;


class Grp
{
	// sirkel radius pr. medlem
	int rMedlem = 12;

	Color bg = Color.gray;


	Com com;
	Vector members = new Vector();

	String name;
	boolean setMove = false;

	int r = 0;
	int x, y;
	boolean hideicons;
	Nettel icon;
	int distX, distY;
	int id;




	public Grp(Com InCom, int inId, boolean hideicons)
	{
		com = InCom;
		id = inId;
		this.hideicons = hideicons;
	}

	public void setIconName(String iconname) {
		if (hideicons && iconname != null && iconname.length() > 0 && !"null".equals(iconname)) {
			icon = new Nettel(com, 0, name, iconname, "0", 0);
		}
	}

	public void setName(String s) { name = s; }
	public String getName() { return name; }
	
	public int getGrpid() { return id; }

	public boolean getHideicons() { return hideicons; }

	public void drawSelf(Graphics g)
	{
		if (!hideicons) {
			g.setColor(bg);
			g.fillOval(x, y, r*2, r*2);
		} else {
			icon.drawSelf(g, 2);
			icon.drawSelf(g, 3);
			icon.drawSelf(g, 4);
			icon.drawSelf(g, 5);
		}

	}

	public void addMember(Nettel n)
	{
		members.addElement(n);
		if (!hideicons) {
			r = rMedlem * members.size();
		} else {
			n.setXY(x, y);
			n.setIconVisible(false);
		}
	}

	public void autoLayout() {
		if (hideicons) return;
		double v = Math.PI*2;
		double inc = Math.PI*2 / members.size();
		// cos(v) = hosligende
		// sin(v) = motstående
		com.d("Grp pos at: ("+x+","+y+",r="+r+")",3);
		for (int i=0; i < members.size(); i++) {
			Nettel n = (Nettel)members.elementAt(i);
			if (!n.getLocationSet()) continue;

			double dx = Math.cos(v - inc*i);
			double dy = Math.sin(v - inc*i);
			if (Math.abs(dx) < 0.00001) dx = 0;
			if (Math.abs(dy) < 0.00001) dy = 0;
			int nx = x + (int)(dx * r) + r - 10;
			int ny = y + (int)(dy * r) + r - 12;
			n.setXY(nx, ny);
			com.d("Pos " + n + " at: ("+dx+","+dy+") ("+nx+","+ny+")",3);
		}
	}

	public int getId() { return id; }
	public int getX() { return x; }
	public int getY() { return y; }

	public void setXY(int inX, int inY)
	{
		x = inX;
		y = inY;
		if (hideicons) {
			if (icon == null) setIconName("default_grp_icon");
			icon.setXY(x, y);
		}
	}

	public void setClicked(boolean b)
	{
		setMove = b;
	}

	public void setMove(int toX, int toY)
	{
		if (setMove)
		{
			distX = toX - x;
			distY = toY - y;
			setMove = false;
		}

		int moveX = toX - x - distX;
		int moveY = toY - y - distY;

		// flytt alle medlemmer av gruppen samme distanse og retning
		for (int i = 0; i < members.size(); i++)
		{
			Nettel n = (Nettel)members.elementAt(i);
			int oldX = n.getX();
			int oldY = n.getY();

			n.resetLast();
			n.setMove(oldX+moveX, oldY+moveY, false);

		}

		int x = toX-distX;
		int y = toY-distY;

		setXY(x, y);
		com.getNet().repaint();

	}

	public boolean contains(int conX, int conY)
	{
		if (hideicons) {
			return icon.contains(conX, conY);
		} else {
			Polygon p = new Polygon();

			p.addPoint(x, y);
			p.addPoint(x+r*2, y);
			p.addPoint(x+r*2, y+r*2);
			p.addPoint(x, y+r*2);

			return p.contains(conX, conY);
		}
	}







}































