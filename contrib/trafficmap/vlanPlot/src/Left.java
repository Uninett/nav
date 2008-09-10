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

import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Panel;


class Left extends Panel
{
	/**
	 * 
	 */
	private static final long serialVersionUID = 1L;
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

		// logo
		Logo logo = new Logo(com);
		c.weightx = 0; c.weighty = 0;
		c.gridx = 0; c.gridy = 0; c.gridwidth = 1; c.gridheight = 1;
		//c.anchor = GridBagConstraints.NORTH;
		gridbag.setConstraints(logo, c);
		add(logo, c);
		com.setLogo(logo);

		// tid-panel
		topPanel = new TopPanel(com);
		c.weightx = 0; c.weighty = 0;
		c.gridx = 0; c.gridy = 1; c.gridwidth = 1; c.gridheight = 1;
		c.anchor = GridBagConstraints.NORTH;
		gridbag.setConstraints(topPanel, c);
		add(topPanel, c);

	}

	public boolean getNetFinalized() { return topPanel.getNetFinalized(); }

	public void addNettNavn(String navn) { topPanel.addNettNavn(navn); }
	public void setNettIndex(int i) { topPanel.setNettIndex(i); }
	public void setNettNavn(String navn) { topPanel.setNettNavn(navn); }

	public String getNettNavn(int i) { return topPanel.getNettNavn(i); }

	public void showAdminButton() { topPanel.showAdminButton(); }

	public void setMsg(String s) { topPanel.setMsg(s); }



}




















