package no.uninett.nav.window;

import java.applet.*;
import java.awt.*;
import java.awt.event.*;
import java.net.*;
import javax.swing.*;
import javax.swing.border.*;

public class netboxTooltip extends JPanel {

	private JLabel sysnameLabel;
	private JLabel sysnameValue;
	private JLabel categoryLabel;
	private JLabel categoryValue;
	private JLabel typeLabel;
	private JLabel typeValue;
	private JLabel roomLabel;
	private JLabel roomValue;
	private JLabel cpuLabel;
	private JLabel cpuValue;
	private JButton ipdevinfoLink;
	private String ipdevinfoUrl;

	public netboxTooltip() {
		initComponents();
	}

	public netboxTooltip(String sysname, String category, String type, String room, String ipdevinfoUrl, String cpuload){
		initComponents();
		sysnameValue.setText(sysname);
		categoryValue.setText(category);
		typeValue.setText(type);
		roomValue.setText(room);
		cpuValue.setText(cpuload);
		this.ipdevinfoUrl = ipdevinfoUrl;
	}

	public JLabel getSysnameValue() {
		return sysnameValue;
	}

	private ActionListener linkClickHandler = new ActionListener() {
		public void actionPerformed(ActionEvent arg){
			try {
				AppletContext ac = no.uninett.nav.netmap.Main._getAppletContext();
				String path = no.uninett.nav.netmap.Main.getBaseURL().toString();
				path = path.substring(0,path.length()-7);
				URL url = new URL(path + ipdevinfoUrl);
				ac.showDocument(url, "_blank");
			} catch (Exception e){
				System.out.println("Could not open link with error" + e.getMessage());
			}
		}
	};


	private void initComponents() {
		sysnameLabel = new JLabel();
		sysnameValue = new JLabel();
		categoryLabel = new JLabel();
		categoryValue = new JLabel();
		typeLabel = new JLabel();
		typeValue = new JLabel();
		roomLabel = new JLabel();
		roomValue = new JLabel();
		cpuLabel = new JLabel();
		cpuValue = new JLabel();
		ipdevinfoLink = new JButton("View in IP Device Info");
		ipdevinfoLink.addActionListener(linkClickHandler);

		setBorder(new LineBorder(new Color(33, 33, 33), 1, true));

		setLayout(new GridBagLayout());
		((GridBagLayout)getLayout()).columnWidths = new int[] {0, 0, 0};
		((GridBagLayout)getLayout()).rowHeights = new int[] {0, 0, 0, 0, 0, 0};
		((GridBagLayout)getLayout()).columnWeights = new double[] {0.0, 1.0, 1.0E-4};
		((GridBagLayout)getLayout()).rowWeights = new double[] {0.0, 0.0, 0.0, 0.0, 0.0, 1.0E-4};

		sysnameLabel.setText("Sysname:");
		sysnameLabel.setFont(sysnameLabel.getFont().deriveFont(Font.BOLD));
		add(sysnameLabel, new GridBagConstraints(0, 0, 1, 1, 0.0, 0.0,
			GridBagConstraints.CENTER, GridBagConstraints.BOTH,
			new Insets(0, 10, 5, 5), 0, 0));

		sysnameValue.setText("");
		sysnameValue.setHorizontalAlignment(SwingConstants.LEFT);
		add(sysnameValue, new GridBagConstraints(1, 0, 1, 1, 0.0, 0.0,
			GridBagConstraints.CENTER, GridBagConstraints.BOTH,
			new Insets(0, 10, 5, 10), 0, 0));

		categoryLabel.setText("Category:");
		categoryLabel.setFont(categoryLabel.getFont().deriveFont(Font.BOLD));
		add(categoryLabel, new GridBagConstraints(0, 1, 1, 1, 0.0, 0.0,
			GridBagConstraints.CENTER, GridBagConstraints.BOTH,
			new Insets(0, 10, 5, 5), 0, 0));

		categoryValue.setText("");
		add(categoryValue, new GridBagConstraints(1, 1, 1, 1, 0.0, 0.0,
			GridBagConstraints.CENTER, GridBagConstraints.BOTH,
			new Insets(0, 10, 5, 10), 0, 0));

		typeLabel.setText("Type:");
		typeLabel.setFont(typeLabel.getFont().deriveFont(Font.BOLD));
		add(typeLabel, new GridBagConstraints(0, 2, 1, 1, 0.0, 0.0,
			GridBagConstraints.CENTER, GridBagConstraints.BOTH,
			new Insets(0, 10, 5, 5), 0, 0));

		typeValue.setText("");
		add(typeValue, new GridBagConstraints(1, 2, 1, 1, 0.0, 0.0,
			GridBagConstraints.CENTER, GridBagConstraints.BOTH,
			new Insets(0, 10, 5, 10), 0, 0));

		roomLabel.setText("Room:");
		roomLabel.setFont(roomLabel.getFont().deriveFont(Font.BOLD));
		add(roomLabel, new GridBagConstraints(0, 3, 1, 1, 0.0, 0.0,
			GridBagConstraints.CENTER, GridBagConstraints.BOTH,
			new Insets(0, 10, 5, 5), 0, 0));

		roomValue.setText("");
		add(roomValue, new GridBagConstraints(1, 3, 1, 1, 0.0, 0.0,
			GridBagConstraints.CENTER, GridBagConstraints.BOTH,
			new Insets(0, 10, 5, 10), 0, 0));

		cpuLabel.setText("CPU Load:");
		cpuLabel.setFont(cpuLabel.getFont().deriveFont(Font.BOLD));
		add(cpuLabel, new GridBagConstraints(0, 4, 1, 1, 0.0, 0.0,
			GridBagConstraints.CENTER, GridBagConstraints.BOTH,
			new Insets(0, 10, 0, 5), 0, 0));

		cpuValue.setText("");
		add(cpuValue, new GridBagConstraints(1, 4, 1, 1, 0.0, 0.0,
			GridBagConstraints.CENTER, GridBagConstraints.BOTH,
			new Insets(0, 10, 0, 10), 0, 0));

		add(ipdevinfoLink, new GridBagConstraints(0, 5, 2, 1, 0.0, 0.0,
			GridBagConstraints.CENTER, GridBagConstraints.BOTH,
			new Insets(0, 10, 0, 5), 0, 0));
	}
}
