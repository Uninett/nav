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
import java.awt.Component;
import java.awt.MenuItem;
import java.awt.PopupMenu;
import java.awt.event.ActionListener;
import java.util.Vector;


class PopupMenus
{
	PopupMenu menu;
	ActionListener al;
	Vector menuItems = new Vector();
	String menuName;
	String menuLabel;

	String nettelName = "";
	String fullNettelName = "";
	String ifName = "";
	double capacity;
	//String speed = "";
	Vector ipRom;
	boolean router = true;
	boolean useCricket = true;

	public PopupMenus(String menuName, String menuLabel, Canvas addTo, ActionListener al)
	{
		this.menuName = menuName;
		this.menuLabel = menuLabel;
		this.al = al;
		//menu = new PopupMenu(menuName);
		menu = new PopupMenu();
		addTo.add(menu);
	}

	public PopupMenus(String menuName, String menuLabel, String[] menuItems, Canvas addTo, ActionListener al)
	{
		this.menuName = menuName;
		this.menuLabel = menuLabel;
		this.al = al;
        //menu = new PopupMenu(menuName);
        menu = new PopupMenu();

		for (int i=0; i < menuItems.length; i++) addMenuItem(menuItems[i]);
		//addAll();
		refresh();
        addTo.add(menu);

	}

	public void addMenuItem(String menuItem)
	{
		menuItems.addElement(menuItem);
	}

	public void addMenuItem(Vlan menuItem)
	{
		menuItems.addElement(menuItem);
	}

	private void addAll()
	{
		if (menuItems == null) return;

		MenuItem mi;
		for(int i = 0; i < menuItems.size(); i++) {
			Object menuItem = menuItems.elementAt(i);
			String itemS = menuItem.toString();
			if (itemS.equals("|")) { menu.addSeparator(); continue; }
	    	menu.add(mi = new MenuItem (itemS) );
	    	mi.setName(menuName);
	    	mi.addActionListener(al);
		}
	}

	public void clear()
	{
		menuItems.removeAllElements();
	}
	public void sort()
	{
		Com.quickSort(menuItems);
	}

	public void refresh()
	{
		menu.removeAll();
		if (menuLabel != null && menuLabel.length() > 0) {
			MenuItem mi = new MenuItem(menuLabel);
			menu.add(mi);
			menu.addSeparator();
		}
		addAll();
	}

	public void show(Component origin, int x, int y)
	{
		menu.show(origin, x, y);
	}

	public String getMenuName() { return menuName; }
	public boolean useCricket() { return useCricket; }

	public void setMenuLabel(String s) { menuLabel = s; }

	public void setNettelName (String InNettelName) { nettelName = InNettelName; }
	public String getNettelName() { return nettelName; }

	public void setFullNettelName (String s) { fullNettelName = s; }
	public String getFullNettelName() { return fullNettelName; }

	public void setIfName (String InIfName) { ifName = InIfName.toLowerCase(); }
	public String getIfName() { return ifName; }

	public void setCapacity(double d) { capacity = d; }
	public double getCapacity() { return capacity; }

	//public void setSpeed(String s) { speed = s; }
	//public String getSpeed() { return speed; }

	public void setIsRouter (boolean InRouter) { router = InRouter; }
	public boolean getIsRouter() { return router; }

}
