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

import java.text.DecimalFormat;
import java.text.NumberFormat;

public class linkTooltip extends javax.swing.JPanel {
    
    public NumberFormat numFormat = new DecimalFormat("0.00");
    /** Creates new form netboxTooltip */
    public linkTooltip() {
        initComponents();
    }
    
    public linkTooltip(String link, String capacity, String bwIn, String bwOut, String type,
                         String interfaceIn, String interfaceOut){
        initComponents();
        
        Double _bwIn = Double.parseDouble(bwIn);
        Double _bwOut = Double.parseDouble(bwOut);
        Double _capacity = Double.parseDouble(capacity);
        
        this.bwInValue.setText(formatBandwidth(_bwIn/1000));
        this.bwOutValue.setText(formatBandwidth(_bwOut/1000));
        
        this.capacity.setText(formatBandwidth(_capacity));
        this.type.setText(type);
        this.interfaceIn.setText(interfaceIn);
        this.interfaceOut.setText(interfaceOut);
        

    }
    
    public String formatBandwidth(double bw){
        if (bw >= 1000){
            return numFormat.format(bw/1000) + " Gbit/s";
        } else if (bw < 1) {
            return numFormat.format(bw*1000) + " Kbit/s";
        } else {
            return numFormat.format(bw) + " Mbit/s";
        }
        
    }

    
    // <editor-fold defaultstate="collapsed" desc="Generated Code">//GEN-BEGIN:initComponents
    private void initComponents() {

        capacityLabel = new javax.swing.JLabel();
        typeLabel = new javax.swing.JLabel();
        bandwidthLabel = new javax.swing.JLabel();
        capacity = new javax.swing.JLabel();
        type = new javax.swing.JLabel();
        interfaceInLabel = new javax.swing.JLabel();
        interfaceOutLabel = new javax.swing.JLabel();
        interfaceIn = new javax.swing.JLabel();
        interfaceOut = new javax.swing.JLabel();
        fromLabel = new javax.swing.JLabel();
        toLabel = new javax.swing.JLabel();
        fromValue = new javax.swing.JLabel();
        toValue = new javax.swing.JLabel();
        bwInLabel = new javax.swing.JLabel();
        bwOutLabel = new javax.swing.JLabel();
        bwInValue = new javax.swing.JLabel();
        bwOutValue = new javax.swing.JLabel();

        setBackground(new java.awt.Color(236, 237, 237));
        setBorder(javax.swing.BorderFactory.createEmptyBorder(1, 1, 1, 1));

        capacityLabel.setFont(new java.awt.Font("DejaVu Sans", 1, 12)); // NOI18N
        capacityLabel.setText("Capacity:");

        typeLabel.setFont(new java.awt.Font("DejaVu Sans", 1, 12)); // NOI18N
        typeLabel.setText("Type:");

        bandwidthLabel.setFont(new java.awt.Font("DejaVu Sans", 1, 12)); // NOI18N
        bandwidthLabel.setText("Bandwidth usage:");

        capacity.setFont(new java.awt.Font("DejaVu Sans", 0, 12)); // NOI18N
        capacity.setText("capacity");

        type.setFont(new java.awt.Font("DejaVu Sans", 0, 12)); // NOI18N
        type.setText("type");

        interfaceInLabel.setFont(new java.awt.Font("DejaVu Sans", 1, 12)); // NOI18N
        interfaceInLabel.setText("Interface in:");

        interfaceOutLabel.setFont(new java.awt.Font("DejaVu Sans", 1, 12)); // NOI18N
        interfaceOutLabel.setText("Interface out:");

        interfaceIn.setFont(new java.awt.Font("DejaVu Sans", 0, 12)); // NOI18N
        interfaceIn.setText("jLabel3");

        interfaceOut.setFont(new java.awt.Font("DejaVu Sans", 0, 12)); // NOI18N
        interfaceOut.setText("jLabel4");

        fromLabel.setFont(new java.awt.Font("DejaVu Sans", 1, 12)); // NOI18N
        fromLabel.setText("From:");

        toLabel.setFont(new java.awt.Font("DejaVu Sans", 1, 12)); // NOI18N
        toLabel.setText("To:");

        fromValue.setFont(new java.awt.Font("DejaVu Sans", 0, 12)); // NOI18N
        fromValue.setText("jLabel3");

        toValue.setFont(new java.awt.Font("DejaVu Sans", 0, 12)); // NOI18N
        toValue.setText("jLabel4");

        bwInLabel.setFont(new java.awt.Font("DejaVu Sans", 1, 12)); // NOI18N
        bwInLabel.setText("In:");

        bwOutLabel.setFont(new java.awt.Font("DejaVu Sans", 1, 12)); // NOI18N
        bwOutLabel.setText("Out:");

        bwInValue.setFont(new java.awt.Font("DejaVu Sans", 0, 12)); // NOI18N
        bwInValue.setText("jLabel3");

        bwOutValue.setFont(new java.awt.Font("DejaVu Sans", 0, 12)); // NOI18N
        bwOutValue.setText("jLabel4");

        org.jdesktop.layout.GroupLayout layout = new org.jdesktop.layout.GroupLayout(this);
        this.setLayout(layout);
        layout.setHorizontalGroup(
            layout.createParallelGroup(org.jdesktop.layout.GroupLayout.LEADING)
            .add(layout.createSequentialGroup()
                .addContainerGap()
                .add(layout.createParallelGroup(org.jdesktop.layout.GroupLayout.LEADING, false)
                    .add(layout.createSequentialGroup()
                        .add(fromLabel)
                        .addPreferredGap(org.jdesktop.layout.LayoutStyle.RELATED)
                        .add(fromValue)
                        .addPreferredGap(org.jdesktop.layout.LayoutStyle.RELATED, org.jdesktop.layout.GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE))
                    .add(layout.createSequentialGroup()
                        .add(layout.createParallelGroup(org.jdesktop.layout.GroupLayout.TRAILING)
                            .add(org.jdesktop.layout.GroupLayout.LEADING, toLabel)
                            .add(org.jdesktop.layout.GroupLayout.LEADING, capacityLabel)
                            .add(org.jdesktop.layout.GroupLayout.LEADING, typeLabel)
                            .add(org.jdesktop.layout.GroupLayout.LEADING, bandwidthLabel))
                        .addPreferredGap(org.jdesktop.layout.LayoutStyle.RELATED)
                        .add(layout.createParallelGroup(org.jdesktop.layout.GroupLayout.LEADING)
                            .add(toValue)
                            .add(capacity)
                            .add(type)))
                    .add(layout.createSequentialGroup()
                        .add(layout.createParallelGroup(org.jdesktop.layout.GroupLayout.LEADING)
                            .add(interfaceInLabel)
                            .add(interfaceOutLabel))
                        .addPreferredGap(org.jdesktop.layout.LayoutStyle.RELATED)
                        .add(layout.createParallelGroup(org.jdesktop.layout.GroupLayout.LEADING, false)
                            .add(interfaceOut, org.jdesktop.layout.GroupLayout.DEFAULT_SIZE, org.jdesktop.layout.GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE)
                            .add(interfaceIn, org.jdesktop.layout.GroupLayout.DEFAULT_SIZE, org.jdesktop.layout.GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE)))
                    .add(layout.createSequentialGroup()
                        .add(12, 12, 12)
                        .add(layout.createParallelGroup(org.jdesktop.layout.GroupLayout.LEADING)
                            .add(bwInLabel)
                            .add(layout.createSequentialGroup()
                                .add(bwOutLabel)
                                .addPreferredGap(org.jdesktop.layout.LayoutStyle.RELATED, org.jdesktop.layout.GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE)))
                        .addPreferredGap(org.jdesktop.layout.LayoutStyle.RELATED)
                        .add(layout.createParallelGroup(org.jdesktop.layout.GroupLayout.LEADING)
                            .add(bwInValue)
                            .add(bwOutValue))
                        .add(75, 75, 75)))
                .addContainerGap(54, Short.MAX_VALUE))
        );

        layout.linkSize(new java.awt.Component[] {bwInLabel, bwOutLabel}, org.jdesktop.layout.GroupLayout.HORIZONTAL);

        layout.linkSize(new java.awt.Component[] {bandwidthLabel, capacityLabel, fromLabel, interfaceInLabel, interfaceOutLabel, toLabel, typeLabel}, org.jdesktop.layout.GroupLayout.HORIZONTAL);

        layout.linkSize(new java.awt.Component[] {capacity, fromValue, interfaceIn, interfaceOut, toValue, type}, org.jdesktop.layout.GroupLayout.HORIZONTAL);

        layout.setVerticalGroup(
            layout.createParallelGroup(org.jdesktop.layout.GroupLayout.LEADING)
            .add(layout.createSequentialGroup()
                .add(layout.createParallelGroup(org.jdesktop.layout.GroupLayout.LEADING)
                    .add(layout.createSequentialGroup()
                        .addContainerGap()
                        .add(layout.createParallelGroup(org.jdesktop.layout.GroupLayout.BASELINE)
                            .add(fromLabel)
                            .add(fromValue))
                        .addPreferredGap(org.jdesktop.layout.LayoutStyle.RELATED)
                        .add(layout.createParallelGroup(org.jdesktop.layout.GroupLayout.BASELINE)
                            .add(toLabel)
                            .add(toValue))
                        .addPreferredGap(org.jdesktop.layout.LayoutStyle.RELATED)
                        .add(layout.createParallelGroup(org.jdesktop.layout.GroupLayout.BASELINE)
                            .add(capacityLabel)
                            .add(capacity))
                        .addPreferredGap(org.jdesktop.layout.LayoutStyle.RELATED)
                        .add(layout.createParallelGroup(org.jdesktop.layout.GroupLayout.BASELINE)
                            .add(typeLabel)
                            .add(type))
                        .addPreferredGap(org.jdesktop.layout.LayoutStyle.RELATED)
                        .add(bandwidthLabel)
                        .addPreferredGap(org.jdesktop.layout.LayoutStyle.RELATED)
                        .add(layout.createParallelGroup(org.jdesktop.layout.GroupLayout.BASELINE)
                            .add(bwInLabel)
                            .add(bwInValue)))
                    .add(layout.createSequentialGroup()
                        .add(138, 138, 138)
                        .add(layout.createParallelGroup(org.jdesktop.layout.GroupLayout.BASELINE)
                            .add(bwOutLabel)
                            .add(bwOutValue))))
                .addPreferredGap(org.jdesktop.layout.LayoutStyle.RELATED)
                .add(layout.createParallelGroup(org.jdesktop.layout.GroupLayout.BASELINE)
                    .add(interfaceInLabel)
                    .add(interfaceIn))
                .addPreferredGap(org.jdesktop.layout.LayoutStyle.RELATED)
                .add(layout.createParallelGroup(org.jdesktop.layout.GroupLayout.BASELINE)
                    .add(interfaceOutLabel)
                    .add(interfaceOut))
                .addContainerGap(16, Short.MAX_VALUE))
        );

        layout.linkSize(new java.awt.Component[] {bandwidthLabel, capacityLabel, fromLabel, interfaceInLabel, interfaceOutLabel, toLabel, typeLabel}, org.jdesktop.layout.GroupLayout.VERTICAL);

        layout.linkSize(new java.awt.Component[] {capacity, fromValue, interfaceIn, interfaceOut, toValue, type}, org.jdesktop.layout.GroupLayout.VERTICAL);

        layout.linkSize(new java.awt.Component[] {bwInLabel, bwOutLabel}, org.jdesktop.layout.GroupLayout.VERTICAL);

    }// </editor-fold>//GEN-END:initComponents
    
    
    // Variables declaration - do not modify//GEN-BEGIN:variables
    private javax.swing.JLabel bandwidthLabel;
    private javax.swing.JLabel bwInLabel;
    private javax.swing.JLabel bwInValue;
    private javax.swing.JLabel bwOutLabel;
    private javax.swing.JLabel bwOutValue;
    private javax.swing.JLabel capacity;
    private javax.swing.JLabel capacityLabel;
    private javax.swing.JLabel fromLabel;
    private javax.swing.JLabel fromValue;
    private javax.swing.JLabel interfaceIn;
    private javax.swing.JLabel interfaceInLabel;
    private javax.swing.JLabel interfaceOut;
    private javax.swing.JLabel interfaceOutLabel;
    private javax.swing.JLabel toLabel;
    private javax.swing.JLabel toValue;
    private javax.swing.JLabel type;
    private javax.swing.JLabel typeLabel;
    // End of variables declaration//GEN-END:variables
    
}
