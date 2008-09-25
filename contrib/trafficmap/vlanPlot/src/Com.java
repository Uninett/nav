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

import java.util.*;
import java.net.*;

import java.applet.*;
import java.awt.*;


class Com
{
	public Com()
	{

	}

	public void d(String s, int i)
	{
		if (i <= debugLevel)
		{
			System.out.println(s);
		}
	}

	public void dn(String s, int i)
	{
		if (i <= debugLevel)
		{
			System.out.print(s);
		}
	}


	public void setDebugLevel(int InDebugLevel) { debugLevel = InDebugLevel; }

	public void setApplet(Applet InApplet) { applet = InApplet; }
	public Applet getApplet() { return applet; }



	public void setKeyl(Keyl Inkeyl) { keyl = Inkeyl; }
	public Keyl getKeyl() { return keyl; }

	public void setMouse(Mouse Inmouse) { mouse = Inmouse; }
	public Mouse getMouse() { return mouse; }

	public void setMouseMove(MouseMove Inmv) { mv = Inmv; }
	public MouseMove getMouseMove() { return mv; }


	// Menyer
	public void setGwMenu(PopupMenus InGwMenu) { gwMenu = InGwMenu; }
	public PopupMenus getGwMenu() { return gwMenu; }

	public void setSwMenu(PopupMenus InSwMenu) { swMenu = InSwMenu; }
	public PopupMenus getSwMenu() { return swMenu; }

	public void setLinkMenu(PopupMenus InLinkMenu) { linkMenu = InLinkMenu; }
	public PopupMenus getLinkMenu() { return linkMenu; }

	public void setLinkGwMenu(PopupMenus InLinkMenu) { linkGwMenu = InLinkMenu; }
	public PopupMenus getLinkGwMenu() { return linkGwMenu; }

	public void setActiveMenu(PopupMenus InActiveMenu) { activeMenu = InActiveMenu; }
	public PopupMenus getActiveMenu() { return activeMenu; }



	public void setInput(Input Ininput ) { input = Ininput; }
	public Input getInput() { return input; }

	public void setLeft(Left InLeft ) { left = InLeft; }
	public Left getLeft() { return left; }

	public void setNet(Net Innet ) { net = Innet; }
	public Net getNet() { return net; }


	public void setClicked(int Inclicked ) { clicked = Inclicked; }
	public int getClicked() { return clicked; }

	public void setClickedGrp(int inClickedGrp ) { clickedGrp = inClickedGrp; }
	public int getClickedGrp() { return clickedGrp; }


	public void setMouseX(int InmouseX ) { mouseX = InmouseX; }
	public int getMouseX() { return mouseX; }

	public void setMouseY(int InmouseY ) { mouseY = InmouseY; }
	public int getMouseY() { return mouseY; }

	// admin
	public void setAdmin(Admin InAdmin) { admin = InAdmin; }
	public Admin getAdmin() { return admin; }


	public void setLogo(Logo InLogo) { logo = InLogo; }
	public Logo getLogo() { return logo; }

	public void setLastInterval(long[] l) { lastInterval = l; }
	public long[] getLastInterval() { return lastInterval; }

	public void setRelativSkala(boolean b) { relativSkala = b; }
	public boolean getRelativSkala() { return relativSkala; }

	public void setTidAvg(boolean InAvg) { avg = InAvg; }
	public boolean getTidAvg() { return avg; }

	public void setBeginLastDate(Date d) { beginLastDate = d; }
	public Date getBeginLastDate() { return beginLastDate; }
	public void setEndLastDate(Date d) { endLastDate = d; }
	public Date getEndLastDate() { return endLastDate; }


	// Layout && Scrollbars
	public void setLayoutNettel(LayoutNettel ln) { layoutNettel = ln; }
	public LayoutNettel getLayoutNettel() { return layoutNettel; }

	public void setTopScroll(Scrollbar sb) { topScroll = sb; }
	public Scrollbar getTopScroll() { return topScroll; }

	public void setMidScroll(Scrollbar sb) { midScroll = sb; }
	public Scrollbar getMidScroll() { return midScroll; }

	public void setBottomScroll(Scrollbar sb) { bottomScroll = sb; }
	public Scrollbar getBottomScroll() { return bottomScroll; }


	public void setMainPanel(panel p) { mainPanel = p; }
	public panel getMainPanel() { return mainPanel; }

	// vars
	Keyl keyl;
	Mouse mouse;
	MouseMove mv;

	PopupMenus gwMenu;
	PopupMenus swMenu;
	PopupMenus linkMenu;
	PopupMenus linkGwMenu;

	PopupMenus activeMenu;

	URL documentBase;
	Applet applet;

	panel mainPanel;

	Logo logo;

	// objects
	Left left;
	Net net;
	Input input;
	Admin admin;

	LayoutNettel layoutNettel;
	Scrollbar topScroll;
	Scrollbar midScroll;
	Scrollbar bottomScroll;

	// mouse
	int mouseX = 0;
	int mouseY = 0;
	int clicked = 0;
	int clickedGrp = -1;

	int debugLevel = 0;

	Date beginLastDate;
	Date endLastDate;
	long[] lastInterval = new long[2];
	boolean relativSkala;
	boolean avg;

	public static int javaMajorVersion = 1;
	public static int javaMinorVersion = 0;
	public static int javaRevisionVersion = 0;
	public void setJavaMajorVersion(int i) { javaMajorVersion = i; }
	public void setJavaMinorVersion(int i) { javaMinorVersion = i; }
	public void setJavaRevisionVersion(int i) { javaRevisionVersion = i; }
	public int getJavaMajorVersion() { return javaMajorVersion; }
	public int getJavaMinorVersion() { return javaMinorVersion; }
	public int getJavaRevisionVersion() { return javaRevisionVersion; }

    // Åpne browser med en URL
    public void showURL(String urlS)
    {
		URL url = null;

		try {
		    url = new URL(urlS);
		} catch (MalformedURLException e) {
		    d("Bad URL: " + urlS, 1);
		}

		if (getApplet() != null) {
			getApplet().getAppletContext().showDocument(url, "_blank");
		} else {
			d("Ikke applet, kan ikke laste URL: " + urlS, 1);
		}
	}

	// Quicksort for a Vector of either String or Integer objects
	public static void quickSort(Vector v) {
		// quicksort the array
		int incr = v.size() / 2;

		while (incr >= 1) {
			for (int i = incr; i < v.size(); i++) {
				Object tmp = (Object)v.elementAt(i);
				int j = i;
				while (j >= incr && compare(tmp, (Object)v.elementAt(j - incr)) < 0 ) {
					v.setElementAt( v.elementAt(j-incr), j);
					j -= incr;
				}
				v.setElementAt(tmp, j);
			}
			incr /= 2;
		}
	}
	private static int compare(Object o1, Object o2)
	{
		int i1,i2;
		if (o1 instanceof String) {
			try {
				i1 = Integer.parseInt((String)o1);
				i2 = Integer.parseInt((String)o2);
			} catch (NumberFormatException e) {
				return (((String)o1).toLowerCase()).compareTo(((String)o2).toLowerCase());
			}
		} else if (o1 instanceof Vlan) {
			i1 = ((Vlan)o1).getVlan();
			i2 = ((Vlan)o2).getVlan();
		} else {
			i1 = ((Integer)o1).intValue();
			i2 = ((Integer)o2).intValue();
		}

		if (i1 == i2) return 0;
		return i1 < i2 ? -1 : 1;
	}

}


