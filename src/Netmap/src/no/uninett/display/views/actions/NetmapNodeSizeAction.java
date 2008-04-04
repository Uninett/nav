/*
 * NetmapNodeSizeAction.java
 * 
 * Created on Aug 16, 2007, 2:18:55 PM
 * 
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */

package no.uninett.display.views.actions;

import prefuse.action.assignment.SizeAction;
import prefuse.data.Node;
import prefuse.visual.VisualItem;

public class NetmapNodeSizeAction extends SizeAction {

    public NetmapNodeSizeAction() {
        super("graph.nodes");
    }
    
    @Override
public double getSize(VisualItem item){
        Node n = (Node)item;
        return 1.0;
    }

}
