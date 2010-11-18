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

package no.uninett.nav.display.views.actions;

import java.awt.Color;
import prefuse.Visualization;
import prefuse.action.assignment.ColorAction;
import prefuse.util.ColorLib;
import prefuse.visual.VisualItem;

/**
 * Sets the correct colors for the text describing
 * the nodes.
 */
public class NetmapTextColorAction extends ColorAction {
    
    /**
     * Default constructor. Applies the action to Visualization.ALL_ITEMS
     */
    public NetmapTextColorAction() {
        super(Visualization.ALL_ITEMS, VisualItem.TEXTCOLOR);
    }
    
    /**
     * Creates a TextColorAction for a single group
     * 
     * @param group The visualization group
     */
    public NetmapTextColorAction(String group) {
        super(group, VisualItem.TEXTCOLOR);
    }
    
    /**
     * Returns the color of the item
     * @return int The color
     */
    @Override
    public int getColor(VisualItem item) {
        if (item.isInGroup("graph.nodes")) {
            return ColorLib.rgb(0, 0, 0);
        } else if (item.isInGroup("graph.edges")) {
            return ColorLib.color(Color.BLACK);
        } else {
            return ColorLib.color(Color.BLACK);
        }
    }
}
