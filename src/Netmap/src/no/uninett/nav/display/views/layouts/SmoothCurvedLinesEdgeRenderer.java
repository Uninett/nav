/*
 * SmoothCurvedLinesEdgeRenderer.java
 * 
 * Created on Aug 15, 2007, 11:31:20 AM
 * 
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */

package no.uninett.display.views.layouts;

import java.awt.geom.Point2D;
import prefuse.Constants;
import prefuse.render.EdgeRenderer;
import prefuse.visual.EdgeItem;

/**
 *
 * @author klette
 */
public class SmoothCurvedLinesEdgeRenderer extends EdgeRenderer {

        @Override
protected void getCurveControlPoints(EdgeItem eitem, Point2D[] cp, double x1, double y1, double x2, double y2) {
        double dx = x2 - x1;
        double dy = y2 - y1;

        double c = Math.sqrt((dx * dx) + (dy * dy));

        double radAngle = Math.acos((Math.abs(dx)) / c);
        double degAngle = radAngle * (180 / Math.PI);

        double wx = getWeight(90 - degAngle);
        double wy = getWeight(degAngle);

        if (eitem.isDirected() && m_edgeArrow != Constants.EDGE_ARROW_NONE) {
            if (m_edgeArrow == Constants.EDGE_ARROW_FORWARD) {
                cp[0].setLocation(x1 + wx * 2 * dx / 3, y1 + wy * 2 * dy / 3);
                cp[1].setLocation(x2 - dx / 8, y2 - dy / 8);
            } else {
                cp[0].setLocation(x1 + dx / 8, y1 + dy / 8);
                cp[1].setLocation(x2 - wx * 2 * dx / 3, y2 - wy * 2 * dy / 3);
            }
        } else {
            cp[0].setLocation(x1 + wx * 1 * dx / 3, y1 + wy * 1 * dy / 3);
            cp[1].setLocation(x1 + wx * 2 * dx / 3, y1 + wy * 2 * dy / 3);
        }
    }

    private double getWeight(double x) {
        return 1 - Math.min(Math.abs(3 - x / 22.5), 1);
    }

}
