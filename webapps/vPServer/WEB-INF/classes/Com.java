/*
 * Com.java
 *
 */


import java.io.*;

import javax.servlet.*;
import javax.servlet.http.*;

public class Com
{
	//public Com() { }

	public void out(String s)
	{
		if (!setType)
		{
			setContentType("text/html");
		}

		try
		{
			out.print(s);
		}
		catch (IOException e)
		{}
	}

	// out med line-feed
	public void outl(String s)
	{
		if (!setType)
		{
			setContentType("text/html");
		}

		try
		{
			out.print(s + "\n");
		}
		catch (IOException e)
		{}
	}

	public void bout(char c)
	{
		try
		{
			out.write(c);
		}
		catch (IOException e)
		{}
	}

	public void printString(String[][] s, String c, String c2)
	{
		if (s == null)
		{
			return;
		}
		for (int i = 0; i < s[0].length; i++)
		{
			for (int j = 0; j < s.length; j++)
			{
				if (s[j][i] != null)
				{
					out(s[j][i]);
					if (j+1 != s.length)
					{
						out(c2);
					}
				}
			}

			if (i+1 != s[0].length)
			{
				out(c);
			}
		}
	}
	public void printString(String[] s, String c)
	{
		if (s == null)
		{
			return;
		}
		for (int i = 0; i < s.length; i++)
		{
			if (s[i] != null)
			{
				out(s[i]);
				if (i+1 != s.length)
				{
					out(c);
				}
			}
		}
	}
	public void printString(String[] s, String[] s2, String c)
	{
		if (s == null)
		{
			return;
		}
		for (int i = 0; i < s.length; i++)
		{
			if (s[i] != null)
			{
				out(s[i] + "," + s2[i]);
				if (i+1 != s.length)
				{
					out(c);
				}
			}
		}
	}
	public void printString(String[] s, String[] s2, String[] s3, String c)
	{
		if (s == null)
		{
			return;
		}
		for (int i = 0; i < s.length; i++)
		{
			if (s[i] != null)
			{
				out(s[i] + "," + s2[i] + "," + s3[i] );
				if (i+1 != s.length)
				{
					out(c);
				}
			}
		}
	}



	public HttpServletRequest getReq() { return req; }
	public void setReq(HttpServletRequest Ireq) { req = Ireq; }

	public HttpServletResponse getRes() { return res; }
	public void setRes(HttpServletResponse Ires) { res = Ires; }

	public HttpSession getSes() { return session; }
	public void setSes(HttpSession Isession) { session = Isession; }

	public ServletOutputStream getOut() { return out; }
	public void setOut(ServletOutputStream Iout) { out = Iout; }

	public Sql getDb() { return db; }
	public void setDb(Sql Idb) { db = Idb; }

	public String getp(String param) { return req.getParameter(param); }

	public void setContentType(String type)
	{
		if (!setType)
		{
			res.setContentType(type); // Required for HTTP
			setType = true;
		}
	}

	HttpServletRequest req;
	HttpServletResponse res;
	HttpSession session;
	ServletOutputStream out;

	Sql db;

	boolean delOutput = false;
	boolean setType = false;
}

