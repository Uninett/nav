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

import java.util.StringTokenizer;


class misc
{
	/************************************************************
	* Static misc-functions										*
	*															*
	************************************************************/


	/************************************************************
	* Tokenize functions										*
	************************************************************/

	public static String[] tokenize(String h, String c)
	{
		return tokenize(h, c, false, true);
	}

	public static String[] tokenizen(String h, String c)
	{
		return tokenize(h, c, false, false);
	}

	public static String[] tokenizel(String h, String c)
	{
		return tokenize(h, c, true, true);
	}

	public static String[] tokenize(String h, String c, boolean single, boolean trim)
	{
		if (h.length() <= 0)
		{
			// return dummy token
			String[] s = new String[1];
			s[0] = "";
			return s;
		}
		StringTokenizer st = new StringTokenizer(h, c, false);
		String[] s;

		if (single && st.countTokens() > 1)
		{
			s = new String[2];
			StringBuffer b = new StringBuffer();
			int tokens = st.countTokens();

			if (trim)
			{
				b.append(st.nextToken().trim() );
			} else
			{
				b.append(st.nextToken() );
			}
			for (int i = 1; i < tokens-1; i++)
			{
				if (trim)
				{
					b.append(c + st.nextToken().trim() );
				} else
				{
					b.append(c + st.nextToken() );
				}
			}
			s[0] = b.toString();
			s[1] = st.nextToken();

		} else
		{
			s = new String[st.countTokens()];

			int i = 0;
			while (st.hasMoreTokens())
			{
				if (trim)
				{
					s[i] = st.nextToken().trim();
				} else
				{
					s[i] = st.nextToken();
				}
				i++;
			}
		}
		return s;

	}

}
