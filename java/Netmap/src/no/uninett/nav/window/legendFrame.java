package no.uninett.nav.window;

public class legendFrame extends javax.swing.JFrame {

    private javax.swing.JLabel highLoad;
    private javax.swing.JCheckBox jCheckBox1;
    private javax.swing.JSeparator jSeparator1;
    private javax.swing.JLabel legendTitle;
    private javax.swing.JLabel lowLoad;
    private javax.swing.JLabel lowMedLoad;
    private javax.swing.JLabel medHighLoad;
    private javax.swing.JLabel medLoad;

    public legendFrame() {
        initComponents();
    }
    @SuppressWarnings("unchecked")
    private void initComponents() {
        java.awt.GridBagConstraints gridBagConstraints;

        legendTitle = new javax.swing.JLabel();
        jSeparator1 = new javax.swing.JSeparator();
        lowLoad = new javax.swing.JLabel();
        lowMedLoad = new javax.swing.JLabel();
        medLoad = new javax.swing.JLabel();
        medHighLoad = new javax.swing.JLabel();
        highLoad = new javax.swing.JLabel();
        jCheckBox1 = new javax.swing.JCheckBox();

        setName("linkColorLegend");
        getContentPane().setLayout(new java.awt.GridBagLayout());

        legendTitle.setFont(legendTitle.getFont().deriveFont(legendTitle.getFont().getStyle() | java.awt.Font.BOLD, legendTitle.getFont().getSize()+4));
        legendTitle.setHorizontalAlignment(javax.swing.SwingConstants.CENTER);
        legendTitle.setText("Link color legend");
        legendTitle.setName("legendTitle");
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 0;
        gridBagConstraints.gridy = 0;
        gridBagConstraints.fill = java.awt.GridBagConstraints.HORIZONTAL;
        gridBagConstraints.insets = new java.awt.Insets(4, 4, 4, 4);
        getContentPane().add(legendTitle, gridBagConstraints);
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 0;
        gridBagConstraints.gridy = 1;
        gridBagConstraints.fill = java.awt.GridBagConstraints.HORIZONTAL;
        getContentPane().add(jSeparator1, gridBagConstraints);

        lowLoad.setBackground(new java.awt.Color(138, 226, 52));
        lowLoad.setHorizontalAlignment(javax.swing.SwingConstants.CENTER);
        lowLoad.setText("0-100Mbit/s");
        lowLoad.setBorder(new javax.swing.border.LineBorder(new java.awt.Color(0, 0, 0), 1, true));
        lowLoad.setDoubleBuffered(true);
        lowLoad.setName("lowLoad");
        lowLoad.setOpaque(true);
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 0;
        gridBagConstraints.gridy = 2;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.ipadx = 1;
        gridBagConstraints.insets = new java.awt.Insets(2, 2, 2, 2);
        getContentPane().add(lowLoad, gridBagConstraints);

        lowMedLoad.setBackground(new java.awt.Color(186, 252, 79));
        lowMedLoad.setHorizontalAlignment(javax.swing.SwingConstants.CENTER);
        lowMedLoad.setText("100-512Mbit/s");
        lowMedLoad.setBorder(new javax.swing.border.LineBorder(new java.awt.Color(0, 0, 0), 1, true));
        lowMedLoad.setDoubleBuffered(true);
        lowMedLoad.setName("lowMedLoad");
        lowMedLoad.setOpaque(true);
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 0;
        gridBagConstraints.gridy = 3;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.insets = new java.awt.Insets(2, 2, 2, 2);
        getContentPane().add(lowMedLoad, gridBagConstraints);

        medLoad.setBackground(new java.awt.Color(252, 233, 79));
        medLoad.setHorizontalAlignment(javax.swing.SwingConstants.CENTER);
        medLoad.setText("0.5-1Gbit/s");
        medLoad.setBorder(new javax.swing.border.LineBorder(new java.awt.Color(0, 0, 0), 1, true));
        medLoad.setDoubleBuffered(true);
        medLoad.setName("medLoad");
        medLoad.setOpaque(true);
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 0;
        gridBagConstraints.gridy = 4;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.insets = new java.awt.Insets(2, 2, 2, 2);
        getContentPane().add(medLoad, gridBagConstraints);

        medHighLoad.setBackground(new java.awt.Color(252, 175, 62));
        medHighLoad.setHorizontalAlignment(javax.swing.SwingConstants.CENTER);
        medHighLoad.setText("1-4Gbit/s");
        medHighLoad.setBorder(new javax.swing.border.LineBorder(new java.awt.Color(0, 0, 0), 1, true));
        medHighLoad.setDoubleBuffered(true);
        medHighLoad.setName("medHighLoad");
        medHighLoad.setOpaque(true);
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 0;
        gridBagConstraints.gridy = 5;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.insets = new java.awt.Insets(2, 2, 2, 2);
        getContentPane().add(medHighLoad, gridBagConstraints);

        highLoad.setBackground(new java.awt.Color(240, 0, 0));
        highLoad.setHorizontalAlignment(javax.swing.SwingConstants.CENTER);
        highLoad.setText("4Gbit/s +");
        highLoad.setBorder(new javax.swing.border.LineBorder(new java.awt.Color(0, 0, 0), 1, true));
        highLoad.setDoubleBuffered(true);
        highLoad.setName("highLoad");
        highLoad.setOpaque(true);
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 0;
        gridBagConstraints.gridy = 6;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.insets = new java.awt.Insets(2, 2, 2, 2);
        getContentPane().add(highLoad, gridBagConstraints);

        jCheckBox1.setText("Relative scale");
        jCheckBox1.addChangeListener(new javax.swing.event.ChangeListener() {
            public void stateChanged(javax.swing.event.ChangeEvent evt) {
                jCheckBox1StateChanged(evt);
            }
        });
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 0;
        gridBagConstraints.gridy = 7;
        gridBagConstraints.insets = new java.awt.Insets(4, 4, 4, 4);
        getContentPane().add(jCheckBox1, gridBagConstraints);

        pack();
    }

    private void jCheckBox1StateChanged(javax.swing.event.ChangeEvent evt) {
                if(jCheckBox1.isSelected()){
            highLoad.setText("90% - 100%");
            medHighLoad.setText("60% - 90%");
            medLoad.setText("40% - 60%");
            lowMedLoad.setText("20% - 40%");
            lowLoad.setText("0% - 20%");
        } else {
            lowLoad.setText("0-100Mbit/s");
            lowMedLoad.setText("100-512Mbit/s");
            medLoad.setText("0.5-1Gbit/s");
            medHighLoad.setText("1-4Gbit/s");
            highLoad.setText("4Gbit/s +");
        }
    }
}

