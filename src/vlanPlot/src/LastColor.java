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

import java.awt.Color;
import java.text.DecimalFormat;
import java.text.DecimalFormatSymbols;


class LastColor
{
	public static final int RELATIV_SKALA = 0;
	public static final int ABSOLUTT_SKALA = 1;

	// default skala
	//private static int skala = RELATIV_SKALA;
	private static int skala = ABSOLUTT_SKALA;

	// tmp, blir satt i programmet
	private static int tmpSkala = RELATIV_SKALA;

	static int[][] grenser = {
	{
		2,
		4,
		7,
		10,
		20,
		30,
		40,
		50,
		60,
		80,
	},
	{
		32 *1024,
		64 *1024,
		256*1024,
		1  *1024*1024,
		2  *1024*1024,
		5  *1024*1024,
		10 *1024*1024,
		50 *1024*1024,
		100*1024*1024,
		500*1024*1024,
	}
	};

	static Color[] colors =
	{
		new Color(0,0,255),
		new Color(0,130,255),
		new Color(0,200,255),
		new Color(0,200,150),
		new Color(0,255,0),
		new Color(200,255,0),
		new Color(255,255,0),
		new Color(200,200,0),
		new Color(255,150,0),
		new Color(255,0,0),
		new Color(200,0,0),
	};

	public static int getSkala() { return skala; }
	public static void setSkala(int sk)
	{
		skala = sk;
	}
	public static void setTmpSkala(int sk)
	{
		tmpSkala = skala;
		skala = sk;
	}
	public static void unsetTmpSkala()
	{
		skala = tmpSkala;
	}


	public static Color getColor(double d)
	{
		if (d < 0)
		{
			return Color.black;
		}

		for (int i = 0; i < grenser[skala].length; i++)
		{
			if (d < grenser[skala][i])
			{
				return colors[i];
			}
		}
		return colors[colors.length-1];
	}

	public static int getAntTrinn()
	{
		return grenser[skala].length+1;
	}

	public static String getStringTrinn(int n)
	{
		if (skala == RELATIV_SKALA)
		{
			if (n == 0)
			{
				return "0% - " + grenser[skala][0] + "%";
			} else
			if (n < grenser[skala].length)
			{
				return "" + grenser[skala][n-1] + "% - " + grenser[skala][n] + "%";
			} else
			{
				return "" + grenser[skala][grenser[skala].length-1] + "% - 100%";
			}
		} else
		if (skala == ABSOLUTT_SKALA)
		{
			if (n == 0)
			{
				return "0 - " + formatBytes(grenser[skala][0],true,0,true);
			} else
			if (n < grenser[skala].length)
			{
				return "" + formatBytes(grenser[skala][n-1],false,0,true) + " - " + formatBytes(grenser[skala][n],true,0,true);
			} else
			{
				return ">" + formatBytes(grenser[skala][grenser[skala].length-1],true,0,true);
			}
		}
		return "";
	}

	public static String formatBytes(double bytes, boolean ext, int n, boolean bits)
	{
		String b = (bits) ? "bit" : "B";

		if (bytes >= 1024*1024)
		{
			bytes /= 1024*1024;
			return (ext) ? ""+format(bytes,n)+" M"+b+"/s" : ""+format(bytes,n);
		} else
		if (bytes >= 1024)
		{
			bytes /= 1024;
			return (ext) ? ""+format(bytes,n)+" k"+b+"/s" : ""+format(bytes,n);
		} else
		{
			return (ext) ? ""+format(bytes,n)+" "+b+"/s" : ""+format(bytes,n);
		}
	}
	public static String format(double d, int n)
	{
		DecimalFormat df = new DecimalFormat("0.0", new DecimalFormatSymbols(java.util.Locale.ENGLISH) );
		df.setMinimumFractionDigits(n);
		return df.format(d);
	}

	public static Color getColorTrinn(int n)
	{
		return colors[n];
	}


}












