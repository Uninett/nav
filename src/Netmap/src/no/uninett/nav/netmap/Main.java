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
package no.uninett.nav.netmap;

import java.applet.AppletContext;
import java.awt.Component;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.io.*;
import java.net.*;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.logging.Level;
import java.util.logging.Logger;
import javax.swing.ImageIcon;
import javax.swing.JCheckBox;
import javax.swing.JCheckBoxMenuItem;
import javax.swing.JLabel;
import javax.swing.JOptionPane;
import no.uninett.nav.display.views.MainView;
import no.uninett.nav.netmap.resources.ResourceHandler;
import prefuse.Visualization;
import prefuse.data.Graph;
import prefuse.data.Tuple;
import prefuse.data.event.TupleSetListener;
import prefuse.data.io.DataIOException;
import prefuse.data.search.PrefixSearchTupleSet;
import prefuse.data.search.SearchTupleSet;
import prefuse.data.tuple.TupleSet;
import prefuse.util.ui.JPrefuseApplet;
import prefuse.util.ui.JSearchPanel;
import prefuse.visual.VisualItem;

public class Main extends JPrefuseApplet {

    private static AppletContext appletContext;
    private static ArrayList<String> availableCategories;
    private static ArrayList<String> availableLinkTypes;
    private static String[] Layer3_LinkTypes = new String[] {"core","elink","link"};
    private static String[] Layer2_LinkTypes = new String[] {"lan"};
    private static Graph m_graph;
    private static Logger log = Logger.getAnonymousLogger();
    private static MainView m_view;
    private static ResourceHandler m_resourceHandler;
    private static String sessionID;
    private static URL baseURL;
    private static Visualization m_vis;
    private static prefuse.Display m_display;
    private static ActionListener catFilter;
    private boolean prepared = false;

    private javax.swing.JCheckBoxMenuItem allLinktypes;
    private javax.swing.JCheckBoxMenuItem freezeCheckbox;
    private javax.swing.JButton increaseFontSizeButton;
    private javax.swing.JButton decreaseFontSizeButton;
    private javax.swing.JButton saveLayoutButton;
    private javax.swing.JMenu categoryMenu;
    private javax.swing.JMenu filterMenu;
    private javax.swing.JMenu freezeMenu;
    private javax.swing.JMenu linkMenu;
    private javax.swing.JMenu visMenu;
    private javax.swing.JMenuBar menuBar;
    private static JCheckBoxMenuItem hideOrphanNetboxes;
    private static JCheckBoxMenuItem useRelativeSpeeds;

    @Override
    public void init() {
        log.entering("Main", "init");

        sessionID = getParameter("sessionid");
        if (sessionID == null || sessionID.equals("")) {
            JOptionPane.showMessageDialog(null, "ERROR: No sessionID found\n");
            return;
        }

        /*
         * Fetch the baseURL so we know where to get our files
         */
        try {
            baseURL = new URL(getParameter("baseurl"));
        } catch (MalformedURLException e) {
            JOptionPane.showMessageDialog(null, "ERROR: baseurl (" + getParameter("baseurl") + ") not in valid format\n" + e.getMessage());
        }

        /*
         * Set size if given by params - adds supoport for javascript-resizing
         * Defaults to 800x600
         */
        try {
            int width = Integer.parseInt(getParameter("width"));
            int height = Integer.parseInt(getParameter("height"));

            if (width > 0 && height > 0) {
                this.setSize(new java.awt.Dimension(width, height));
            } else {
                throw new Exception();
            }
        } catch (Exception e) {
            this.setSize(new java.awt.Dimension(800, 600));
        }

      

        m_resourceHandler = new ResourceHandler();
        try {
            availableCategories = m_resourceHandler.getAvailableCategories();
        } catch (Exception ex) {
            Logger.getLogger(Main.class.getName()).log(Level.SEVERE, null, ex);
        }

        menuBar = new javax.swing.JMenuBar();
        filterMenu = new javax.swing.JMenu();
        categoryMenu = new javax.swing.JMenu();

        linkMenu = new javax.swing.JMenu();
        allLinktypes = new javax.swing.JCheckBoxMenuItem();

        visMenu = new javax.swing.JMenu();
        hideOrphanNetboxes = new javax.swing.JCheckBoxMenuItem();
        useRelativeSpeeds = new javax.swing.JCheckBoxMenuItem();

        freezeMenu = new javax.swing.JMenu();
        freezeCheckbox = new javax.swing.JCheckBoxMenuItem();

        filterMenu.setText("Filters");
        categoryMenu.setText("Categories");

        /*
         * Create actionListeners
         */
        catFilter = new ActionListener() {

            public void actionPerformed(ActionEvent arg0) {
                ArrayList<String> wantedCategories = new ArrayList<String>();
                ArrayList<String> wantedLinkTypes = new ArrayList<String>();

                for (Component c : categoryMenu.getMenuComponents()) {
                    if (((JCheckBox) c).isSelected()) {
                        wantedCategories.add(((JCheckBox) c).getText());
                    }
                }
                for (Component c : linkMenu.getMenuComponents()) {
                    if (((JCheckBox) c).isSelected()) {
			if (((JCheckBox) c).getText().equals("Layer 3")){
				for (String type : Layer3_LinkTypes){
					wantedLinkTypes.add(type);
				}
			}
			if (((JCheckBox) c).getText().equals("Layer 2")){
				for (String type : Layer2_LinkTypes){
					wantedLinkTypes.add(type);
				}
			}
                    }
                }
                if (m_view != null) {
                    m_view.filterNodes(wantedCategories, wantedLinkTypes, hideOrphanNetboxes.isSelected());
		    freezeCheckbox.setSelected(false);
                }
            }
        };

        ActionListener freezeButtonHandler = new ActionListener() {

            public void actionPerformed(ActionEvent arg0) {
                if (freezeCheckbox.isSelected()) {
                    no.uninett.nav.netmap.Main.getVis().cancel("layout");
                } else {
                    no.uninett.nav.netmap.Main.getVis().run("layout");
                }
            }
        };

        ActionListener increaseFontSizeHandler = new ActionListener() {
                public void actionPerformed(ActionEvent arg0) {
                        if (m_view != null){
                                m_view.increaseFontSize();
                        }
                }
        };
        ActionListener decreaseFontSizeHandler = new ActionListener() {
                public void actionPerformed(ActionEvent arg0) {
                        if (m_view != null){
                                m_view.decreaseFontSize();
                        }
                }
        };
	ActionListener saveLayoutHandler = new ActionListener() {
		public void actionPerformed(ActionEvent arg0){
			if (m_view != null){
				if (!sendPositionData()){
            				JOptionPane.showMessageDialog(null, "ERROR: Could not save layout\n");
				} else {
            				JOptionPane.showMessageDialog(null, "Layout saved\n");
				}
			}
		}
	};

        /*
         * Clear and add available checkboxes according
         * to what the server has.
         */
        categoryMenu.removeAll();
        for (String cat : availableCategories) {
            JCheckBox tmp = new JCheckBox();
            tmp.setText(cat);
            tmp.addActionListener(catFilter);
	    if (cat.equals("GW") || cat.equals("GSW")){
		tmp.setSelected(true);
	    }
            tmp.setEnabled(true);
	    categoryMenu.add(tmp);
        }

        filterMenu.add(categoryMenu);

        linkMenu.setText("Linktypes");
	linkMenu.removeAll();

	availableLinkTypes = new ArrayList<String>();
	availableLinkTypes.add("Layer 2");
	availableLinkTypes.add("Layer 3");
        for (String type : availableLinkTypes) {
            JCheckBox tmp = new JCheckBox();
            tmp.setText(type);
            tmp.addActionListener(catFilter);
	    if (type.equals("Layer 3")){
		    tmp.setSelected(true);
	    }
            tmp.setEnabled(true);
            linkMenu.add(tmp);
        }

        filterMenu.add(linkMenu);

        menuBar.add(filterMenu);

        visMenu.setText("Visualisation");
        hideOrphanNetboxes.setText("Show single instances");
        hideOrphanNetboxes.setToolTipText("Hides netboxes not connected to any other netboxes (in the db, not by filtering)");
        hideOrphanNetboxes.addActionListener(catFilter);
        visMenu.add(hideOrphanNetboxes);
        visMenu.add(new javax.swing.JSeparator());
        useRelativeSpeeds.setText("Show load based on relative usage");
        useRelativeSpeeds.setToolTipText("Calculate load-color using the line capacity");
        visMenu.add(useRelativeSpeeds);
        menuBar.add(visMenu);

        freezeMenu.setText("Actions");

        freezeCheckbox.setText("Freeze layout");
        freezeCheckbox.setToolTipText("Stop the layout-process.");
        freezeCheckbox.addActionListener(freezeButtonHandler);
        freezeMenu.add(freezeCheckbox);

        increaseFontSizeButton = new javax.swing.JButton("Increase font size");
        increaseFontSizeButton.addActionListener(increaseFontSizeHandler);
        freezeMenu.add(increaseFontSizeButton);
        decreaseFontSizeButton = new javax.swing.JButton("Decrease font size");
        decreaseFontSizeButton.addActionListener(decreaseFontSizeHandler);
        freezeMenu.add(decreaseFontSizeButton);

        try {
        	if (getParameter("is_admin").equals("true")){
        		saveLayoutButton = new javax.swing.JButton("Save layout");
        		saveLayoutButton.addActionListener(saveLayoutHandler);
        		freezeMenu.add(saveLayoutButton);
        	}
        } catch (Exception e){
        	System.out.println("NOTICE: Could not get is_admin-parameter");
        }



        menuBar.add(freezeMenu);

        setJMenuBar(menuBar);
        doLayout();
        setVisible(true);

        appletContext = getAppletContext();

        // Load graph
        URL graphURL = null;
        try {
            graphURL = new URL(baseURL.toString() + "/server");
        } catch (MalformedURLException ex) {
            Logger.getLogger(Main.class.getName()).log(Level.SEVERE, null, ex);
        }
        try {

            m_graph = no.uninett.nav.netmap.Main.getResourceHandler().getGraphFromURL(graphURL);
        } catch (DataIOException ex) {
            Logger.getLogger(Main.class.getName()).log(Level.SEVERE, null, ex);
        }
        prepared = true;

    }

    @Override
    public void start() {

        log.setLevel(Level.ALL);
        log.entering("Main", "main");

        m_vis = new Visualization();
        m_display = new prefuse.Display();
        m_display.setVisualization(m_vis);
        m_view = new MainView();
        m_view.prepare();
        m_view.runActions();

	// Run default filters
	catFilter.actionPerformed(null);

	m_display.addControlListener(new prefuse.controls.FocusControl());
        m_display.addControlListener(new no.uninett.nav.display.controllers.NetmapControl());
        m_display.addControlListener(new prefuse.controls.DragControl());
        m_display.addControlListener(new prefuse.controls.PanControl());
        m_display.addControlListener(new prefuse.controls.ZoomControl());
        m_display.addControlListener(new prefuse.controls.ZoomToFitControl());

        m_display.setSize(this.getSize());
        this.add(m_display);
        m_display.setEnabled(true);
        m_display.setVisible(true);

	SearchTupleSet search = new PrefixSearchTupleSet();
	m_vis.addFocusGroup(Visualization.SEARCH_ITEMS, search);
	search.addTupleSetListener(new TupleSetListener(){
		public void tupleSetChanged(TupleSet tset, Tuple[] added, Tuple[] removed){
			m_vis.getAction("zoomAction").setEnabled(true);
			m_vis.getAction("zoomAction").run();
		}
	});

	JSearchPanel jsp = new JSearchPanel(m_vis, "graph.nodes", Visualization.SEARCH_ITEMS, new String[]{"sysname","ip","room"}, true, true);
	jsp.setLabelText("  Search: ");
	jsp.setEnabled(true);
	menuBar.add(jsp);

			// Zoom after initial run
			try {
			Thread.sleep(5000);
			m_vis.getAction("zoomAction").setEnabled(true);
			m_vis.getAction("zoomAction").run();
			} catch (Exception e){}

    }

    public static ResourceHandler getResourceHandler() {
        return m_resourceHandler;
    }

    public static Visualization getVis() {
        return m_vis;
    }

    public static prefuse.Display getDisplay() {
        return m_display;
    }

    public static MainView getView() {
        return m_view;
    }

    public static String getSessionID() {
        return sessionID;
    }

    public boolean inLayoutFreeze() {
        return freezeCheckbox.isSelected();
    }

    public static AppletContext _getAppletContext() {
        return appletContext;
    }

    public static ArrayList<String> getAvailableCategories() {
        return availableCategories;
    }
    public static ArrayList<String> getAvailableLinkTypes() {
        return availableLinkTypes;
    }

    public static Graph getGraph() {
        return m_graph;
    }

    public static JCheckBoxMenuItem getUseRelativeSpeeds() {
        return useRelativeSpeeds;
    }
    public static URL getBaseURL(){
        return baseURL;
    }
    static public String bwToString(String bandwidth){
	    try {
		    Double bw = Double.parseDouble(bandwidth);
		    if (bw < 1024){
			    return String.format("%.2f", bw) + "Kbit/s";
		    }
		    if (bw > 1048576){
			    return String.format("%.3f", (bw/(1024*1024))) + "Gbit/s";
		    }
		    return String.format("%.2f", (bw/1024)) + "Mbit/s";

	    } catch(Exception e){
		    return "unknown";
	    }
    }
    public static ArrayList getAllLinkTypes(){
	    ArrayList<String> ret = new ArrayList<String>();
	    for (String type : Layer2_LinkTypes) {
			ret.add(type);
		}
	    for (String type : Layer3_LinkTypes) {
			ret.add(type);
		}
	    return ret;
    }

    public boolean sendPositionData(){
	    try {
	    URL url;
	    URLConnection urlConn;
	    DataOutputStream printout;
	    DataInputStream input;
	    // URL of CGI-Bin script.
	    url = new URL (baseURL + "/position");
	    // URL connection channel.
	    urlConn = url.openConnection();
	    // Let the run-time system (RTS) know that we want input.
	    urlConn.setDoInput (true);
	    // Let the RTS know that we want to do output.
	    urlConn.setDoOutput (true);
	    // No caching, we want the real thing.
	    urlConn.setUseCaches (false);
	    // Specify the content type.
	    urlConn.setRequestProperty
		    ("Content-Type", "application/x-www-form-urlencoded");
	    // Send POST output.
	    printout = new DataOutputStream (urlConn.getOutputStream ());
	    Iterator iter = getVis().items("graph.nodes");
	    String postData = "";
	    while (iter.hasNext()){
		VisualItem item = (VisualItem) iter.next();
		if (item.getX() != 0.0 && item.getY() != 0.0){
			if (item.getString("sysname") != null && !item.getString("sysname").equals("")){
				postData += URLEncoder.encode(item.getString("sysname") + "_x", "utf-8") + "=" + item.getX() + "&";
				postData += URLEncoder.encode(item.getString("sysname") + "_y", "utf-8") + "=" + item.getY() + "&";
		 	}
		}
	    }
	    System.out.println(postData);
	    printout.writeBytes (postData);
	    printout.flush ();
	    printout.close ();
	    // Get response data.
	    input = new DataInputStream (urlConn.getInputStream ());
	    String str;
	    while (null != ((str = input.readLine())))
	    {
		    System.out.println (str);
	    }
	    input.close ();
	    } catch (Exception e){
		    System.out.println(e.getMessage());
	    }
	    return true;
    }
}
