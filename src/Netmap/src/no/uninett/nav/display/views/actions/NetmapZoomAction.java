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

import java.awt.geom.Rectangle2D;
import java.util.Iterator;
import prefuse.Display;
import prefuse.Visualization;
import prefuse.action.GroupAction;
import prefuse.data.tuple.TableTuple;
import prefuse.data.tuple.TupleSet;
import prefuse.util.GraphicsLib;
import prefuse.util.display.DisplayLib;
import prefuse.visual.VisualItem;

public class NetmapZoomAction extends GroupAction {

    @Override
	public void run(double arg) {
        Display display = no.uninett.nav.netmap.Main.getDisplay();
        
        if (!display.isTranformInProgress()) {
            TupleSet s_group = no.uninett.nav.netmap.Main.getVis().getGroup(Visualization.SEARCH_ITEMS);
            Rectangle2D.Double r = new Rectangle2D.Double();
            if (s_group.getTupleCount() > 0) {
                Iterator s_group_iter = s_group.tuples();
                if (s_group_iter.hasNext()) {
                    VisualItem item = no.uninett.nav.netmap.Main.getVis().
                            getVisualItem("graph.nodes", (TableTuple) s_group_iter.next());
                    r.setRect(item.getBounds());
                }
                while (s_group_iter.hasNext()) {
                    VisualItem item = no.uninett.nav.netmap.Main.getVis().getVisualItem("graph.nodes", (TableTuple) s_group_iter.next());
                    Rectangle2D.union(item.getBounds(), r, r);
                }

                GraphicsLib.expand(r, 1000 + (int) (1/display.getScale()));
                DisplayLib.fitViewToBounds(display, r, 200);
                setEnabled(false);
            }
        }
    }
}
