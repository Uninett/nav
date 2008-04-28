
package no.uninett.window;

import java.awt.*;
import javax.swing.*;
import javax.swing.border.*;

public class linkTooltip extends JPanel {

	private JLabel linkLabel;
	private JLabel linkValue;
	private JLabel interfacesLabel;
	private JLabel interfacesValue;
	private JLabel netidentLabel;
	private JLabel netidentValue;
	private JLabel capacityLabel;
	private JLabel capacityValue;
	private JLabel loadLabel;
	private JLabel loadValue;

	public linkTooltip() {
		initComponents();
	}

	public linkTooltip(String link, String interfaces, String netident,
		String capacity, String load){
		initComponents();
		this.linkValue.setText(link);
		this.interfacesValue.setText(interfaces);
		this.netidentValue.setText(netident);
		this.capacityValue.setText(capacity);
		this.loadValue.setText(load);
	}

	private void initComponents() {
		linkLabel = new JLabel();
		linkValue = new JLabel();
		interfacesLabel = new JLabel();
		interfacesValue = new JLabel();
		netidentLabel = new JLabel();
		netidentValue = new JLabel();
		capacityLabel = new JLabel();
		capacityValue = new JLabel();
		loadLabel = new JLabel();
		loadValue = new JLabel();

		setBorder(new LineBorder(new Color(33, 33, 33), 1, true));

		setLayout(new GridBagLayout());
		((GridBagLayout)getLayout()).columnWidths = new int[] {0, 0, 0};
		((GridBagLayout)getLayout()).rowHeights = new int[] {0, 0, 0, 0, 0, 0};
		((GridBagLayout)getLayout()).columnWeights = new double[] {0.0, 1.0, 1.0E-4};
		((GridBagLayout)getLayout()).rowWeights = new double[] {0.0, 0.0, 0.0, 0.0, 0.0, 1.0E-4};

		linkLabel.setText("Link:");
		linkLabel.setFont(linkLabel.getFont().deriveFont(linkLabel.getFont().getStyle() | Font.BOLD));
		add(linkLabel, new GridBagConstraints(0, 0, 1, 1, 0.0, 0.0,
			GridBagConstraints.CENTER, GridBagConstraints.BOTH,
			new Insets(0, 10, 5, 5), 0, 0));

		linkValue.setText("text");
		add(linkValue, new GridBagConstraints(1, 0, 1, 1, 0.0, 0.0,
			GridBagConstraints.CENTER, GridBagConstraints.BOTH,
			new Insets(0, 10, 5, 10), 0, 0));

		interfacesLabel.setText("Interfaces:");
		interfacesLabel.setFont(interfacesLabel.getFont().deriveFont(interfacesLabel.getFont().getStyle() | Font.BOLD));
		add(interfacesLabel, new GridBagConstraints(0, 1, 1, 1, 0.0, 0.0,
			GridBagConstraints.CENTER, GridBagConstraints.BOTH,
			new Insets(0, 10, 5, 5), 0, 0));

		interfacesValue.setText("text");
		add(interfacesValue, new GridBagConstraints(1, 1, 1, 1, 0.0, 0.0,
			GridBagConstraints.CENTER, GridBagConstraints.BOTH,
			new Insets(0, 10, 5, 10), 0, 0));

		netidentLabel.setText("Net ident:");
		netidentLabel.setFont(netidentLabel.getFont().deriveFont(netidentLabel.getFont().getStyle() | Font.BOLD));
		add(netidentLabel, new GridBagConstraints(0, 2, 1, 1, 0.0, 0.0,
			GridBagConstraints.CENTER, GridBagConstraints.BOTH,
			new Insets(0, 10, 5, 5), 0, 0));

		netidentValue.setText("text");
		add(netidentValue, new GridBagConstraints(1, 2, 1, 1, 0.0, 0.0,
			GridBagConstraints.CENTER, GridBagConstraints.BOTH,
			new Insets(0, 10, 5, 10), 0, 0));

		capacityLabel.setText("Capacity:");
		capacityLabel.setFont(capacityLabel.getFont().deriveFont(capacityLabel.getFont().getStyle() | Font.BOLD));
		add(capacityLabel, new GridBagConstraints(0, 3, 1, 1, 0.0, 0.0,
			GridBagConstraints.CENTER, GridBagConstraints.BOTH,
			new Insets(0, 10, 5, 5), 0, 0));

		capacityValue.setText("text");
		add(capacityValue, new GridBagConstraints(1, 3, 1, 1, 0.0, 0.0,
			GridBagConstraints.CENTER, GridBagConstraints.BOTH,
			new Insets(0, 10, 5, 10), 0, 0));

		loadLabel.setText("Load:");
		loadLabel.setFont(loadLabel.getFont().deriveFont(loadLabel.getFont().getStyle() | Font.BOLD));
		add(loadLabel, new GridBagConstraints(0, 4, 1, 1, 0.0, 0.0,
			GridBagConstraints.CENTER, GridBagConstraints.BOTH,
			new Insets(0, 10, 0, 5), 0, 0));

		loadValue.setText("text");
		add(loadValue, new GridBagConstraints(1, 4, 1, 1, 0.0, 0.0,
			GridBagConstraints.CENTER, GridBagConstraints.BOTH,
			new Insets(0, 10, 0, 10), 0, 0));
	}

}
