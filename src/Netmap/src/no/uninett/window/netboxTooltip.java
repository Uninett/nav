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
package no.uninett.window;

import java.applet.AppletContext;
import java.net.MalformedURLException;
import java.net.URL;
import java.util.logging.Level;
import java.util.logging.Logger;
import java.awt.*;
import javax.swing.JPanel;

public class netboxTooltip extends javax.swing.JPanel {

    private javax.swing.JLabel catLabel;
    private javax.swing.JLabel categoryValue;
    private javax.swing.JButton jButton1;
    private javax.swing.JLabel loadLabel;
    private javax.swing.JLabel loadValue;
    private javax.swing.JLabel roomLabel;
    private javax.swing.JLabel roomValue;
    private javax.swing.JLabel sysnameLabel;
    private javax.swing.JLabel sysnameValue;
    private javax.swing.JLabel typeLabel;
    private javax.swing.JLabel typeValue;
    private javax.swing.JLabel uptimeLabel;
    private javax.swing.JLabel uptimeValue;

    public netboxTooltip() {
    }

    public netboxTooltip(String _sysname, String _category, String _room,
                         String _type, String _load, String _uptime){

        JPanel pane = new JPanel(new GridBagLayout());
        GridBagConstraints c = new GridBagConstraints();

        sysnameLabel = new javax.swing.JLabel();
        catLabel = new javax.swing.JLabel();
        typeLabel = new javax.swing.JLabel();
        roomLabel = new javax.swing.JLabel();
        loadLabel = new javax.swing.JLabel();
        uptimeLabel = new javax.swing.JLabel();
        sysnameValue = new javax.swing.JLabel();
        categoryValue = new javax.swing.JLabel();
        typeValue = new javax.swing.JLabel();
        roomValue = new javax.swing.JLabel();
        loadValue = new javax.swing.JLabel();
        uptimeValue = new javax.swing.JLabel();
        jButton1 = new javax.swing.JButton();

        setBackground(new java.awt.Color(236, 237, 237));
        setBorder(javax.swing.BorderFactory.createEmptyBorder(1, 1, 1, 1));

        sysnameLabel.setFont(new java.awt.Font("Dialog", 1, 11));
        sysnameLabel.setText("Sysname:");

        catLabel.setFont(new java.awt.Font("Dialog", 1, 11));
        catLabel.setText("Category:");

        typeLabel.setFont(new java.awt.Font("Dialog", 1, 11));
        typeLabel.setText("Type:");

        roomLabel.setFont(new java.awt.Font("Dialog", 1, 11));
        roomLabel.setText("Room:");

        loadLabel.setFont(new java.awt.Font("Dialog", 1, 11));
        loadLabel.setText("CPU Load:");

        uptimeLabel.setFont(new java.awt.Font("Dialog", 1, 11));
        uptimeLabel.setText("Uptime:");

        sysnameValue.setText("sysname");

        categoryValue.setText("category");

        typeValue.setText("type");

        roomValue.setText("room");

        loadValue.setText("load");

        uptimeValue.setText("uptime");

        jButton1.setText("View in IP Device Center ");
        jButton1.addActionListener(new java.awt.event.ActionListener() {
            public void actionPerformed(java.awt.event.ActionEvent evt) {
                jButton1ActionPerformed(evt);
            }
        });

        c.fill = GridBagConstraints.HORIZONTAL;
        c.gridx = 0;
        c.gridy = 0;
        c.insets = new Insets(0,0,0,2);
        pane.add(sysnameLabel, c);

        c.gridx = 1;
        c.gridy = 0;
        pane.add(sysnameValue, c);

        pane.add(catLabel);
        pane.add(typeLabel);
        pane.add(roomLabel);
        pane.add(loadLabel);
        pane.add(uptimeLabel);
        pane.add(categoryValue);
        pane.add(typeValue);
        pane.add(roomValue);
        pane.add(loadValue);
        pane.add(uptimeValue);
        pane.doLayout();

        pane.setEnabled(true);
        pane.setVisible(true);
  
        sysnameValue.setText(_sysname);
        categoryValue.setText(_category);
        roomValue.setText(_room);
        typeValue.setText(_type);
        loadValue.setText(_load);
        uptimeValue.setText(_uptime);

    }

    private void jButton1ActionPerformed(java.awt.event.ActionEvent evt) {
        try {
            AppletContext ac = no.uninett.netmap.Main._getAppletContext();
            if (ac != null){
                ac.showDocument(new URL(no.uninett.netmap.Main.getBaseURL().toString() + "/browse/" + this.sysnameValue.getText()), "_blank");
            }
        } catch (MalformedURLException ex) {
            Logger.getLogger(netboxTooltip.class.getName()).log(Level.SEVERE, null, ex);
        }
    }
}
