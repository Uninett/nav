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


class LayoutXY
{
	// konfigurasjon UPLINK og DNLINK
	int vtDivider = 16; // mellomrom mellom kanten og boksene
	int spaceX = 30; // mellomrom mellom selve boksene

	// konfigurasjon HZLINK
	int hzDivider = 32;
	int spaceY = 20;


	Com com;
	String linkType;

	// statiske konstanter
	public static final int UPLINK = 0;
	public static final int HZLINK = 1;
	public static final int DNLINK = 2;

	int canvasX, canvasY;
	int sizeX, sizeY;
	int retX, retY;
	int borderVt, borderHz;

	int total;
	int current = 1;

	public LayoutXY(Com InCom, String InLinkType, int InTotal)
	{
		com = InCom;
		linkType = InLinkType;
		total = InTotal;

		canvasX = com.getNet().getMinimumSize().width;
		canvasY = com.getNet().getMinimumSize().height;

		sizeX = Nettel.sizeX;
		sizeY = Nettel.sizeY;

		borderVt = canvasY / vtDivider;
		borderHz = canvasX / hzDivider;

		if (linkType.equals("up") || linkType.equals("dn") )
		{
			calcVt();
		}
	}

	public void reset()
	{
		current = 1;
	}


	public int[] getXY()
	{
		if (linkType.equals("up") || linkType.equals("dn") )
		{
			return getVt();

		} else
		if (linkType.equals("hz"))
		{
			return getHz();
		}

		return new int[0];
	}

	public int getTotal() { return total; }

	public int getAntVisible()
	{
		if (linkType.equals("up") || linkType.equals("dn") )
		{
			return (canvasX - borderVt*2) / (Nettel.sizeX+spaceX);

		} else
		if (linkType.equals("hz") )
		{
			int availY = canvasY - borderVt*2 - (int)((Nettel.sizeY+spaceY)*2*1.5);
			int visible = availY / (Nettel.sizeY+spaceY);

			return visible*2;
		}
		return 0;
	}

	private void calcVt()
	{
		if (linkType.equals("up"))
		{
			retY = borderVt;

		} else
		if (linkType.equals("dn"))
		{
			retY = canvasY - borderVt;
			retY -= Nettel.sizeY;
		}
	}

	private int[] getVt()
	{
		retX = canvasX/2 - (Math.min(getTotal(), getAntVisible()) * (Nettel.sizeX+spaceX))/2 + spaceX/2;
		retX += (Nettel.sizeX+spaceX)*(current-1);

		current++;

		int[] ret = new int[2];
		ret[0] = retX;
		ret[1] = retY;

		return ret;
	}

	private int[] getHz()
	{
		// oddetall, boxen settes på venstre side
		// partall, boxen settes på høyre side
		int retX = ((current&1)!=0) ? borderHz : canvasX - borderHz - Nettel.sizeX;

		int antRader = (Math.min(getTotal(), getAntVisible() )+1)/2;
		retY = canvasY/2 - antRader*(Nettel.sizeY+spaceY)/2 + spaceY/2;

		// kun øk Y-verdi dersom oddetall
		int t = current;
		if ((t&1)==0) t--;
		retY += (Nettel.sizeY+spaceY)* ((t-1)/2);

		current++;

		int[] ret = new int[2];
		ret[0] = retX;
		ret[1] = retY;

		return ret;
	}


}



























