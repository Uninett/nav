/*
 * NTNU ITEA Nettnu prosjekt
 *
 * Skrvet av: Kristian Eide
 *
 */

import java.util.*;

import java.awt.*;
import java.awt.event.*;


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
			//com.d("SET SCROLL " + linkType + " FALSE!!!",2);
			//com.getMainPanel().validate();
			//com.getMainPanel().validate();
		} else
		{
			sb.setVisible(true);
			//com.d("SET SCROLL " + linkType + " TRUE!!!",2);
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

		//com.d("LayoutNettel.activate(): LinkType: " + linkType + " Max: " + sbTotal + " VisibleAmount: " + sb.getMaximum() ,2);

		refresh();
	}

	public void addNettel(Nettel n)
	{
		list.addElement(n);
	}

	public void refresh()
	{
		layoutXY.reset();

		//int sbMax = Math.min(sb.getMaximum(),list.size());
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
				//com.d("LAYOUT: Nettel: " + n.getName() + " Visible: YES" + " X: " + XY[0] + " Y: " + XY[1],2);
			} else {
				n.setVisible(false);
				//com.d("LAYOUT: Nettel: " + n.getName() + " Visible: NO",2);
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
			//canvas.repaint(1, 1, canvasX, canvasY);
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

				//while (j >= incr && tmp.angle() < ((vect)v.elementAt(j - incr)).angle() )
				while (j >= incr && tmp.compareTo( (Nettel)v.elementAt(j - incr) ) < 0 )
				{
					//v.setElementAt(v.elementAt(j - incr), j);
					v.setElementAt( v.elementAt(j-incr), j);
					//s[j] = s[j - incr];
					j -= incr;
				}
				//v.setElementAt(tmp, j);
				v.setElementAt(tmp, j);
				//s[j] = tmp;
			}
			incr /= 2;
		}

		//return s;
	}


}




































