/*
 * Handler.java
 *
 */

import java.io.*;
import java.util.*;

import java.net.*;
import java.io.*;

import javax.servlet.*;
import javax.servlet.http.*;

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

	public String handle(String h) throws PError
	{
		return handle(h, 0, 0);
	}

	public void handle(String h, int num) throws PError
	{
		handle(h, num, 0);
	}

	public String handle(String h, int num, int tempNr) throws PError
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
