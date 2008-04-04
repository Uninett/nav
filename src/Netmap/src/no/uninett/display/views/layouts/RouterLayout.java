/*
 * The RouterView class - Displays the router on a network
 * 
 */

package no.uninett.display.views.layouts;

import prefuse.action.layout.graph.ForceDirectedLayout;
import prefuse.data.Node;
import prefuse.visual.VisualItem;

public class RouterLayout extends ForceDirectedLayout {

    public RouterLayout() {
        super("graph", false);
        
    }
    
    @Override
    protected float getMassValue(VisualItem vi) {
        Node n = (Node) vi;
        return (float) 1+ (n.getDegree()*1.5f);
    }
}