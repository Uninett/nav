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
import java.awt.Dimension;
import java.awt.Font;
import java.awt.FontMetrics;
import java.awt.Graphics;
import java.awt.Polygon;
import java.awt.Rectangle;
import java.util.Hashtable;
import java.util.Vector;


class Nettel
{
	// konfigurasjons-variabler
	public static int sizeX = 45;
	public static int sizeY = 50;
	public static int FONT_SIZE = 9;
	public static int POPUP_FONT_SIZE = 13;
	Font nf = new Font("Helvetica",Font.PLAIN, FONT_SIZE);
	public static Font popupFont = new Font("Arial",Font.PLAIN, POPUP_FONT_SIZE);

	private static int canvasTopSpaceY = 25; // plass til overskrift

	private static int topSpace = 0;
	private static int leftSpace = 3;
	private static int rightSpace = 2;
	private static int bottomSpace = 10;

	public static int vlanBoxSizeX = 24;
	public static int vlanBoxSizeY = 12;

	public static int lastBoxDivider = 4;
	public static int lastBoxSpaceX = 4;
	public static int lastBoxSpaceY = 2;


	// statiske variabler
	Com com;
	Graphics graph;
	boolean isGraphSet = false;

	NettelIcon nettelIcon;

	String name;
	String fullName;
	String kat;
	int boksid;
	int vlan;

	String hashKey;

	int clickId;
	String clickKat;

	boolean groupMember = false;
	boolean isClickable = false;
	int group = 0;

	Vector linkNettel = new Vector();
	Vector link = new Vector();

	// Hver boks har sin egen PopupMessage
	Hashtable keywords = new Hashtable();
	PopupMessage desc;
	String descText;
	boolean popupUpToDate = false;

	int descSizeX, descSizeY; // størrelse på

	Polygon nettel; 	// selve boxen
	Polygon nettelLast; // last på boxen


	// state-variabler for objektet
	boolean isVisible = true;
	boolean iconVisible = true;
	boolean click = false;
	boolean setMove = false;
	boolean setSelected = false;

	boolean mouseOver = false;
	boolean threadCreated = false;
	boolean drawPopup = false;
	//boolean drawVlan = true;
	boolean drawVlan = false;
	int mouseOverX;
	int mouseOverY;

	int mouseOverLink;
	NettelAction nc = null;

	int x = 0,y = 25; // koordinater, y settes lik 25 som default så den kommer under knappene på toppen
	int lastX = 0, lastY = 0;
	boolean locationSet = false;

	// stats
	double nettelLastPst = -1.0;

	public Nettel(Com com, int boksid, String name, String kat, String InNum, int vlan)
	{
		this.com = com;
		setBoksid(boksid);
		setName(name);
		setKat(kat);
		this.vlan = vlan;

		if (kat.equals("gw") || kat.equals("gsw") || kat.equals("sw") || kat.equals("edge") ) isClickable = true;
	}

	private void setBoksid(int i)
	{
		boksid = i;
		keywords.put("boksid".toLowerCase(), String.valueOf(boksid));
	}
	public int getBoksid() { return boksid; }
	public String getBoksidS() { return String.valueOf(boksid); }

	public int getClickId() { return clickId; }
	public void setClickId(int i) { clickId = i; }
	public String getClickKat() { return clickKat != null ? clickKat : getKat(); }
	public void setClickKat(String s) { clickKat = s; }

	public boolean isCore() {
		return boksid < 0;
	}

	public void setName(String s)
	{
		fullName = s;
		name = s;
		int k;
		while ((k=name.indexOf(Net.domainSuffix)) >= 0) {
			name = name.substring(0, k) + name.substring(k+Net.domainSuffix.length(), name.length());
		}

		keywords.put("sysname".toLowerCase(), name);
	}
	public String getName() { return name; }
	public String getFullName() { return fullName; }
	public String getShowName() { return name; }

	public void setKat(String s)
	{		
		if (kat == null || !kat.equals(s)) {
			kat = s;
			com.d("Nettel.setKat(): Creating new nettelIcon for nettel: " + getName() + " Kat: " + kat, 5);
			nettelIcon = new NettelIcon(com, kat, this);
			nettelIcon.setXY(x, y);
		}
	}
	public String getKat() { return kat; }

	public int getVlan() { return vlan; }
	public void setVlan(int i) { vlan = i; }

	public Font getFont()	{ return nf; }

	public boolean getGroupMember() { return groupMember; }
	public void setGroupMember(boolean InGroupMember) { groupMember = InGroupMember; }
	public int getGroup() { return group; }
	public void setGroup(int InGroup) { group = InGroup; }

	public void setNettelLast(double InNettelLast)
	{
		nettelLastPst = InNettelLast;
		keywords.put("boksLast".toLowerCase(), String.valueOf(nettelLastPst)+"%");
	}

	public void setIsClickable(boolean InIsClickable) { isClickable = InIsClickable; }
	public boolean getIsClickable() { return isClickable; }


	public int compareTo(Object o)
	{
		Nettel n = (Nettel)o;
		if (vlan < n.getVlan()) return -1;
		if (vlan > n.getVlan()) return 1;
		return 0;
	}

	public void drawSelf(Graphics g, int pass)
	{
		if (!isVisible) return;

		if (!isGraphSet)
		{
			graph = g;
			isGraphSet = true;
		}

		if (pass == 1)
		{
			// tegn alle linjer
			for (int i = 0; i < link.size(); i++)
			{
				Link l = (Link)link.elementAt(i);
				l.drawSelf(g);
			}
		} else
		if (pass == 2)
		{
			// Tegn selve iconet for nettel-boksen
			if (iconVisible) {
				nettelIcon.drawSelf(g, com.getNet() );
			}

		} else
		if (pass == 3 && iconVisible)
		{
			// Navn-tegning er felles for alle enheter
			int spaceX = 2;
			int spaceY = 4;

			// ikke skriv navn for FDDI-ringen
			if (name.equalsIgnoreCase("fddi")) return;

			g.setFont(nf);
			FontMetrics fontMetrics = g.getFontMetrics(nf);

			String text = getShowName();
			int fontWidth = fontMetrics.stringWidth(text);

			Polygon p = new Polygon();
				p.addPoint(x+nettelIcon.getSizeX()/2-fontWidth/2-spaceX, y+nettelIcon.getSizeY() );
				p.addPoint(x+nettelIcon.getSizeX()/2+fontWidth/2+spaceX, y+nettelIcon.getSizeY() );

				p.addPoint(x+nettelIcon.getSizeX()/2+fontWidth/2+spaceX, y+nettelIcon.getSizeY()+fontMetrics.getHeight()/2+spaceY );
				p.addPoint(x+nettelIcon.getSizeX()/2-fontWidth/2-spaceX, y+nettelIcon.getSizeY()+fontMetrics.getHeight()/2+spaceY );

			g.setColor(new Color(255, 255, 225) );
			g.fillPolygon(p);

			if (nettelLastPst > 0) {
				// Nettel-bokser skal alltid farges relativt
				LastColor.setTmpSkala(LastColor.RELATIV_SKALA);
				g.setColor(LastColor.getColor(nettelLastPst) );
				LastColor.unsetTmpSkala();

				g.drawPolygon(p);
				p.translate(-1, 0);
				g.drawPolygon(p);
				p.translate(1, -1);
				g.drawPolygon(p);
			} else {
				g.setColor(Color.black);
				g.drawPolygon(p);
			}

			g.setColor(Color.black);
			g.drawString(text, x+nettelIcon.getSizeX()/2-fontWidth/2, y+nettelIcon.getSizeY()+fontMetrics.getHeight()-fontMetrics.getHeight()/2+spaceY/2 );


		} else if (pass == 4) {
			// kalkuler og tegn alle vlan til andre boxer
			for (int i = 0; i < linkNettel.size(); i++) {
				// Hvis ikke linken er synlig er det ingenting å gjøre
				if (!((Link)link.elementAt(i)).isVisible()) continue;

				Nettel n = (Nettel)linkNettel.elementAt(i);

				int fromX = x + sizeX/2;
				int fromY = y + sizeY/2;
				int toX = n.getX() + n.getSizeX()/2;
				int toY = n.getY() + n.getSizeY()/2;


				int tx = (toX - fromX)/2 +fromX -vlanBoxSizeX/2;
				int ty = (toY - fromY)/2 +fromY -vlanBoxSizeY/2;

				// temp hack
				{
					boolean b = false;
					if (fromX+fromY < toX+toY)
					{
						b = true;
					} else
					if (fromX+fromY == toX+toY)
					{
						if (fromX < toX)
						{
							b = true;
						}
					}

					if (b)
					{
						tx = (fromX - toX)/2 +toX -vlanBoxSizeX/2;
						ty = (fromY - toY)/2 +toY -vlanBoxSizeY/2;
					}

					if (drawVlan) {
						g.setColor(new Color(255, 255, 225) );
						g.fillRect(tx, ty, vlanBoxSizeX, vlanBoxSizeY);
						g.setColor(Color.black);
						g.drawRect(tx, ty, vlanBoxSizeX, vlanBoxSizeY);

						g.setColor(Color.black);
						int vlanNr;
						if (vlan != 0) {
							vlanNr = vlan;
						} else {
							vlanNr = n.getVlan();
						}
						g.drawString("" + vlanNr, tx+1, ty-1 +vlanBoxSizeY);

					} else if (((Link)link.elementAt(i)).getIsTrunk() && vlan != 0 ) {
						String text = "Trunk";
						FontMetrics fontMetrics = g.getFontMetrics(nf);
						int fontWidth = fontMetrics.stringWidth(text);

						tx = (toX - fromX)/2 +fromX -(fontWidth+2)/2;

						Rectangle vlanRect = new Rectangle(tx, ty, fontWidth+2, vlanBoxSizeY);
						((Link)link.elementAt(i)).setVlanRect(vlanRect);

						g.setColor(new Color(255, 255, 225) );
						g.fillRect(tx, ty, fontWidth+2, vlanBoxSizeY);
						g.setColor(Color.black);
						g.drawRect(tx, ty, fontWidth+2, vlanBoxSizeY);

						g.setColor(Color.black);
						g.drawString(text, tx+1, ty-1 +vlanBoxSizeY);

					}
				}

			}
		}
		if (pass == 5)
		{
			// tegn bokser som bare dukker opp ved å holde musen over noe i en viss tid
			if (desc != null) desc.drawSelf(g);
			for (int i = 0; i < link.size(); i++) {
				Link l = (Link)link.elementAt(i);
				l.drawPopup(g);
			}

		}

	}

	public void setHashKey(String s) { hashKey = s; }
	public String getHashKey() { return hashKey; }

	public boolean getIconVisible() { return iconVisible; }
	public void setIconVisible(boolean visible) { iconVisible = visible; }

	public boolean isVisible() { return isVisible; }
	public void setVisible(boolean visible)
	{
		// Sett visible-status for denne nettel
		isVisible = visible;
	}

	public void transform()
	{
		if (clickId != 0) {
			setBoksid(clickId);
			setKat(clickKat);
		}
	}


	public void setXY(int InX, int InY)
	{
		int canvasX = com.getNet().getMinimumSize().width;
		int canvasY = com.getNet().getMinimumSize().height;

		if (canvasY == 0 && InY < canvasTopSpaceY)
		{
			y = canvasTopSpaceY;

		} else
		if (canvasX > 0)
		{
			if (InX > 0 && InX < canvasX-sizeX)
			{
				x = InX;
			} else
			{
				if (InX <= 0)
				{
					x = 0;
				} else
				{
					x = canvasX-sizeX-1;
				}
			}

			if (InY > canvasTopSpaceY && InY < canvasY-sizeY)
			{
				y = InY;
			} else
			{
				if (InY <= canvasTopSpaceY)
				{
					y = canvasTopSpaceY;
				} else
				{
					y = canvasY-sizeY-1;
				}
			}

		} else
		{
			x = InX;
			y = InY;
		}

		nettelIcon.setXY(x, y);

	}

	public void locationSet() { locationSet = true; }
	public boolean getLocationSet() { return locationSet; }

	public int getX() { return x; }
	public int getY() { return y; }

	public int getSizeX() { return sizeX; }
	public int getSizeY() { return nettelIcon.getSizeY(); }

	public void setMouseOver(boolean InMouseOver, int InMouseOverX, int InMouseOverY)
	{
		mouseOver = InMouseOver;
		mouseOverX = InMouseOverX;
		mouseOverY = InMouseOverY;

		if (mouseOver) {
			if (nc != null) {
				if (drawPopup) {
					setDrawPopup(false);
				}
				nc.end();
			}
			nc = new NettelAction(this);
			nc.start();
		} else {
			if (drawPopup) {
				setDrawPopup(false);
			}
		}
	}
	public boolean getMouseOver() { return mouseOver; }

	public void disablePopup()
	{
		if (nc != null) {
			nc.end();
		}
		if (getDrawPopup()) {
			setDrawPopup(false);
		}
	}

	public void setDrawPopup(boolean drawPopup)
	{
		this.drawPopup = drawPopup;
		if (drawPopup && !popupUpToDate) {
			updatePopup();
		}

		if (mouseOverLink == -1) {
			// Muspekeren er over selve boksen
			if (drawPopup) {
				com.d("  Popup over boks drawn", 6);
				addPopup(desc);
				desc.show(mouseOverX, mouseOverY, graph);
			} else {
				com.d("  Popup over boks hidden", 6);
				//desc.hide();
				hideAllPopups();
			}
		} else {
			// Musen er over en link
			Link l = (Link)link.elementAt(mouseOverLink);
			if (drawPopup) {
				com.d("  Popup over link drawn", 6);
				PopupMessage pm = l.showPopup(mouseOverX, mouseOverY, graph, com);
				if (pm != null) addPopup(pm);
			} else {
				com.d("  Popup over link hidden", 6);
				//l.hidePopup();
				hideAllPopups();
			}
		}
	}

	// Vi ønsker kun at en popup skal vises samtidig, så når en ny popup tas evt. gamle bort
	private static Vector popupList = new Vector();
	private static void addPopup(PopupMessage pm) { popupList.addElement(pm); }
	private static void hideAllPopups()
	{
		for (int i=0; i < popupList.size(); i++) {
			PopupMessage pm = (PopupMessage)popupList.elementAt(i);
			pm.hide();
		}
		popupList.removeAllElements();
	}


	public boolean getDrawPopup() { return drawPopup; }
	public void setDrawVlan(boolean InDrawVlan) { drawVlan = InDrawVlan; }

	public void setSelected(boolean InSelected)
	{
		setSelected = InSelected;

		if (setSelected)
		{
			// må finne size på canavas
			Dimension d = com.getNet().getMinimumSize();
			int canvasX = d.width;
			int canvasY = d.height;

			int x = (canvasX - sizeX) / 2;
			int y = (canvasY - sizeY) / 2;

			setXY(x, y);
		}
	}

	public Link addLink(Nettel n, int linkId, double capacity, double last, String ifName)
	{
		if (groupMember) {
			if (n.getGroup() == group) {
				com.d("     " + getName() + " er i gruppe med " + n.getName(), 6);
				capacity = 0;
			}
		}

		double lastPst;
		if (capacity == 0 || last < 0) {
			lastPst = -1;
		} else {
			lastPst = (last*8) / (capacity*1000000) * 100;
		}

		Link l = new Link(this, n, linkId, capacity, lastPst, ifName);

		linkNettel.addElement(n);
		link.addElement(l);
		return l;
	}

	public Link getLinkTo(Nettel n)
	{
		for (int i=0; i < link.size(); i++) {
			Link l = (Link)link.elementAt(i);
			if (l.getNettelTo().equals(n)) return l;
		}
		// Ingen link til n funnet
		return null;
	}

	public void recalcLink(boolean b, Nettel n)
	{
		for (int i = 0; i < link.size(); i++)
		{
			((Link)link.elementAt(i)).recalc();
			if (b)
			{
				((Nettel)linkNettel.elementAt(i)).recalcLink(false, this);
			} else
			if ( ((Nettel)linkNettel.elementAt(i)).equals(n) )
			{
				((Nettel)linkNettel.elementAt(i)).recalcLink(false, n);
			}
		}

	}

	public void recalcLink()
	{
		for (int i = 0; i < link.size(); i++)
		{
			Link l = (Link)link.elementAt(i);
			l.recalc();
			l.getLinkOtherWay().recalc();
		}
	}


	public void resetLink()
	{
		linkNettel.removeAllElements();
		link.removeAllElements();
		popupUpToDate = false;
	}

	public void resetLast()
	{
		lastX = 0;
		lastY = 0;
	}

	public void setClicked(boolean b) { click = b; setMove = b; }

	public void setMove(int moveX, int moveY)
	{
		setMove(moveX, moveY, true);
	}
	public void setMove(int moveX, int moveY, boolean refresh)
	{
		if (setMove)
		{
			lastX = moveX - x;
			lastY = moveY - y;
			setMove = false;
		}

		int oldX = x;
		int oldY = y;

		int x = moveX-lastX;
		int y = moveY-lastY;

		setXY(x, y);
		recalcLink(true, this);

		if (refresh) {
			com.getNet().repaint();
		}


	}

	public boolean contains(int x, int y)
	{
		if (!isVisible || !iconVisible) return false;

		if (nettelIcon.contains(x, y) ) {
			mouseOverLink = -1;
			return true;
		}

		for (int i = 0; i < link.size(); i++) {
			if ( ((Link)link.elementAt(i)).contains(x, y) ) {
				mouseOverLink = i;
				return true;
			}
		}
		return false;
	}
	// Opplyser om punktet (x,y) er innenfor selve boksen
	public boolean boksContains(int x, int y)
	{
		if (!isVisible || !iconVisible) return false;
		return nettelIcon.contains(x, y);
	}


	public boolean containsNettel(int x, int y)	{ return nettelIcon.contains(x, y); }
	public boolean containsLink(int x, int y)
	{
		for (int i = 0; i < link.size(); i++) {
			if ( ((Link)link.elementAt(i)).contains(x, y) ) {
				return true;
			}
		}
		return false;
	}

	public Link getLink(int x, int y)
	{
		for (int i = 0; i < link.size(); i++) {
			if ( ((Link)link.elementAt(i)).contains(x, y) ) {
				return (Link)link.elementAt(i);
			}
		}
		return null;
	}

	private void updatePopup()
	{
		desc = new PopupMessage(com.getNet(), popupFont);
		if (descText != null) {
			desc.addMessage(descText);
		}
		// Så oppdaterer vi alle linker
		for (int i=0; i < link.size(); i++) {
			Link l = (Link)link.elementAt(i);
			com.d("  Calling updatePopup on link", 7);
			l.updatePopup(com.getNet(), popupFont);
		}
		popupUpToDate = true;
	}
	public String processText(String text, String[] data)
	{
		descText = Input.processText(text, data, keywords);
		return descText;
	}

	public String toString() {
		return getName();
	}
}














