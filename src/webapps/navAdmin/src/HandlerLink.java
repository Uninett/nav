/*
 * $Id$
 *
 * Copyright 2002-2004 Norwegian University of Science and Technology
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
 * Author: Kristian Eide <kreide@gmail.com>
 */

class HandlerLink
{
	public HandlerLink(String[] Is, Com Icom, int InNum, int InTempNr)
	{
		s = Is;
		com = Icom;
		tempNr = InTempNr;
		num = InNum;
		PATH = com.getReq().getContextPath() + com.getReq().getServletPath();
	//}

	//public boolean begin()
	//{

		/************************************************************
		* Level 1 handler											*
		* link.*													*
		************************************************************/

		if (s.length >= 2)
		{
			// identify sub-levels

			// handle functions on this level
			// (admin)
			{
				// default link
				com.out(PATH);
				com.out("?section=" + s[1]);

				if (s.length >= 3)
				{
					com.out("&func=" + s[2]);
				}

				for (int i = 1; i < s.length-2; i++)
				{
					com.out("&p" + i +"=" + s[i+2]);
				}
			}
		} else
		{
			com.out(PATH);
		}
		//return false;
	}

	// class vars
	final String PATH;
	String[] s;
	Com com;
	int num;
	int tempNr;

}
