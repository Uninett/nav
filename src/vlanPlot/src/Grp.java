/*
 * NTNU ITEA Nettnu prosjekt
 *
 * Skrvet av: Kristian Eide
 *
 */

import java.util.*;

import java.awt.*;
import java.awt.event.*;


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
	int distX, distY;
	int id;




	public Grp(Com InCom, int inId)
	{
		com = InCom;
		id = inId;
	}

	public void setName(String s) { name = s; }

	public void drawSelf(Graphics g)
	{
		//g.setColor(Color.black);
		//g.drawOval(x+1, y+1, r*2-1, r*2-1);
		g.setColor(bg);
		g.fillOval(x, y, r*2, r*2);

	}

	public void addMember(Nettel n)
	{
		members.addElement(n);
		r = rMedlem * members.size();

	}

	public int getId() { return id; }
	public int getX() { return x; }
	public int getY() { return y; }

	public void setXY(int inX, int inY)
	{
		x = inX;
		y = inY;
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
		Polygon p = new Polygon();

		p.addPoint(x, y);
		p.addPoint(x+r*2, y);
		p.addPoint(x+r*2, y+r*2);
		p.addPoint(x, y+r*2);

		return p.contains(conX, conY);


	}







}































