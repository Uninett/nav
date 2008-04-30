package no.uninett.nav.display.views.actions;

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
