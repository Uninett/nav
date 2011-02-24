/**
 * Copyright 2008 UNINETT AS
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
 * Authors: Kristian Klette <kristian.klette@uninett.no>
 *
 */

package no.uninett.nav.display.controllers;

import java.awt.event.MouseEvent;
import java.util.Iterator;
import javax.swing.JPopupMenu;
import no.uninett.nav.window.*;
import no.uninett.nav.netmap.Main;
import prefuse.Visualization;
import prefuse.controls.ControlAdapter;
import prefuse.data.tuple.TupleSet;
import prefuse.visual.EdgeItem;
import prefuse.visual.NodeItem;
import prefuse.visual.VisualItem;

public class NetmapControl extends ControlAdapter {

    @Override
    public void itemEntered(VisualItem item, MouseEvent e) {
        item.setHover(true);
    }

    @Override
    public void itemExited(VisualItem item, MouseEvent e) {
        item.setHover(false);
    }

    @Override
    public void itemClicked(VisualItem item, java.awt.event.MouseEvent e) {
	    Visualization cur_vis = no.uninett.nav.netmap.Main.getVis();
	    item.setFixed(true);
	    JPopupMenu t = new JPopupMenu();
	    if (item.isInGroup("graph.nodes")){
		    String load;
		    try {
			load = String.format("%.2f", Double.parseDouble(item.getString("cpuload"))) + " %";
		    } catch (java.lang.NumberFormatException parseException){
			    load = "unknown";
		    }
		    t.add(new netboxTooltip(
					    item.getString("sysname"),
					    item.getString("category"),
					    item.getString("type"),
					    item.getString("room"),
					    item.getString("ipdevinfolink"),
					    load
					   ));
	    } else if (item.isInGroup("graph.edges")){
		    Double cap = -1.0;
		    Double in = -1.0;
		    Double out = -1.0;
		    try {
		    	cap = Double.parseDouble(item.getString("link_capacity"));
			in = Double.parseDouble(item.getString("link_load_in"));
			out = Double.parseDouble(item.getString("link_load_out"));
			in = in / (cap*1000000);
			out = out / (cap*1000000);
			} catch (Exception exception){}
		    t.add(new linkTooltip(
					    item.getString("from_sysname") + " -> " + item.getString("to_sysname"),
					    item.getString("from_interface") + " -> " + item.getString("to_interface"),
					    item.getString("netident"),
					    item.getString("nettype"),
					    item.getString("link_capacity"),
					    "In: " + Main.bwToString(item.getString("link_load_in")) + "  (" + String.format("%.1f", in) +"%) " +
					    "Out: " + Main.bwToString(item.getString("link_load_out")) + "  (" + String.format("%.1f", out) + "%)",
                        item.getString("ipdevinfolink")
					 ));
	    }

	    t.pack();
	    t.show(e.getComponent(), e.getX(), e.getY());

    }

    public void findAndSetNeighborHighlight(VisualItem item, boolean state) {
	    if (item != null) {
		    NodeItem ni = (NodeItem) item;
		    Iterator iter = ni.edges();

		    while (iter.hasNext()) {
			    EdgeItem ei = (EdgeItem) iter.next();
			    ei.getAdjacentItem(ni).setHighlighted(state);
			    ei.setHighlighted(state);
		    }
	    }
    }
}
