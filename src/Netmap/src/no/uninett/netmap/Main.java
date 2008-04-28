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
package no.uninett.netmap;

import java.applet.AppletContext;
import java.awt.Component;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.lang.Thread.UncaughtExceptionHandler;
import java.net.MalformedURLException;
import java.net.URL;
import java.util.ArrayList;
import java.util.logging.Level;
import java.util.logging.Logger;
import javax.swing.ImageIcon;
import javax.swing.JCheckBoxMenuItem;
import javax.swing.JOptionPane;
import no.uninett.display.views.MainView;
import no.uninett.netmap.resources.ResourceHandler;
import prefuse.Visualization;
import prefuse.data.io.DataIOException;
import prefuse.util.ui.JPrefuseApplet;
import javax.swing.JCheckBox;
import javax.swing.JLabel;
import prefuse.data.Graph;

public class Main extends JPrefuseApplet {

    private static ResourceHandler m_resourceHandler;
    private static prefuse.Display m_display;
    private static Visualization m_vis;
    private static MainView m_view;
    private static Graph m_graph;
    private static Logger log = Logger.getAnonymousLogger();
    private static String sessionID;
    private static AppletContext appletContext;
    private static ArrayList<String> availableCategories;
    private static ArrayList<JCheckBox> categoryCheckboxes;
    private static URL baseURL;
    private boolean prepared = false;
    //  UI-components
    private javax.swing.JMenuBar menuBar;
    private javax.swing.JMenu filterMenu;
    private javax.swing.JMenu categoryMenu;
    private javax.swing.JMenu linkMenu;
    private javax.swing.JCheckBoxMenuItem allLinktypes;
    private javax.swing.JMenu visMenu;
    private javax.swing.JMenu freezeMenu;
    private javax.swing.JCheckBoxMenuItem freezeCheckbox;
    private static JCheckBoxMenuItem useRelativeSpeeds;
    private static JCheckBoxMenuItem hideOrphanNetboxes;

    @Override
    public void init() {
        log.entering("Main", "init");

        sessionID = this.getParameter("sessionid");
           JOptionPane.showMessageDialog(null, sessionID);
        if (sessionID == null || sessionID.equals("")) {
            JOptionPane.showMessageDialog(null, "ERROR: No sessionID found\n");
            return;
        }

        /*
         * Fetch the baseURL so we know where to get our files
         */
        try {
            baseURL = new URL(this.getParameter("baseurl"));
        } catch (MalformedURLException e) {
            JOptionPane.showMessageDialog(null, "ERROR: baseurl (" + this.getParameter("baseurl") + ") not in valid format\n" + e.getMessage());
        }

        /*
         * Set size if given by params - adds supoport for javascript-resizing
         * Defaults to 800x600
         */
        try {
            int width = Integer.parseInt(this.getParameter("width"));
            int height = Integer.parseInt(this.getParameter("height"));

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

        ActionListener catFilter = new ActionListener() {

            public void actionPerformed(ActionEvent arg0) {
                ArrayList<String> wantedCategories = new ArrayList<String>();
                for (Component c : categoryMenu.getMenuComponents()) {
                    if (((JCheckBox) c).isSelected()) {
                        wantedCategories.add(((JCheckBox) c).getText());
                    }
                }
                if (m_view != null) {
                    m_view.filterNodes(wantedCategories);
                }
            }
        };

        ActionListener freezeButtonHandler = new ActionListener() {

            public void actionPerformed(ActionEvent arg0) {
                if (freezeCheckbox.isSelected()) {
                    no.uninett.netmap.Main.getVis().cancel("layout");
                } else {
                    no.uninett.netmap.Main.getVis().run("layout");
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
            if (cat.equals("GW") || cat.equals("GSW")) {
                tmp.setSelected(true);
            }
            categoryMenu.add(tmp);
        }

        filterMenu.add(categoryMenu);

        linkMenu.setText("Linktypes");

        allLinktypes.setSelected(true);
        allLinktypes.setText("All");
        linkMenu.add(allLinktypes);

        filterMenu.add(linkMenu);

        menuBar.add(filterMenu);

        visMenu.setText("Visualisation");
        hideOrphanNetboxes.setText("Hide single instances");
        hideOrphanNetboxes.setToolTipText("Hides netboxes not connected to any other boxes");
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

        menuBar.add(freezeMenu);

        this.setJMenuBar(menuBar);
        this.doLayout();
        this.setVisible(true);

        appletContext = getAppletContext();

        final JLabel loaderImg;
        try {
            URL loadingImage = new URL(baseURL.toString() + "/applet/media/loading.gif");
            loaderImg = new JLabel(new ImageIcon(loadingImage));
            loaderImg.setEnabled(true);
            loaderImg.setSize(100, 100);

            this.add(loaderImg);
            Thread loadingWatcher = new Thread() {

                @Override
                public void run() {
                    boolean running = true;
                    while (running) {
                        if (m_view != null && prepared) {
                            loaderImg.setVisible(false);
                            running = false;
                        }
                        try {
                            sleep(10);
                        } catch (InterruptedException ex) {
                        }
                    }
                }
            };
            loadingWatcher.start();
        } catch (MalformedURLException ex) {
            Logger.getLogger(Main.class.getName()).log(Level.SEVERE, null, ex);
        }

        // Load graph
        URL graphURL = null;
        try {
            graphURL = new URL(baseURL.toString() + "/server");
        } catch (MalformedURLException ex) {
            Logger.getLogger(Main.class.getName()).log(Level.SEVERE, null, ex);
        }
        try {

            m_graph = no.uninett.netmap.Main.getResourceHandler().getGraphFromURL(graphURL);
        } catch (DataIOException ex) {
            Logger.getLogger(Main.class.getName()).log(Level.SEVERE, null, ex);
        }
        this.prepared = true;
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

        m_display.addControlListener(new prefuse.controls.FocusControl());
        m_display.addControlListener(new no.uninett.display.controllers.NetmapControl());
        m_display.addControlListener(new prefuse.controls.DragControl());
        m_display.addControlListener(new prefuse.controls.PanControl());
        m_display.addControlListener(new prefuse.controls.ZoomControl());
        m_display.addControlListener(new prefuse.controls.ZoomToFitControl());

        m_display.setSize(this.getSize());
        this.add(m_display);
        m_display.setEnabled(true);
        m_display.setVisible(true);

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
        return this.freezeCheckbox.isSelected();
    }

    public static AppletContext _getAppletContext() {
        return appletContext;
    }

    public static ArrayList<String> getAvailableCategories() {
        return availableCategories;
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
}
