/**
 * Copyright 2007 UNINETT AS
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
 * Authors: Kristian Klette <klette@samfundet.no>
 *
 */

package no.uninett.display.controllers;

import java.awt.event.MouseEvent;
import java.util.Iterator;
import javax.swing.JPopupMenu;
import no.uninett.window.*;
import prefuse.Visualization;
import prefuse.controls.ControlAdapter;
import prefuse.data.tuple.TupleSet;
import prefuse.visual.EdgeItem;
import prefuse.visual.NodeItem;
import prefuse.visual.VisualItem;

public class NetmapControl extends ControlAdapter {

    private boolean shift_pressed = false;
    private VisualItem last_clicked;
    private TupleSet neighbor_group;

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
	    Visualization cur_vis = no.uninett.netmap.Main.getVis();
	    item.setFixed(true);
	    JPopupMenu t = new JPopupMenu();
	    if (item.isInGroup("graph.nodes")){
		    t.add(new netboxTooltip(
					    item.getString("sysname"),
					    item.getString("category"),
					    item.getString("type"),
					    item.getString("room"),
					    item.getString("cpuload")
					   ));
	    } else if (item.isInGroup("graph.edges")){
		    t.add(new linkTooltip(
					    item.getString("from_sysname") + " -> " + item.getString("to_sysname"),
					    item.getString("to_interface") + " -> " + item.getString("from_interface"),
					    "",
					    item.getString("link_capacity"),
					    "In: " + item.getString("link_load_in") + " Out: " + item.getString("link_load_out")
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
