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

import java.awt.Canvas;
import java.awt.Scrollbar;
import java.awt.event.AdjustmentEvent;
import java.awt.event.AdjustmentListener;
import java.util.Vector;


class LayoutNettel implements AdjustmentListener
{
	LayoutXY layoutXY;
	Scrollbar sb;
	Com com;
	Vector list;
	Canvas canvas;
	String linkType;


	public LayoutNettel(Canvas canvas, Scrollbar sb, String linkType, Com com)
	{
		this.canvas = canvas;
		this.sb = sb;
		this.linkType = linkType;
		this.com = com;

		if (sb != null) {
			sb.addAdjustmentListener(this);
			sb.setVisible(false); // Default er ikke synlig
		}

	}

	public void reset()
	{
		list = new Vector();
	}

	public void activate()
	{
		quickSort(list);
		layoutXY = new LayoutXY(com, linkType, list.size() );

		// Sjekk om scrollbar er nødvendig
		if (list.size() <= layoutXY.getAntVisible())
		{
			sb.setVisible(false);
		} else
		{
			sb.setVisible(true);
			com.getMainPanel().validate();
		}

		int sbTotal = list.size();
		int sbVisible = layoutXY.getAntVisible();
		if (linkType.equals("hz"))
		{
			sbTotal = (sbTotal+1)/2;
			sbVisible /= 2;
		}

		sb.setMaximum(sbTotal);
		sb.setVisibleAmount(sbVisible);

		refresh();
	}

	public void addNettel(Nettel n)
	{
		list.addElement(n);
	}

	public void refresh()
	{
		layoutXY.reset();

		int sbMax = list.size();
		int sbValue = sb.getValue();
		int sbVisible = sb.getVisibleAmount();

		if (linkType.equals("hz"))
		{
			sbValue *= 2;
			sbVisible *= 2;
		}

		for (int i = 0; i < sbMax; i++)
		{
			Nettel n = (Nettel)list.elementAt(i);

			if (i >= sbValue && i < sbValue+sbVisible) {
				int[] XY = layoutXY.getXY();
				n.setXY(XY[0], XY[1]);
				n.setVisible(true);
				n.recalcLink();
			} else {
				n.setVisible(false);
			}
		}
		com.getNet().getVisNettel().recalcLink();

		// repaint Net
		int canvasX = canvas.getMinimumSize().width;
		int canvasY = canvas.getMinimumSize().height;

		if (linkType.equals("up"))
		{
			canvas.repaint(1, 1, canvasX, canvasY/2);
		} else
		if (linkType.equals("hz"))
		{
			canvas.repaint(1, canvasY/4, canvasX, canvasY/2);
		}
		if (linkType.equals("dn"))
		{
			canvas.repaint(1, canvasY/2, canvasX, canvasY/2);
		}


	}

	public void adjustmentValueChanged(AdjustmentEvent e)
	{
		refresh();
	}


	public static void quickSort(Vector v)
	{
		// quicksort the array
		int incr = v.size() / 2;

		while (incr >= 1)
		{
			for (int i = incr; i < v.size(); i++)
			{
				Nettel tmp = (Nettel)v.elementAt(i);
				int j = i;

				while (j >= incr && tmp.compareTo( (Nettel)v.elementAt(j - incr) ) < 0 )
				{
					v.setElementAt( v.elementAt(j-incr), j);
					j -= incr;
				}
				v.setElementAt(tmp, j);
			}
			incr /= 2;
		}

	}


}




































