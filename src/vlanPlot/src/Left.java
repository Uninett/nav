/*
 * NTNU ITEA Nettnu prosjekt
 *
 * Skrvet av: Kristian Eide
 *
 */

import java.util.*;
import java.text.*;

import java.awt.*;
import java.awt.event.*;


class Left extends Panel
{
	Com com;
	TopPanel topPanel;

	public Left(Com InCom)
	{
		com = InCom;

		// jepp, gridbag må til
		GridBagLayout gridbag = new GridBagLayout();
		setLayout(gridbag);
		GridBagConstraints c = new GridBagConstraints();
		c.fill = GridBagConstraints.BOTH;
		//c.fill = GridBagConstraints.NONE;
		//c.fill = GridBagConstraints.VERTICAL;
		//c.fill = GridBagConstraints.HORIZONTAL;

/*
		// logo
		c.fill = GridBagConstraints.NONE;
		Logo logo = new Logo(com);
		//c.weightx = 0; c.weighty = 0;
		c.gridx = 0; c.gridy = 0; c.gridwidth = 1; c.gridheight = 1;
		c.ipadx = 115/2; c.ipady = 310/2;
		//c.anchor = GridBagConstraints.NORTH;
		gridbag.setConstraints(logo, c);
		add(logo, c);
		com.setLogo(logo);

		// tid-panel
		c.fill = GridBagConstraints.BOTH;
		TopPanel topPanel = new TopPanel(com);
		c.weightx = 0; c.weighty = 1;
		c.gridx = 0; c.gridy = 1; c.gridwidth = 1; c.gridheight = 1;
		c.ipadx = 0; c.ipady = 0;
		gridbag.setConstraints(topPanel, c);
		add(topPanel, c);

		// admin-panelet
		AdminPanel ap = new AdminPanel(com);
		c.weightx = 0; c.weighty = 0;
		c.gridx = 0; c.gridy = 2; c.gridwidth = 1; c.gridheight = 1;
		c.ipadx = 115/2; c.ipady = 150/2;
		gridbag.setConstraints(ap, c);
		add(ap, c);
		com.setAdminPanel(ap);
*/


		// logo
		Logo logo = new Logo(com);
		c.weightx = 0; c.weighty = 50;
		c.gridx = 0; c.gridy = 0; c.gridwidth = 1; c.gridheight = 1;
		//c.anchor = GridBagConstraints.NORTH;
		gridbag.setConstraints(logo, c);
		add(logo, c);
		com.setLogo(logo);

		// tid-panel
		topPanel = new TopPanel(com);
		c.weightx = 0; c.weighty = 0;
		c.gridx = 0; c.gridy = 1; c.gridwidth = 1; c.gridheight = 1;
		//c.ipady = 500;
		c.anchor = GridBagConstraints.NORTH;
		gridbag.setConstraints(topPanel, c);
		add(topPanel, c);

		// admin-panelet
		AdminPanel ap = new AdminPanel(com);
		c.weightx = 0; c.weighty = 15;
		c.gridx = 0; c.gridy = 2; c.gridwidth = 1; c.gridheight = 1;
		//c.ipady = 40;
		//c.anchor = GridBagConstraints.CENTER;
		gridbag.setConstraints(ap, c);
		add(ap, c);
		com.setAdminPanel(ap);




	}

	public boolean getNetFinalized() { return topPanel.getNetFinalized(); }

	public void addNettNavn(String navn) { topPanel.addNettNavn(navn); }
	public void setNettIndex(int i) { topPanel.setNettIndex(i); }
	public void setNettNavn(String navn) { topPanel.setNettNavn(navn); }

	public String getNettNavn(int i) { return topPanel.getNettNavn(i); }



}


//class TopPanel extends Panel implements ItemListener,ActionListener,KeyListener
class TopPanel extends Panel implements ItemListener,ActionListener
{
	Com com;

	private TextField fraTid;
	private TextField fraDato;
	private Choice fraYear = new Choice();

	private TextField tilTid;
	private TextField tilDato;
	private Choice tilYear = new Choice();

	private Label errorLabel = new Label("");

/*
	private Choice tilMin = new Choice();
	private Choice tilHour = new Choice();
	private Choice tilDay = new Choice();
	private Choice tilMonth = new Choice();
	private Choice tilYear = new Choice();
*/

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

/*
	public Dimension getMinimumSize()
	{
		return new Dimension(100,100);
	}
	public Dimension getPreferredSize()
	{
		return getMinimumSize();
	}
*/

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
				nett.addItem("Vis " + v.elementAt(i));
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

	public TopPanel(Com InCom)
	{
		com = InCom;

		Label fraLabel = new Label("  Fra tid:");
		Label tilLabel = new Label("  Til tid:");
		Label avgmaxLabel = new Label("  Last:");

		Button okButton = new Button("OK");

		skala.addItem("Absolutt skala");
		skala.addItem("Relativ skala");

		lastValg.addItem("Avg. siste 5 min");
		lastValg.addItem("Avg. siste 1h");
		lastValg.addItem("Avg. siste 24h");
		lastValg.addItem("Maks siste 2h");
		lastValg.addItem("Maks siste 24h");
		lastValg.addItem("Manuel");

		avgmax.addItem("Avg");
		avgmax.addItem("Maks");

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
		c.weightx = 0.0; c.weighty = 10;
		c.gridx = 1; c.gridy = 8; c.gridwidth = 1; c.gridheight = 1;
		gridbag.setConstraints(okButton, c);
		add(okButton, c);

		// errorLabel
		c.weightx = 0.0; c.weighty = 0;
		c.gridx = 2; c.gridy = 8; c.gridwidth = 1; c.gridheight = 1;
		gridbag.setConstraints(errorLabel, c);
		add(errorLabel, c);


		// itemListener
		skala.addItemListener(this);
		lastValg.addItemListener(this);
		fraYear.addItemListener(this);
		tilYear.addItemListener(this);

		// acionListeners
		okButton.addActionListener(this);

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
		//roll(calendar, lastTid[0]);
		//com.setStartTid(calendar);

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

	/*
	private void roll(Calendar calendar, long n)
	{
		final long SECONDS_PER_YEAR = 60 * 60 * 24 * 365; // leap-years blir ikke tatt hensyn til her nei
		final long SECONDS_PER_MONTH = 60 * 60 * 24 * 31;
		final long SECONDS_PER_DAY = 60 * 60 * 24;
		final long SECONDS_PER_HOUR = 60 * 60;
		final long SECONDS_PER_MINUTE = 60;

		int years = calendar.get(Calendar.YEAR);
		int months = calendar.get(Calendar.MONTH);
		int days = calendar.get(Calendar.DAY_OF_MONTH);
		int hours = calendar.get(Calendar.HOUR);
		int minutes = calendar.get(Calendar.MINUTE);
		int seconds = calendar.get(Calendar.SECOND);

		years   += (int) (n / SECONDS_PER_YEAR);
		months  += (int) (n % SECONDS_PER_YEAR / SECONDS_PER_MONTH);
		days    += (int) (n % SECONDS_PER_YEAR % SECONDS_PER_MONTH / SECONDS_PER_DAY);
		hours   += (int) (n % SECONDS_PER_YEAR % SECONDS_PER_MONTH % SECONDS_PER_DAY / SECONDS_PER_HOUR);
		minutes += (int) (n % SECONDS_PER_YEAR % SECONDS_PER_MONTH % SECONDS_PER_DAY % SECONDS_PER_HOUR / SECONDS_PER_MINUTE);
		seconds += (int) (n % SECONDS_PER_YEAR % SECONDS_PER_MONTH % SECONDS_PER_DAY % SECONDS_PER_HOUR % SECONDS_PER_MINUTE);

		com.d("   Rolling back to " + hours + ":" + minutes + ":" + seconds + "  " + days + "/" + months + " " + years, 3);

		calendar.set(Calendar.YEAR, years);
		calendar.set(Calendar.MONTH, months);
		calendar.set(Calendar.DAY_OF_MONTH, days);
		calendar.set(Calendar.HOUR, hours);
		calendar.set(Calendar.MINUTE, minutes);
		calendar.set(Calendar.SECOND, seconds);
	}
	*/


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
			relativSkala = (s.equals("Relativ skala")) ? true : false;
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

			if (s.equals("Avg. siste 5 min"))
			{
				lastTid[0] = -5 * 60;
				avgmax.select("Avg");
			} else
			if (s.equals("Avg. siste 1h"))
			{
				lastTid[0] = -1 * 60 * 60;
				avgmax.select("Avg");
			} else
			if (s.equals("Avg. siste 24h"))
			{
				lastTid[0] = -24 * 60 * 60;
				avgmax.select("Avg");
			} else
			if (s.equals("Maks siste 2h"))
			{
				lastTid[0] = -2 * 60 * 60;
				com.setTidAvg(false);
				avgmax.select("Maks");
			} else
			if (s.equals("Maks siste 24h"))
			{
				lastTid[0] = -24 * 60 * 60;
				com.setTidAvg(false);
				avgmax.select("Maks");
			}

			com.setLastInterval(lastTid);
			recalcFields();
		}



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
			errorLabel.setText("Datofeil");
			validate();
			return;
		}
		errorLabel.setText("");
		com.d("   Differanse, diff: " + diff + " diffCurrent: " + diffCurrent, 3);


		long[] lastInterval = new long[2];
		//lastTid[0] = -diff - diffCurrent;
		//lastTid[1] = -diffCurrent;

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

		// Oppdatert kalenderen
		/*
		roll(calendar, lastTid[0]);
		com.setStartTid(calendar);
		calendar = new GregorianCalendar();
		roll(calendar, lastTid[1]);
		com.setEndTid(calendar);
		*/
		// Først lager vi starttidspunktet
		Date beginDate = new Date(currentTime.getTime() + (beginInterval*1000));
		Date endDate = new Date(currentTime.getTime() + (endInterval*1000));
		com.setBeginLastDate(beginDate);
		com.setEndLastDate(endDate);

		com.d("     beginInterval: " + beginDate, 4);
		com.d("     endInterval  : " + endDate, 4);

		lastValg.select("Manuel");

		//com.getNet().refetchLastInput();
		com.getNet().setNeedReset(true);
		com.getNet().refreshNettel();


	}

/*
	public void keyPressed(KeyEvent e)
	{
		TextField tf = (TextField)e.getSource();
		char c = e.getKeyChar();
		int pos = tf.getCaretPosition();
		String txt = tf.getText();

		com.d("pressed: " + e.getKeyCode() + " back: " + e.VK_BACK_SPACE + " char: " + c, 1);

		if (e.getKeyCode() == e.VK_BACK_SPACE && pos != 0)
		{
			if ( (txt.charAt(pos-1) == ':') || (txt.charAt(pos-1) == '/') )
			{
				pos--;
				tf.setCaretPosition(pos);
			}

			// slett char bak, dvs. sett inn space
			txt = txt.substring(0, pos-1) + " " + txt.substring(pos, txt.length() );
			tf.setText(txt);
			tf.setCaretPosition(pos-1);
			e.consume();
			return;
		}

		if (e.getKeyCode() == e.VK_TAB)
		{
			tf.transferFocus();
			e.consume();
			return;
		}


		try
		{
			Integer.parseInt("" + c);
		}
		catch (NumberFormatException exp)
		{
			e.consume();
			return;
		}


		//keyTyped(e);
		//keyReleased(e);
		e.consume();




	}

	public void keyReleased(KeyEvent e)
	{
		// sørg for at ikke markøren havner på en ':'
		TextField tf = (TextField)e.getSource();

		if (tf.getCaretPosition() >= tf.getColumns() )
		{
			return;
		}


		int move = 0;
		if (e.getKeyCode() == e.VK_LEFT)
		{
			if (tf.getCaretPosition() == 0)
			{
				return;
			}
			move--;

		} else
		if (e.getKeyCode() == e.VK_RIGHT)
		{
			if (tf.getCaretPosition()+move >= (tf.getColumns()-1) )
			{
				return;
			}
			move++;
		}

		if ( (tf.getText().charAt(tf.getCaretPosition()+move) == ':') || (tf.getText().charAt(tf.getCaretPosition()+move) == '/') )
		{
			if (move < 0)
			{
				move--;
			} else
			{
				move++;
			}
		}

		tf.setCaretPosition(tf.getCaretPosition()+move);








	}

	public void keyTyped(KeyEvent e)
	{
		TextField tf = (TextField)e.getSource();
		int pos = tf.getCaretPosition();
		int length = tf.getColumns();
		char c = e.getKeyChar();
		String txt = tf.getText();

		try
		{
			Integer.parseInt("" + c);
		}
		catch (NumberFormatException exp)
		{
			e.consume();
			return;
		}

		// sett inn ny char
		txt = txt.substring(0, pos) + c + txt.substring(pos+1, txt.length() );
		tf.setText(txt);

		// hvis ikke nådd slutten, flytt en frem
		if (pos < (length-1) )
		{
			tf.setCaretPosition(pos+1);
		} else
		{
			tf.setCaretPosition(pos);
		}

		// hopp over : og /
		if ( (tf.getText().charAt(tf.getCaretPosition()) == ':') || (tf.getText().charAt(tf.getCaretPosition()) == '/') )
		{
			tf.setCaretPosition(tf.getCaretPosition()+1);
		}

		// kun LEFT og RIGHT går videre
		if (e.getKeyCode() != e.VK_LEFT &&
			e.getKeyCode() != e.VK_RIGHT
			)
		{
			e.consume();
		}




	}
*/



}



class LogoPanel extends Panel
{
	Com com;

	public LogoPanel(Com InCom)
	{
		com = InCom;
/*
		// jepp, gridbag må til
		GridBagLayout gridbag = new GridBagLayout();
		setLayout(gridbag);
		GridBagConstraints c = new GridBagConstraints();
		c.fill = GridBagConstraints.BOTH;

		// venstre side av bildet
		Logo logo = new Logo(com);
		c.weightx = 0.0;
		c.weighty = 0.0;
		gridbag.setConstraints(logo, c);
		add(logo, c);
*/
		setSize(200, 500);

		Logo logo = new Logo(com);
		setLayout(new GridLayout(1, 1));
		add(logo);


	}

/*
	public Dimension getMinimumSize()
	{
		return new Dimension(100, 300);

	}
*/


}





class Logo extends Canvas
{
	Com com;
	Image navLogo;
	static final String DIR_PREFIX = "gfx/";

	public Logo(Com InCom)
	{
		com = InCom;

		Mouse mouse = new Mouse(com);
		MouseMove mv = new MouseMove(com);
		addMouseListener(mouse);
		addMouseMotionListener(mv);


		if (com.getApplet() != null)
		{
			navLogo = com.getApplet().getImage(com.getApplet().getDocumentBase(),DIR_PREFIX+"nav_logo.gif");
		} else
		{
			navLogo = Toolkit.getDefaultToolkit().getImage(DIR_PREFIX+"nav_logo.gif");
		}

	}

	public void paint(Graphics g)
	{
		// ntnulogo
		int imageX = 8;
		int imageY = 12;
		g.drawImage(navLogo, imageX, imageY, this);

		// Linjer
		{
			int xstart = 20;
			int ystart = 86;

		    // Tykkelse på linjer
		    g.setColor(Color.black);
		    g.fillRect(xstart,ystart,30,3);
		    g.fillRect(xstart,ystart+9,30,5);
		    g.fillRect(xstart,ystart+20,30,8);

			// tekst
			g.drawString("<10Mb", xstart+35, ystart+7);
			g.drawString("<100Mb", xstart+35, ystart+17);
			g.drawString("<1Gb", xstart+35, ystart+28);
		}

	    // Fargeskala
	    int xstart = 10;
	    int ystart = 130;
	    int boxSizeX = 15;
	    int boxSizeY = 15;
	    int spaceX = 5;

	    for (int i = LastColor.getAntTrinn()-1; i >= 0; i--)
	    {
		    g.setColor(LastColor.getColorTrinn(i) );
		    g.fillRect(xstart,ystart,boxSizeX,boxSizeY);

		    g.setColor(Color.black);
		    g.drawRect(xstart,ystart,boxSizeX,boxSizeY);

		    g.drawString(LastColor.getStringTrinn(i) ,xstart+boxSizeX+spaceX, ystart+10);

			ystart += boxSizeY;
		}


	}
}
















