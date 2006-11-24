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
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;


class AdminListener implements ActionListener
{
	Com com;
	private Button moveMode;
	private Button saveBoksXY;

	public AdminListener(Com InCom)
	{
		com = InCom;
	}

	public void setMoveMode(Button moveMode) { this.moveMode=moveMode; }
	public void setSaveBoksXY(Button saveBoksXY) { this.saveBoksXY=saveBoksXY; }

	public void actionPerformed(ActionEvent e)
	{
		Object o = e.getSource();

		if (o.equals(moveMode)) {
			// Det er kun lov å trykke denne knappen i bynettView-modus
			if (com.getNet().getBynettView()) {
				Admin adm = com.getAdmin();
				boolean b = (adm.getMoveMode()) ? false : true;
				setMoveMode(b);
			}
		} else
		if (o.equals(saveBoksXY)) {
			// Det er kun lov å trykke denne knappen i bynettView-modus
			if (com.getNet().getBynettView()) {
				Output outp = new Output(com);
				outp.saveBoksXY(com.getNet().getNettelHash(), com.getNet().getVisGruppeid() );
			}
		}
	}

	public void setMoveMode(boolean b)
	{
		// Skru av eller på move-mode
		Admin adm = com.getAdmin();
		adm.setMoveMode(b);
		moveMode.setLabel( (b)?"Off":"Move" );
	}

}