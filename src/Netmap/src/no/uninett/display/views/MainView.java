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
package no.uninett.display.views;

import no.uninett.display.views.actions.NetmapTextColorAction;
import no.uninett.display.views.layouts.NetmapGrouping;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.logging.Logger;
import no.uninett.netmap.Main;
import prefuse.action.animate.VisibilityAnimator;
import prefuse.data.Node;
import prefuse.visual.NodeItem;
import prefuse.visual.VisualItem;
import prefuse.visual.tuple.TableEdgeItem;

public class MainView {
    private boolean prepared = false;

    private Logger log = Logger.getLogger("netmap");
    private Node largest = null;
    private NetmapGrouping ng;
    private boolean show_strays = false; // Render nodes without edges

    @SuppressWarnings(value = "unchecked")
    public void prepare() {
        this.prepared = false;

        // Index most frequently used fields.
        try {
            Main.getGraph().getNodeTable().index("category");
            Main.getGraph().getEdgeTable().index("link_capacity");
        } catch (Exception e){
            System.out.println("Could not index one or more tables");
        }
        // Attach graph to visualization
        no.uninett.netmap.Main.getVis().reset();
        no.uninett.netmap.Main.getVis().addGraph("graph", Main.getGraph());

        
        prefuse.render.LabelRenderer nodeRenderer = new prefuse.render.LabelRenderer("sysname",
                no.uninett.netmap.Main.getBaseURL().toString() + "image");
        nodeRenderer.setRenderType(prefuse.render.AbstractShapeRenderer.RENDER_TYPE_DRAW);
        nodeRenderer.setImagePosition(prefuse.Constants.TOP);


        prefuse.render.DefaultRendererFactory factory = new prefuse.render.DefaultRendererFactory(nodeRenderer);
        prefuse.render.EdgeRenderer er = new no.uninett.display.views.layouts.NetmapEdgeRender();
        factory.setDefaultEdgeRenderer(er);

        no.uninett.netmap.Main.getVis().setRendererFactory(factory);

        prefuse.action.ItemAction nodeColor = new prefuse.action.assignment.ColorAction("graph.nodes", prefuse.visual.VisualItem.FILLCOLOR, prefuse.util.ColorLib.rgb(255, 0, 0));
        prefuse.action.ItemAction textColor = new prefuse.action.assignment.ColorAction("graph.nodes", prefuse.visual.VisualItem.TEXTCOLOR, prefuse.util.ColorLib.rgb(0, 0, 0));

        prefuse.action.assignment.FontAction fontAction = new prefuse.action.assignment.FontAction();
        fontAction.setDefaultFont(new java.awt.Font("Serif", 1, 60));

        // create an action list containing all color assignments
        prefuse.action.ActionList color = new prefuse.action.ActionList();

        color.add(new NetmapTextColorAction());


        prefuse.action.ActionList layout = new prefuse.action.ActionList(prefuse.activity.Activity.INFINITY);

        no.uninett.display.views.layouts.RouterLayout fdl = new no.uninett.display.views.layouts.RouterLayout();
        
        // Allow some extra time for calculation between renders
        fdl.setMaxTimeStep(100);

        // Set up some basic forces. Seems to work well with the NTNU-routers at least.
        // Ohh, the black magic variables
        prefuse.util.force.NBodyForce nbf = new prefuse.util.force.NBodyForce();
        nbf.setParameter(0, -1000.0F);
        nbf.setParameter(1, 4700.0F);
        nbf.setParameter(2, -10.0F);
        prefuse.util.force.SpringForce sf = new prefuse.util.force.SpringForce();
        sf.setParameter(0, -1.0E-9F);
        sf.setParameter(1, 900.0F);

        prefuse.util.force.DragForce df = new prefuse.util.force.DragForce();
        df.setParameter(0, 0.0040F);

        fdl.getForceSimulator().addForce(nbf);
        fdl.getForceSimulator().addForce(sf);
        fdl.getForceSimulator().addForce(df);

        layout.add(fdl);
        
       
        VisibilityAnimator visibilityAnimator = new VisibilityAnimator();
        visibilityAnimator.setEnabled(true);
        visibilityAnimator.setDuration(10000);
        layout.add(visibilityAnimator);
        layout.add(new no.uninett.display.views.actions.NetmapNodeSizeAction());
        layout.add(new prefuse.action.RepaintAction());

        no.uninett.netmap.Main.getVis().putAction("repaint", new prefuse.action.RepaintAction());
        no.uninett.netmap.Main.getVis().putAction("color", color);
        no.uninett.netmap.Main.getVis().putAction("font", fontAction);
        no.uninett.netmap.Main.getVis().putAction("layout", layout);

    }

    public void cancelActions() {
        no.uninett.netmap.Main.getVis().cancel("color");
        no.uninett.netmap.Main.getVis().cancel("font");
        no.uninett.netmap.Main.getVis().cancel("layout");
        no.uninett.netmap.Main.getVis().cancel("zoomAction");
        no.uninett.netmap.Main.getVis().cancel("repaint");
    }

    public void runActions() {
        no.uninett.netmap.Main.getVis().runAfter("color", 10);
        no.uninett.netmap.Main.getVis().runAfter("font", 10);
        no.uninett.netmap.Main.getVis().run("layout");
        no.uninett.netmap.Main.getVis().run("zoomAction");
        no.uninett.netmap.Main.getVis().run("repaint");
        this.prepared = true;
    }

    public void filterNodes(ArrayList<String> categories) {
        this.cancelActions();

        ArrayList<String> def_types = new ArrayList<String>(no.uninett.netmap.Main.getAvailableCategories());

        for (Iterator i = no.uninett.netmap.Main.getVis().items("graph"); i.hasNext();) {
            ((VisualItem) i.next()).setVisible(true);
        }
        String pred_string = "ISNODE() AND (";
        if (categories != null) {
            for (String cat : categories) {
                if (def_types.contains(cat)) {
                    def_types.remove(cat);
                }
            }
        }
        for (String ncat : def_types) {
            pred_string += (" category = \'" + ncat + "\' OR");
        }
        if (!show_strays) {
            pred_string += " DEGREE() = 0 OR";
        }

        pred_string += " ISEDGE())";

        Logger.global.log(java.util.logging.Level.FINEST, "Filter: " + pred_string);
        java.util.Iterator it = no.uninett.netmap.Main.getVis().items("graph.nodes",
                prefuse.data.expression.parser.ExpressionParser.predicate(pred_string));
        while (it.hasNext()) {
            NodeItem item = (NodeItem) it.next();
            item.setVisible(false);

            for (Iterator ei = item.edges(); ei.hasNext();) {
                VisualItem e = (TableEdgeItem) ei.next();
                e.setVisible(false);
            }
        }
        this.runActions();
        this.prepared = true;
    }
    public boolean isPrepared(){
        return this.prepared;
    }
}
