/*
 * NTNU ITEA Nettnu prosjekt
 *
 * Skrvet av: Kristian Eide
 *
 */

import java.util.*;

import java.awt.*;
import java.awt.event.*;


class Admin
{
	Com com;

	// bolske status-variabler
	boolean hasAdmin;
	boolean isAdmin = false;
	boolean moveMode = false;
	String pw;

	public Admin(Com InCom)
	{
		com = InCom;
	}

	public void setHasAdmin(boolean b) { hasAdmin = b; }
	public boolean getHasAdmin() { return hasAdmin; }

	public void setAdmin(boolean InAdmin) { isAdmin = InAdmin; }
	public boolean getAdmin() { return isAdmin; }

	public void setMoveMode(boolean b) { moveMode = b; }
	public boolean getMoveMode() { return moveMode; }

	public void setPw(String s) { pw = s; }
	public String getPw() { return pw; }
}


/*
class KnappLytter implements ActionListener
{
	Com com;
	AdminAuth adminAuth;
	TextField user;
	TextField pw;
	Label l;


	public KnappLytter(AdminAuth InAdminAuth, TextField InUser, TextField InPw, Com InCom, Label InL)
	{
		adminAuth = InAdminAuth;
		user = InUser;
		pw = InPw;
		com = InCom;
		l = InL;

	}

	public void actionPerformed(ActionEvent evt)
	{
		System.out.println("Pressed OK (admin): " + evt.getActionCommand() );
		if (evt.getActionCommand().equals("Cancel"))
		{
			//auth.hide();
		} else
		{
			String userS = user.getText();
			String pwS = pw.getText();

			if (com.getInput().getAuth(userS, pwS))
			{
				com.getAdmin().setPw(pwS);
				com.getAdmin().setAdmin(true);
				//auth.hide();
				com.getAdminPanel().showMenu();
				//com.getAdminPanel().validate();

			} else
			{
				l.setText("Invalid login");
			}
		}



	}
}
*/

class AdminPanel extends Panel
{
	Com com;
	//AdminAuth adminAuth;
	AdminMenu adminMenu;

	public AdminPanel(Com InCom)
	{
		com = InCom;
		//adminAuth = new AdminAuth(com);
		adminMenu = new AdminMenu(com);

		setLayout(new GridLayout(1, 1));
	}

/*
	public void showAuth()
	{
		add(adminAuth);
		validate();
	}
*/

	public void showMenu()
	{
		//remove(adminAuth);
		add(adminMenu);
		validate();
	}

	public void hideMenu()
	{
		remove(adminMenu);
		//adminAuth.clear();
		//add(adminAuth);
		validate();
	}
}

class AdminMenu extends Panel
{
	Com com;

	public AdminMenu(Com InCom)
	{
		com = InCom;

		// jepp, gridbag må til
		GridBagLayout gridbag = new GridBagLayout();
		setLayout(gridbag);
		GridBagConstraints c = new GridBagConstraints();
		c.fill = GridBagConstraints.BOTH;

		// admin-label
		/*
		Label topLabel = new Label("Admin:");
		c.weightx = 0.0; c.weighty = 0.0;
		c.gridx = 1; c.gridy = 1; c.gridwidth = 1; c.gridheight = 1;
		c.anchor = GridBagConstraints.NORTH;
		gridbag.setConstraints(topLabel, c);
		add(topLabel, c);
		*/

		// move nettel button
		Button moveMode = new Button("Enter move-mode");
		c.weightx = 0.0; c.weighty = 0.0;
		c.gridx = 1; c.gridy = 1; c.gridwidth = 1; c.gridheight = 1;
		c.anchor = GridBagConstraints.NORTH;
		gridbag.setConstraints(moveMode, c);
		add(moveMode, c);

		// move nettel button
		Button saveBoksXY = new Button("Save pos");
		c.weightx = 0.0; c.weighty = 0.0;
		c.gridx = 1; c.gridy = 2; c.gridwidth = 1; c.gridheight = 1;
		c.anchor = GridBagConstraints.NORTH;
		gridbag.setConstraints(saveBoksXY, c);
		add(saveBoksXY, c);

		// save-knapp
		Button exitAdmin = new Button("Exit admin");
		c.weightx = 0.0; c.weighty = 0.0;
		c.gridx = 1; c.gridy = 3; c.gridwidth = 1; c.gridheight = 1;
		c.anchor = GridBagConstraints.NORTH;
		gridbag.setConstraints(exitAdmin, c);
		add(exitAdmin, c);


		AdminListener al = new AdminListener(com);
		com.setAdminListener(al);

		al.setMoveMode(moveMode);
		al.setSaveBoksXY(saveBoksXY);
		al.setExitAdmin(exitAdmin);

		moveMode.addActionListener(al);
		saveBoksXY.addActionListener(al);
		exitAdmin.addActionListener(al);

	}

}

/*
class AdminAuth extends Panel
{
	Com com;
	final static TextField user = new TextField(6);
	final static TextField pw = new TextField(6);

	public AdminAuth(Com InCom)
	{
		com = InCom;

		// jepp, gridbag må til
		GridBagLayout gridbag = new GridBagLayout();
		setLayout(gridbag);
		GridBagConstraints c = new GridBagConstraints();
		c.fill = GridBagConstraints.BOTH;

		// overskrift
		Label overskrift = new Label("Please login");
		c.weightx = 0.0; c.weighty = 0.0;
		c.gridx = 1; c.gridy = 1; c.gridwidth = 3; c.gridheight = 1;
		gridbag.setConstraints(overskrift, c);
		add(overskrift, c);

		// userLabel
		Label userLabel = new Label("User:");
		c.weightx = 0.0; c.weighty = 0.0;
		c.gridx = 1; c.gridy = 2; c.gridwidth = 1; c.gridheight = 1;
		gridbag.setConstraints(userLabel, c);
		add(userLabel, c);

		// user
		c.weightx = 0.0; c.weighty = 0.0;
		c.gridx = 2; c.gridy = 2; c.gridwidth = 2; c.gridheight = 1;
		gridbag.setConstraints(user, c);
		add(user, c);

		// pwLabel
		Label pwLabel = new Label("Pw");
		c.weightx = 0.0; c.weighty = 0.0;
		c.gridx = 1; c.gridy = 3; c.gridwidth = 1; c.gridheight = 1;
		gridbag.setConstraints(pwLabel, c);
		add(pwLabel, c);

		// pw
		pw.setEchoChar('*');
		c.weightx = 0.0; c.weighty = 0.0;
		c.gridx = 2; c.gridy = 3; c.gridwidth = 2; c.gridheight = 1;
		gridbag.setConstraints(pw, c);
		add(pw, c);

		// OK
		Button ok = new Button("OK");
		c.weightx = 0.0; c.weighty = 0.0;
		c.gridx = 1; c.gridy = 4; c.gridwidth = 1; c.gridheight = 1;
		gridbag.setConstraints(ok, c);
		add(ok, c);

		KnappLytter knappLytter = new KnappLytter(this, user, pw, com, overskrift);
		ok.addActionListener(knappLytter);
//		cancel.addActionListener(knappLytter);



	}

	public void clear()
	{
		user.setText("");
		pw.setText("");
	}



}
*/









