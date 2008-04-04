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

public class netboxTooltip extends javax.swing.JPanel {
    
    /** Creates new form netboxTooltip */
    public netboxTooltip() {
        initComponents();
    }
    
    public netboxTooltip(String _sysname, String _category, String _room,
                         String _type, String _load, String _uptime){
        initComponents();
        
        sysnameValue.setText(_sysname);
        categoryValue.setText(_category);
        roomValue.setText(_room);
        typeValue.setText(_type);
        loadValue.setText(_load);
        uptimeValue.setText(_uptime);

    }
    
    private void initComponents() {//GEN-BEGIN:initComponents
        
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
        
        org.jdesktop.layout.GroupLayout layout = new org.jdesktop.layout.GroupLayout(this);
        this.setLayout(layout);
        layout.setHorizontalGroup(
                layout.createParallelGroup(org.jdesktop.layout.GroupLayout.LEADING)
                .add(layout.createSequentialGroup()
                .addContainerGap()
                .add(layout.createParallelGroup(org.jdesktop.layout.GroupLayout.LEADING)
                .add(jButton1, org.jdesktop.layout.GroupLayout.DEFAULT_SIZE, 228, Short.MAX_VALUE)
                .add(layout.createParallelGroup(org.jdesktop.layout.GroupLayout.LEADING, false)
                .add(layout.createSequentialGroup()
                .add(sysnameLabel)
                .addPreferredGap(org.jdesktop.layout.LayoutStyle.UNRELATED)
                .add(sysnameValue, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE, 154, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE))
                .add(layout.createSequentialGroup()
                .add(catLabel)
                .addPreferredGap(org.jdesktop.layout.LayoutStyle.UNRELATED)
                .add(categoryValue, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE, 160, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE))
                .add(layout.createSequentialGroup()
                .add(typeLabel)
                .addPreferredGap(org.jdesktop.layout.LayoutStyle.RELATED, 12, Short.MAX_VALUE)
                .add(typeValue, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE, 160, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE))
                .add(layout.createSequentialGroup()
                .add(roomLabel)
                .addPreferredGap(org.jdesktop.layout.LayoutStyle.UNRELATED)
                .add(roomValue, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE, 160, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE))
                .add(layout.createSequentialGroup()
                .add(loadLabel)
                .addPreferredGap(org.jdesktop.layout.LayoutStyle.RELATED, 12, Short.MAX_VALUE)
                .add(loadValue, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE, 160, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE))
                .add(layout.createSequentialGroup()
                .add(uptimeLabel)
                .addPreferredGap(org.jdesktop.layout.LayoutStyle.RELATED, 12, Short.MAX_VALUE)
                .add(uptimeValue, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE, 160, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE))))
                .addContainerGap())
                );
        
        
        layout.linkSize(new java.awt.Component[] {categoryValue, loadValue, roomValue, sysnameValue, typeValue, uptimeValue}, org.jdesktop.layout.GroupLayout.HORIZONTAL);
        
        
        
        layout.linkSize(new java.awt.Component[] {catLabel, loadLabel, roomLabel, sysnameLabel, typeLabel, uptimeLabel}, org.jdesktop.layout.GroupLayout.HORIZONTAL);
        
        layout.setVerticalGroup(
                layout.createParallelGroup(org.jdesktop.layout.GroupLayout.LEADING)
                .add(layout.createSequentialGroup()
                .addContainerGap()
                .add(layout.createParallelGroup(org.jdesktop.layout.GroupLayout.BASELINE)
                .add(sysnameLabel)
                .add(sysnameValue))
                .addPreferredGap(org.jdesktop.layout.LayoutStyle.RELATED)
                .add(layout.createParallelGroup(org.jdesktop.layout.GroupLayout.BASELINE)
                .add(catLabel)
                .add(categoryValue))
                .addPreferredGap(org.jdesktop.layout.LayoutStyle.RELATED)
                .add(layout.createParallelGroup(org.jdesktop.layout.GroupLayout.BASELINE)
                .add(typeLabel)
                .add(typeValue))
                .addPreferredGap(org.jdesktop.layout.LayoutStyle.RELATED)
                .add(layout.createParallelGroup(org.jdesktop.layout.GroupLayout.BASELINE)
                .add(roomLabel)
                .add(roomValue))
                .addPreferredGap(org.jdesktop.layout.LayoutStyle.RELATED)
                .add(layout.createParallelGroup(org.jdesktop.layout.GroupLayout.BASELINE)
                .add(loadLabel)
                .add(loadValue))
                .addPreferredGap(org.jdesktop.layout.LayoutStyle.RELATED)
                .add(layout.createParallelGroup(org.jdesktop.layout.GroupLayout.BASELINE)
                .add(uptimeLabel)
                .add(uptimeValue))
                .addPreferredGap(org.jdesktop.layout.LayoutStyle.RELATED)
                .add(jButton1)
                .addContainerGap(org.jdesktop.layout.GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE))
                );
    }//GEN-END:initComponents

    private void jButton1ActionPerformed(java.awt.event.ActionEvent evt) {//GEN-FIRST:event_jButton1ActionPerformed
        try {
            AppletContext ac = no.uninett.netmap.Main._getAppletContext();
            if (ac != null){
                ac.showDocument(new URL("https://navdev.uninett.no/browse/" + this.sysnameValue.getText()), "_blank");
            }
        } catch (MalformedURLException ex) {//GEN-LAST:event_jButton1ActionPerformed
            Logger.getLogger(netboxTooltip.class.getName()).log(Level.SEVERE, null, ex);
        }
    }
    
    
    // Variables declaration - do not modify//GEN-BEGIN:variables
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
    // End of variables declaration//GEN-END:variables
    
}
