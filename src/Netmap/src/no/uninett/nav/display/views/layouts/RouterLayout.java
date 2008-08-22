package no.uninett.nav.display.views.layouts;

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
        return 1+ (n.getDegree()*1.5f);
    }
}
