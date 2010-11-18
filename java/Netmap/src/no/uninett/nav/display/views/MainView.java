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
package no.uninett.nav.display.views;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.logging.Logger;

import prefuse.action.animate.VisibilityAnimator;
import prefuse.data.Node;
import prefuse.visual.NodeItem;
import prefuse.visual.EdgeItem;
import prefuse.visual.VisualItem;
import prefuse.visual.tuple.TableEdgeItem;
import prefuse.util.ui.JForcePanel;

import no.uninett.nav.netmap.Main;
import no.uninett.nav.display.views.NodeRenderer;
import no.uninett.nav.display.views.actions.NetmapTextColorAction;
import no.uninett.nav.display.views.layouts.NetmapGrouping;

public class MainView {
    private boolean prepared = false;
    boolean has_position_data = false;

    private Logger log = Logger.getLogger("netmap");
    private int currentFontSize = 160;

    private prefuse.action.assignment.FontAction fontAction;

    @SuppressWarnings(value = "unchecked")
        public void prepare() {
            prepared = false;

            // Index most frequently used fields.
            try {
                Main.getGraph().getNodeTable().index("category");
                Main.getGraph().getEdgeTable().index("link_capacity");
            } catch (Exception e){
                System.out.println("Could not index one or more tables");
            }
            // Attach graph to visualization
            no.uninett.nav.netmap.Main.getVis().reset();
            no.uninett.nav.netmap.Main.getVis().addGraph("graph", Main.getGraph());

            // See if we have stored position-data about the nodes
            System.out.println("Checking for saved positions");
            Iterator pos_iter = no.uninett.nav.netmap.Main.getVis().items("graph.nodes");
            while (pos_iter.hasNext()) {
                VisualItem node = (VisualItem) pos_iter.next();
                if (node.canGetString("position") && node.getString("position") != null && !node.getString("position").equals("")){
                    has_position_data = true;
                    System.out.println("Found position data for " + node.getString("sysname"));
                    String[] pos = node.getString("position").split("x");
                    try {
                        double xpos = Double.parseDouble(pos[0]);
                        double ypos = Double.parseDouble(pos[1]);
                        node.setX(xpos);
                        node.setY(ypos);
                        System.out.println("\t " + xpos + " x " + ypos);
                    } catch (Exception e) {
                        Logger.global.log(java.util.logging.Level.WARNING, "Could not set positional data for " +
                                node.getString("sysname") + "\n" + e.getMessage());
                    }
                }
            }


            NodeRenderer nodeRenderer = new NodeRenderer("sysname", "image");
            nodeRenderer.setRenderType(prefuse.render.AbstractShapeRenderer.RENDER_TYPE_DRAW);
            nodeRenderer.setImagePosition(prefuse.Constants.TOP);
            nodeRenderer.setMaxImageDimensions(300,300);

            prefuse.render.DefaultRendererFactory factory = new prefuse.render.DefaultRendererFactory(nodeRenderer);
            prefuse.render.EdgeRenderer er = new no.uninett.nav.display.views.layouts.NetmapEdgeRender();
            factory.setDefaultEdgeRenderer(er);

            no.uninett.nav.netmap.Main.getVis().setRendererFactory(factory);

            prefuse.action.ItemAction nodeColor = new prefuse.action.assignment.ColorAction("graph.nodes", prefuse.visual.VisualItem.FILLCOLOR, prefuse.util.ColorLib.rgb(255, 0, 0));
            prefuse.action.ItemAction textColor = new prefuse.action.assignment.ColorAction("graph.nodes", prefuse.visual.VisualItem.TEXTCOLOR, prefuse.util.ColorLib.rgb(0, 0, 0));

            fontAction = new prefuse.action.assignment.FontAction();
            fontAction.setDefaultFont(new java.awt.Font("Serif", 1, currentFontSize));

            // create an action list containing all color assignments
            prefuse.action.ActionList color = new prefuse.action.ActionList();

            color.add(new NetmapTextColorAction());

            prefuse.action.ActionList layout = new prefuse.action.ActionList(prefuse.activity.Activity.INFINITY);

            no.uninett.nav.display.views.layouts.RouterLayout fdl = new no.uninett.nav.display.views.layouts.RouterLayout();

            // Allow some extra time for calculation between renders
            fdl.setMaxTimeStep(100);

            // Set up some basic forces. Seems to work well with the NTNU-routers at least.
            // Ohh, the black magic variables
            prefuse.util.force.NBodyForce nbf = new prefuse.util.force.NBodyForce();
            nbf.setParameter(0, -8000.0F);
            nbf.setParameter(1, 4700.0F);
            nbf.setParameter(2, -55.0F);
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
            layout.add(new no.uninett.nav.display.views.actions.NetmapNodeSizeAction());
            layout.add(new prefuse.action.RepaintAction());

            no.uninett.nav.netmap.Main.getVis().putAction("repaint", new prefuse.action.RepaintAction());
            no.uninett.nav.netmap.Main.getVis().putAction("color", color);
            no.uninett.nav.netmap.Main.getVis().putAction("font", fontAction);
            no.uninett.nav.netmap.Main.getVis().putAction("layout", layout);
            no.uninett.nav.netmap.Main.getVis().putAction("zoomAction", new no.uninett.nav.display.views.actions.NetmapZoomAction());

        }

    public void cancelActions() {
        no.uninett.nav.netmap.Main.getVis().cancel("color");
        no.uninett.nav.netmap.Main.getVis().cancel("font");
        no.uninett.nav.netmap.Main.getVis().cancel("layout");
        no.uninett.nav.netmap.Main.getVis().cancel("zoomAction");
        no.uninett.nav.netmap.Main.getVis().cancel("repaint");
    }

    public void runActions() {
        no.uninett.nav.netmap.Main.getVis().runAfter("color", 10);
        no.uninett.nav.netmap.Main.getVis().runAfter("font", 10);
        no.uninett.nav.netmap.Main.getVis().run("layout");
        no.uninett.nav.netmap.Main.getVis().run("zoomAction");
        no.uninett.nav.netmap.Main.getVis().run("repaint");
        prepared = true;
    }

    public void filterNodes(ArrayList<String> categories, ArrayList<String> linktypes, boolean show_strays) {
        cancelActions();

        ArrayList<String> def_types = new ArrayList<String>(no.uninett.nav.netmap.Main.getAvailableCategories());
        ArrayList<String> link_type = new ArrayList<String>();
        try {
            link_type.add("2");
            link_type.add("3");
        } catch (Exception e){
            e.printStackTrace();
            return;
        }
        if (categories != null) {
            for (String cat : categories) {
                if (def_types.contains(cat)) {
                    def_types.remove(cat);
                }
            }
        }
        if (linktypes != null){
            for (String type : linktypes){
                if (link_type.contains(type)) {
                    link_type.remove(type);
                }
            }
        }

        for (Iterator i = no.uninett.nav.netmap.Main.getVis().items("graph"); i.hasNext();) {
            ((VisualItem) i.next()).setVisible(true);
        }


        // Filter out links first
        String pred_string = "";

        for (String ntype : link_type) {
            pred_string += (" layer = \'" + ntype + "\' OR");
            if (ntype.equals("unknown")){
                pred_string += " nettype =\'\' OR";
            }
        }
        pred_string += " false";

        Logger.global.log(java.util.logging.Level.FINEST, "EdgeFilter: " + pred_string);
        java.util.Iterator it = no.uninett.nav.netmap.Main.getVis().items("graph.edges",
                prefuse.data.expression.parser.ExpressionParser.predicate(pred_string));
        while (it.hasNext()) {
            EdgeItem item = (EdgeItem) it.next();
            item.setVisible(false);
        }


        // Filter out netboxes
        pred_string = "";
        for (String ncat : def_types) {
            pred_string += (" category = \'" + ncat + "\' OR");
        }
        if (!show_strays) {
            pred_string += " DEGREE() = 0";
        } else {
            pred_string += " false";
        }
        Logger.global.log(java.util.logging.Level.FINEST, "Netbox filter: " + pred_string);
        it = no.uninett.nav.netmap.Main.getVis().items("graph.nodes",
                prefuse.data.expression.parser.ExpressionParser.predicate(pred_string));
        while (it.hasNext()) {
            NodeItem item = (NodeItem) it.next();
            item.setVisible(false);

            for (Iterator ei = item.edges(); ei.hasNext();) {
                VisualItem e = (TableEdgeItem) ei.next();
                e.setVisible(false);
            }
        }

        it = no.uninett.nav.netmap.Main.getVis().items("graph.nodes", prefuse.data.expression.parser.ExpressionParser.predicate("DEGREE() != 0"));
        while(it.hasNext()){
            NodeItem item = (NodeItem) it.next();
            boolean hasEdges = false;
            for (Iterator ei = item.edges(); ei.hasNext();){
                VisualItem e = (TableEdgeItem) ei.next();
                if (e.isVisible()){
                    hasEdges = true;
                }
            }
            if (!hasEdges){
                item.setVisible(false);
            }

        }

        runActions();
        prepared = true;
    }
    public boolean isPrepared(){
        return prepared;
    }
    public void setFont(java.awt.Font font){
        no.uninett.nav.netmap.Main.getVis().cancel("font");
        ((prefuse.action.assignment.FontAction)no.uninett.nav.netmap.Main.getVis().getAction("font")).setDefaultFont(font);
        no.uninett.nav.netmap.Main.getVis().run("font");
    }
    public void increaseFontSize(){
        currentFontSize += 4;
        setFont(new java.awt.Font("Serif", 1, currentFontSize));
    }
    public void decreaseFontSize(){
        if (currentFontSize < 10) {
            return;
        }
        currentFontSize -= 4;
        setFont(new java.awt.Font("Serif", 1, currentFontSize));
    }

}
