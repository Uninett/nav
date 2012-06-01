package no.uninett.nav.display.views.layouts;

import java.awt.BasicStroke;
import java.awt.Color;
import java.awt.Graphics2D;
import no.uninett.nav.netmap.Main;
import prefuse.Constants;
import prefuse.render.EdgeRenderer;
import prefuse.util.ColorLib;
import prefuse.visual.EdgeItem;
import prefuse.visual.VisualItem;

public class NetmapEdgeRender extends EdgeRenderer {

	private double net_load_in = -1;
	private double net_load_out = -1;
	private double capacity = -1;
	// Got to love the naming convention.. shrug
	private Color high_load_color = ColorLib.getColor(ColorLib.rgb(204, 0, 0));
	private Color high_med_load_color = ColorLib.getColor(ColorLib.rgb(252, 175, 62));
	private Color med_load_color = ColorLib.getColor(ColorLib.rgb(252, 233, 79));
	private Color low_med_load_color = ColorLib.getColor(ColorLib.rgb(186, 252, 79));
	private Color low_load_color = ColorLib.getColor(ColorLib.rgb(138, 226, 52));
	// Default colors
	private Color out_color = ColorLib.getColor(ColorLib.rgb(230,230,230));
	private Color in_color = ColorLib.getColor(ColorLib.rgb(230,230,230));

	private int lowLevel = 100*1000000;
	private int lowMedLevel = 512*1000000;
	private int medLevel = 1024*1000000;
	private int medHighLevel = 4096*1000000;

	public NetmapEdgeRender() {
		setEdgeType(Constants.EDGE_TYPE_CURVE);
	}

    @Override
		public void render(Graphics2D g, VisualItem item) {

			EdgeItem ei = (EdgeItem) item;

			// Get link colors if link data is present

			try {
				capacity = Double.parseDouble(ei.getString("link_capacity"));
				net_load_in = Double.parseDouble(ei.getString("link_load_in"));
				net_load_out = Double.parseDouble(ei.getString("link_load_out"));
			} catch (Exception e) {
				in_color = ColorLib.getColor(ColorLib.rgb(200, 200, 200));
				out_color = ColorLib.getColor(ColorLib.rgb(200, 200, 200));
			}
			if (net_load_in != -1 && net_load_out != -1) {

				double out_percent = (net_load_out*8) / (capacity*1000000);
				double in_percent = (net_load_in*8) / (capacity*1000000);
				if (Main.getUseRelativeSpeeds().isSelected()) {
					if (out_percent < 0.3) {
						out_color = low_load_color;
					} else if (out_percent < 0.6) {
						out_color = med_load_color;
					} else if (out_percent < 0.9) {
						out_color = high_med_load_color;
					} else {
						out_color = high_med_load_color;
					}

					if (in_percent < 0.3) {
						in_color = low_load_color;
					} else if (in_percent < 0.6) {
						in_color = med_load_color;
					} else if (in_percent < 0.9) {
						in_color = high_med_load_color;
					} else {
						in_color = high_med_load_color;
					}
				} else {
					if (net_load_out < lowLevel){
						out_color = low_load_color;
					} else if (net_load_out < lowMedLevel){
						out_color = low_med_load_color;
					} else if (net_load_out < medLevel){
						out_color = med_load_color;
					} else if (net_load_out < medHighLevel){
						out_color = high_med_load_color;
					} else if (net_load_out > medHighLevel){
						out_color = high_load_color;
					}
					if (net_load_in < lowLevel){
						in_color = low_load_color;
					} else if (net_load_in < lowMedLevel){
						in_color = low_med_load_color;
					} else if (net_load_in < medLevel){
						in_color = med_load_color;
					} else if (net_load_in < medHighLevel){
						in_color = high_med_load_color;
					} else if (net_load_in > medHighLevel){
						in_color = high_load_color;
					}
				}

			} else {
				in_color = ColorLib.getColor(ColorLib.rgb(200, 200, 200));
				out_color = ColorLib.getColor(ColorLib.rgb(200, 200, 200));
			}

			VisualItem item1 = ei.getSourceItem();
			VisualItem item2 = ei.getTargetItem();

			double source_center_x = item1.getEndX() - (item1.getEndX() - item1.getStartX()) / 2.0;
			double source_center_y = item1.getEndY() - (item1.getEndY() - item1.getStartY()) / 2.0;
			double target_center_x = item2.getEndX() - (item2.getEndX() - item2.getStartX()) / 2.0;
			double target_center_y = item2.getEndY() - (item2.getEndY() - item2.getStartY()) / 2.0;

			double center_x = source_center_x + ((target_center_x - source_center_x) / 2.0);
			double center_y = source_center_y + ((target_center_y - source_center_y) / 2.0);

			BasicStroke stroke = new BasicStroke(1);

			// Get the proper width
			if (capacity != -1) {
				if (capacity < 10) {
					item.setSize(5.0);
					stroke = new BasicStroke(5);
				} else if (capacity < 100) {
					item.setSize(20.0);
					stroke = new BasicStroke(20);
				} else if (capacity < 1000) {
					item.setSize(50.0);
					stroke = new BasicStroke(50);
				} else {
					item.setSize(80.0);
					stroke = new BasicStroke(80);
				}
			}
			g.setStroke(stroke);
			g.setPaint(out_color);

			g.drawLine((int)source_center_x, (int)source_center_y, (int)center_x, (int)center_y);

			g.setPaint(in_color);
			g.drawLine((int)center_x, (int)center_y, (int)target_center_x, (int)target_center_y);
		}
}
