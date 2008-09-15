/*
 * $Id$ 
 *
 * Copyright 2000-2005 Norwegian University of Science and Technology
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
 *
 * Authors: Kristian Eide <kreide@gmail.com>
 */

import java.awt.Button;
import java.awt.Choice;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Label;
import java.awt.Panel;
import java.awt.TextField;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.ItemEvent;
import java.awt.event.ItemListener;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.Calendar;
import java.util.Date;
import java.util.GregorianCalendar;
import java.util.Vector;


class TopPanel extends Panel implements ItemListener,ActionListener
{
	/**
	 * 
	 */
	private static final long serialVersionUID = 1L;

	Com com;

	private TextField fraTid;
	private TextField fraDato;
	private Choice fraYear = new Choice();

	private TextField tilTid;
	private TextField tilDato;
	private Choice tilYear = new Choice();

	private Label errorLabel = new Label("                   ");


	boolean nettFinalized = false; // Nettnavn hentes fra server
	public boolean getNetFinalized() { return nettFinalized; }

	private Choice nett = new Choice();
	private Choice skala = new Choice();  // relativ||absolutt
	private Choice lastValg = new Choice(); // avg||max
	private Choice avgmax = new Choice();

	private int fraYearInt;
	private int tilYearInt;

	private boolean relativSkala;
	private boolean avg;

	private Button moveButton;
	private Button saveButton;

	public void addNettNavn(String navn)
	{
		if (nettFinalized) return;
		if (navn == null)
		{
			// Sorter listen
			Vector v = new Vector();
			for (int i = 0; i < nett.getItemCount(); i++) {
				v.addElement(nett.getItem(i));
			}
			nett.removeAll();
			Com.quickSort(v);

			for (int i = 0; i < v.size(); i++) {
				String s = (String)v.elementAt(i);
				if (s.startsWith("_")) s = s.substring(1, s.length());
				nett.addItem("" + s);
			}
			nett.addItem("");

			nett.addItemListener(com.getNet());
			nettFinalized = true;

		} else {
			nett.addItem(navn);
		}
	}
	public void setNettIndex(int i) { if (nett.getSelectedIndex()==i) return; nett.select(i); nett.transferFocus(); }
	public void setNettNavn(String navn) {
		if (!nettFinalized) return;

		if (nett.getSelectedItem().equals(navn)) return;
		nett.select(navn);
		nett.transferFocus();
	}

	public String getNettNavn(int i)
	{
		if (i >= 0 && i < nett.getItemCount()) return nett.getItem(i);
		return null;
	}

	public void showAdminButton() {
		com.d("Showing admin button", 5);
		moveButton.setVisible(true);
		saveButton.setVisible(true);
		setMsg("Data not saved");
		//validate();
	}

	public TopPanel(Com InCom)
	{
		com = InCom;

		Label fraLabel = new Label("  St time");
		Label tilLabel = new Label("  En time:");
		Label avgmaxLabel = new Label("  Load:");

		Button okButton = new Button("OK");
		moveButton = new Button("Move");
		saveButton = new Button("Save");
		moveButton.setVisible(false);
		saveButton.setVisible(false);

		Button refreshButton = new Button("Refresh");

		skala.addItem("Absolute scale");
		skala.addItem("Relative scale");

		lastValg.addItem("Avg. last 5 min");
		lastValg.addItem("Avg. last 1h");
		lastValg.addItem("Avg. last 24h");
		lastValg.addItem("Max last 2h");
		lastValg.addItem("Max last 24h");
		lastValg.addItem("Manual");

		avgmax.addItem("Avg");
		avgmax.addItem("Max");

		fraTid = new TextField("HH:MM"); fraTid.setColumns(4);
		fraDato = new TextField("DD/MM"); fraDato.setColumns(4);

		tilTid = new TextField("HH:MM"); tilTid.setColumns(4);
		tilDato = new TextField("DD/MM"); tilDato.setColumns(4);

		// Insert this year + last year
		// Get current year
		Calendar calendar = new GregorianCalendar();
		SimpleDateFormat yearFormat = new SimpleDateFormat("yyyy");
		int year = Integer.parseInt(yearFormat.format(calendar.getTime()));
		for (int i = year-1; i <= year; i++) { fraYear.addItem(""+i); tilYear.addItem(""+i); }


		// jepp, gridbag må til
		GridBagLayout gridbag = new GridBagLayout();
		setLayout(gridbag);
		GridBagConstraints c = new GridBagConstraints();
		c.fill = GridBagConstraints.HORIZONTAL;
		c.anchor = GridBagConstraints.NORTH;

		// Nettnavn
		c.weightx = 0; c.weighty = 0;
		c.gridx = 1; c.gridy = 0; c.gridwidth = 3; c.gridheight = 1;
		gridbag.setConstraints(nett, c);
		add(nett, c);

		// Skala
		c.weightx = 0; c.weighty = 0;
		c.gridx = 1; c.gridy = 1; c.gridwidth = 3; c.gridheight = 1;
		gridbag.setConstraints(skala, c);
		add(skala, c);

		// lastValg
		c.weightx = 0; c.weighty = 0;
		c.gridx = 1; c.gridy = 2; c.gridwidth = 3; c.gridheight = 1;
		gridbag.setConstraints(lastValg, c);
		add(lastValg, c);

		// fraLabel
		c.weightx = 0; c.weighty = 0;
		c.gridx = 1; c.gridy = 3; c.gridwidth = 1; c.gridheight = 1;
		gridbag.setConstraints(fraLabel, c);
		add(fraLabel, c);
		// fraTid
		c.weightx = 0; c.weighty = 0;
		c.gridx = 2; c.gridy = 3; c.gridwidth = 1; c.gridheight = 1;
		gridbag.setConstraints(fraTid, c);
		add(fraTid, c);

		// fraDato
		c.weightx = 0; c.weighty = 0;
		c.gridx = 1; c.gridy = 4; c.gridwidth = 1; c.gridheight = 1;
		gridbag.setConstraints(fraDato, c);
		add(fraDato, c);
		// fraYear
		c.weightx = 0; c.weighty = 0;
		c.gridx = 2; c.gridy = 4; c.gridwidth = 1; c.gridheight = 1;
		gridbag.setConstraints(fraYear, c);
		add(fraYear, c);


		// tilLabel
		c.weightx = 0; c.weighty = 0;
		c.gridx = 1; c.gridy = 5; c.gridwidth = 1; c.gridheight = 1;
		gridbag.setConstraints(tilLabel, c);
		add(tilLabel, c);
		// tilTid
		c.weightx = 0; c.weighty = 0;
		c.gridx = 2; c.gridy = 5; c.gridwidth = 1; c.gridheight = 1;
		gridbag.setConstraints(tilTid, c);
		add(tilTid, c);

		// tilDato
		c.weightx = 0; c.weighty = 0;
		c.gridx = 1; c.gridy = 6; c.gridwidth = 1; c.gridheight = 1;
		gridbag.setConstraints(tilDato, c);
		add(tilDato, c);
		// fraYear
		c.weightx = 0; c.weighty = 0;
		c.gridx = 2; c.gridy = 6; c.gridwidth = 1; c.gridheight = 1;
		gridbag.setConstraints(tilYear, c);
		add(tilYear, c);

		// avgmaxLabel
		c.weightx = 0.0; c.weighty = 0.0;
		c.gridx = 1; c.gridy = 7; c.gridwidth = 1; c.gridheight = 1;
		gridbag.setConstraints(avgmaxLabel, c);
		add(avgmaxLabel, c);

		// avgmax
		c.weightx = 0.0; c.weighty = 0;
		c.gridx = 2; c.gridy = 7; c.gridwidth = 1; c.gridheight = 1;
		gridbag.setConstraints(avgmax, c);
		add(avgmax, c);

		// okButton
		c.fill = GridBagConstraints.NONE;
		c.weightx = 0.0; c.weighty = 1;
		c.gridx = 1; c.gridy = 8; c.gridwidth = 1; c.gridheight = 1;
		gridbag.setConstraints(okButton, c);
		add(okButton, c);

		// okButton
		c.fill = GridBagConstraints.NONE;
		c.weightx = 0.0; c.weighty = 1;
		c.gridx = 2; c.gridy = 8; c.gridwidth = 1; c.gridheight = 1;
		gridbag.setConstraints(refreshButton, c);
		add(refreshButton, c);

		// adminButton
		c.fill = GridBagConstraints.NONE;
		c.weightx = 0.0; c.weighty = 1;
		c.gridx = 1; c.gridy = 9; c.gridwidth = 1; c.gridheight = 1;
		gridbag.setConstraints(moveButton, c);
		add(moveButton, c);

		// adminButton
		c.fill = GridBagConstraints.NONE;
		c.weightx = 0.0; c.weighty = 1;
		c.gridx = 2; c.gridy = 9; c.gridwidth = 1; c.gridheight = 1;
		gridbag.setConstraints(saveButton, c);
		add(saveButton, c);

		// errorLabel
		c.weightx = 0; c.weighty = 1;
		c.gridx = 1; c.gridy = 10; c.gridwidth = 2; c.gridheight = 1;
		gridbag.setConstraints(errorLabel, c);
		add(errorLabel, c);

		// itemListener
		skala.addItemListener(this);
		lastValg.addItemListener(this);
		fraYear.addItemListener(this);
		tilYear.addItemListener(this);

		// acionListeners
		okButton.addActionListener(this);
		refreshButton.addActionListener(new ActionListener() {
				public void actionPerformed(ActionEvent e) {
					com.getNet().refreshNettel(true);
				}
			});				

		AdminListener al = new AdminListener(com);
		al.setMoveMode(moveButton);
		al.setSaveBoksXY(saveButton);
		moveButton.addActionListener(al);
		saveButton.addActionListener(al);

		itemStateChanged(new ItemEvent(lastValg, ItemEvent.SELECTED, lastValg, ItemEvent.SELECTED) );
	}

	private void recalcFields()
	{
		com.d("Recalc all time-fields", 3);

		// Get current time
		Calendar calendar = new GregorianCalendar();
		Date currentTime = calendar.getTime();

		// Parse the date into a string
		SimpleDateFormat tidFormat = new SimpleDateFormat("HH:mm");
		String tid = tidFormat.format(currentTime);

		SimpleDateFormat datoFormat = new SimpleDateFormat("dd/MM");
		String dato = datoFormat.format(currentTime);

		SimpleDateFormat yearFormat = new SimpleDateFormat("yyyy");
		String year = yearFormat.format(currentTime);

		tilTid.setText(tid);
		tilDato.setText(dato);
		tilYear.select(year);

		long[] lastInterval = com.getLastInterval();
		com.d("   Rolling back: " + lastInterval[0] + " seconds.", 3);

		Date beginInterval = new Date(currentTime.getTime() + (lastInterval[0]*1000));
		com.setBeginLastDate(beginInterval);
		com.setEndLastDate(currentTime);

		com.d("     beginInterval: " + beginInterval, 4);
		com.d("     endInterval  : " + currentTime, 4);


		tid = tidFormat.format(beginInterval);
		dato = datoFormat.format(beginInterval);
		year = yearFormat.format(beginInterval);

		fraTid.setText(tid);
		fraDato.setText(dato);
		fraYear.select(year);

		if (com.getNet() != null)
		{
			com.getNet().setNeedReset(true);
			com.getNet().refreshNettel();

		}
	}

	public void itemStateChanged(ItemEvent e)
	{
		if (e.getSource() == fraYear)
		{
			String s = fraYear.getSelectedItem();
			fraYearInt = Integer.parseInt(s);
		} else
		if (e.getSource() == tilYear)
		{
			String s = tilYear.getSelectedItem();
			tilYearInt = Integer.parseInt(s);
		} else
		if (e.getSource() == skala)
		{
			String s = skala.getSelectedItem();
			relativSkala = (s.equals("Relative scale")) ? true : false;
			com.setRelativSkala(relativSkala);
			int sk = (relativSkala) ? LastColor.RELATIV_SKALA : LastColor.ABSOLUTT_SKALA;
			LastColor.setSkala(sk);
			com.getLogo().repaint();
			com.getNet().recalcLinks();
			com.getNet().repaint();

		} else
		if (e.getSource() == avgmax)
		{
			String s = avgmax.getSelectedItem();
			avg = (s.equals("Avg")) ? true : false;
			com.setTidAvg(avg);

		} else
		{
			Choice lastValg = (Choice)e.getSource();
			String s = lastValg.getSelectedItem();
			if (s.equals("Manuel")) return;

			long[] lastTid = new long[2];
			lastTid[1] = 0;
			com.setTidAvg(true);

			if (s.equals("Avg. last 5 min"))
			{
				lastTid[0] = -5 * 60;
				avgmax.select("Avg");
			} else
			if (s.equals("Avg. last 1h"))
			{
				lastTid[0] = -1 * 60 * 60;
				avgmax.select("Avg");
			} else
			if (s.equals("Avg. last 24h"))
			{
				lastTid[0] = -24 * 60 * 60;
				avgmax.select("Avg");
			} else
			if (s.equals("Max last 2h"))
			{
				lastTid[0] = -2 * 60 * 60;
				com.setTidAvg(false);
				avgmax.select("Maks");
			} else
			if (s.equals("Max last 24h"))
			{
				lastTid[0] = -24 * 60 * 60;
				com.setTidAvg(false);
				avgmax.select("Max");
			}

			com.setLastInterval(lastTid);
			recalcFields();
		}



	}

	public void setMsg(String s)
	{
		errorLabel.setText(s);
		validate();
	}

	public void actionPerformed(ActionEvent e)
	{
		// kalkuler lastTid[]
		Calendar calendar = new GregorianCalendar();
		Date currentTime = calendar.getTime();
		SimpleDateFormat tid = new SimpleDateFormat("HH:mm:ss dd/MM/yyyy");

		int sec = calendar.get(Calendar.SECOND);
		String fratidS = fraTid.getText() + ":"+sec + " " + fraDato.getText() + "/" + fraYear.getSelectedItem();
		String tiltidS = tilTid.getText() + ":"+sec + " " + tilDato.getText() + "/" + tilYear.getSelectedItem();

		long diff = 0;
		long diffCurrent = 0;

		try
		{
			diff = (tid.parse(tiltidS).getTime() - tid.parse(fratidS).getTime() ) / 1000;
			diffCurrent = (currentTime.getTime() - tid.parse(tiltidS).getTime() ) / 1000;
		}
		catch (ParseException exc)
		{
			com.d(exc.getMessage(), 1);
			setMsg("Date err");
			return;
		}
		setMsg("");
		com.d("   Differanse, diff: " + diff + " diffCurrent: " + diffCurrent, 3);


		long[] lastInterval = new long[2];

		long beginInterval = lastInterval[0] = -diff - diffCurrent;
		long endInterval = lastInterval[1] = - diffCurrent;
		com.setLastInterval(lastInterval);

		// sett avg/max
		if (avgmax.getSelectedItem().equals("Avg")) {
			com.setTidAvg(true);
		} else {
			com.setTidAvg(false);
		}

		com.d("   Ny tid, fra: " + beginInterval + " til: " + endInterval, 3);

		// Først lager vi starttidspunktet
		Date beginDate = new Date(currentTime.getTime() + (beginInterval*1000));
		Date endDate = new Date(currentTime.getTime() + (endInterval*1000));
		com.setBeginLastDate(beginDate);
		com.setEndLastDate(endDate);

		com.d("     beginInterval: " + beginDate, 4);
		com.d("     endInterval  : " + endDate, 4);

		lastValg.select("Manual");

		com.getNet().setNeedReset(true);
		com.getNet().refreshNettel();


	}


}