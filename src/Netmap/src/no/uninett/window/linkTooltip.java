/**
 * Copyright 2007 UNINETT AS
 *
 * This file is part of Network Administration Visualized (NAV)
 *
 * NAV is free software;you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation;either version 2 of the License, or
 * (at your option) any later version.
 *
 * NAV is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY;without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with NAV;if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 *
 * Authors: Kristian Klette <klette@samfundet.no>
 *
 */
package no.uninett.window;

import java.text.DecimalFormat;
import java.text.NumberFormat;
import javax.swing.JLabel;

public class linkTooltip extends javax.swing.JPanel {

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

    public NumberFormat numFormat = new DecimalFormat("0.00");

    public linkTooltip(String link, String capacity, String bwIn, String bwOut, String type,
                         String interfaceIn, String interfaceOut){

        this.capacityLabel = new javax.swing.JLabel();
       this.typeLabel = new javax.swing.JLabel();
        this.bandwidthLabel = new javax.swing.JLabel();
        this.capacity = new javax.swing.JLabel();
        this.type = new javax.swing.JLabel();
        this.interfaceInLabel = new javax.swing.JLabel();
        this.interfaceOutLabel = new javax.swing.JLabel();
        this.interfaceIn = new javax.swing.JLabel();
        this.interfaceOut = new javax.swing.JLabel();
        this.fromLabel = new javax.swing.JLabel();
        this.toLabel = new javax.swing.JLabel();
        this.fromValue = new javax.swing.JLabel();
        this.toValue = new javax.swing.JLabel();
        this.bwInLabel = new javax.swing.JLabel();
        this.bwOutLabel = new javax.swing.JLabel();
        this.bwInValue = new javax.swing.JLabel();
        this.bwOutValue = new javax.swing.JLabel();

        setBackground(new java.awt.Color(236, 237, 237));
        setBorder(javax.swing.BorderFactory.createEmptyBorder(1, 1, 1, 1));

        this.capacityLabel.setFont(new java.awt.Font("DejaVu Sans", 1, 12));
        this.capacityLabel.setText("Capacity:");

        this.typeLabel.setFont(new java.awt.Font("DejaVu Sans", 1, 12));
        this.typeLabel.setText("Type:");

        this.bandwidthLabel.setFont(new java.awt.Font("DejaVu Sans", 1, 12));
        this.bandwidthLabel.setText("Bandwidth usage:");

        this.capacity.setFont(new java.awt.Font("DejaVu Sans", 0, 12));
        this.capacity.setText("capacity");

        this.type.setFont(new java.awt.Font("DejaVu Sans", 0, 12));
        this.type.setText("type");

        this.interfaceInLabel.setFont(new java.awt.Font("DejaVu Sans", 1, 12));
        this.interfaceInLabel.setText("Interface in:");

        this.interfaceOutLabel.setFont(new java.awt.Font("DejaVu Sans", 1, 12));
        this.interfaceOutLabel.setText("Interface out:");

        this.interfaceIn.setFont(new java.awt.Font("DejaVu Sans", 0, 12));
        this.interfaceIn.setText("jLabel3");

        this.interfaceOut.setFont(new java.awt.Font("DejaVu Sans", 0, 12));
        this.interfaceOut.setText("jLabel4");

        this.fromLabel.setFont(new java.awt.Font("DejaVu Sans", 1, 12));
        this.fromLabel.setText("From:");

        this.toLabel.setFont(new java.awt.Font("DejaVu Sans", 1, 12));
        this.toLabel.setText("To:");

        this.fromValue.setFont(new java.awt.Font("DejaVu Sans", 0, 12));
        this.fromValue.setText("jLabel3");

        this.toValue.setFont(new java.awt.Font("DejaVu Sans", 0, 12));
        this.toValue.setText("jLabel4");

        this.bwInLabel.setFont(new java.awt.Font("DejaVu Sans", 1, 12));
        this.bwInLabel.setText("In:");

        this.bwOutLabel.setFont(new java.awt.Font("DejaVu Sans", 1, 12));
        this.bwOutLabel.setText("Out:");

        this.bwInValue.setFont(new java.awt.Font("DejaVu Sans", 0, 12));
        this.bwInValue.setText("jLabel3");

        this.bwOutValue.setFont(new java.awt.Font("DejaVu Sans", 0, 12));
        this.bwOutValue.setText("jLabel4");

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
}
