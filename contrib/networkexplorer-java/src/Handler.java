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

import javax.servlet.ServletOutputStream;
import javax.servlet.http.HttpServletRequest;

public class Handler
{
	public Handler(Com Icom)
	{
		com = Icom;

		req = com.getReq();
		u = com.getUser();
		out = com.getOut();
	}

	public String handleSection(String h)
	{
		if (h.equals("ni")) return HandlerNettinfo.handle(com);
		return null;
	}

	public String handle(String h)
	{
		return handle(h, 0, 0);
	}

	public void handle(String h, int num)
	{
		handle(h, num, 0);
	}

	public String handle(String h, int num, int tempNr)
	{
		String[] s = misc.tokenize(h, ".");

		if (s[0].equals("gfx"))
		{
			com.out( com.getReq().getContextPath() + "/gfx" );
		} else
		if (s[0].equals("link"))
		{
			HandlerLink handler = new HandlerLink(s, com, num, tempNr);
		} else
			
		if (s[0].equals("ni"))
		{
			HandlerNettinfo handler = new HandlerNettinfo(s, com, num, tempNr);
			handler.begin();
		}



		return null;

	}

	public int getLoops(String h, int num)
	{
		String[] s = misc.tokenize(h, ".");

		if (s[1] != null)
		{
			{
				return 0;
			}
		} else
		{
			return 0;
		}


	}

	Com com;
	HttpServletRequest req;
	User u;
	ServletOutputStream out;
}
