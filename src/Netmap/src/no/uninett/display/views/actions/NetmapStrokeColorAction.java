/**
 * Copyright 2006 UNINETT AS
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

package no.uninett.display.views.actions;

import java.awt.BasicStroke;
import prefuse.Visualization;
import prefuse.action.assignment.StrokeAction;
import prefuse.util.ColorLib;
import prefuse.visual.VisualItem;

/**
 *
 * @author klette
 */
public class NetmapStrokeColorAction extends StrokeAction {

    BasicStroke link_stroke = new BasicStroke(1.5f,java.awt.BasicStroke.CAP_ROUND, java.awt.BasicStroke.JOIN_ROUND);
    BasicStroke node_stroke = new BasicStroke(8.0f,java.awt.BasicStroke.CAP_ROUND, java.awt.BasicStroke.JOIN_ROUND);
    public NetmapStrokeColorAction() {
        super(Visualization.ALL_ITEMS);
    }

    public NetmapStrokeColorAction(String group) {
        super(group);
        
    }
    
    @Override
    public BasicStroke getStroke(VisualItem item){
        
        if(item.getGroup().equals("graph.nodes")){
            return node_stroke;
        } else {
            item.setStrokeColor(ColorLib.rgb(0, 0, 0));
            return link_stroke;  
        }
        
    }
}