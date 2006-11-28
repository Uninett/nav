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

import java.io.IOException;
import java.io.PrintStream;
import java.io.PrintWriter;
import java.util.Vector;

import javax.servlet.ServletContext;
import javax.servlet.ServletOutputStream;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.servlet.http.HttpSession;

import no.ntnu.nav.ConfigParser.ConfigParser;

public class Com
{
	public Com()
	{
		objList[0] = new Vector();
		objList[1] = new Vector();
	}

	public void out(String s)
	{
		if (!setType) { setContentType("text/html"); }

		try	{
			if (stdout)
				System.out.print(s);
			else
				out.print(s);
		}
		catch (IOException e)
		{}
	}

	// out med line-feed
	public void outl(String s)
	{
		if (!setType) { setContentType("text/html"); }

		try
		{
			if (stdout)
				System.out.println(s);
			else
				out.print(s + "\n");
		}
		catch (IOException e)
		{}
	}


	public void bout(char c)
	{
		try
		{
			if (stdout) System.out.write(c);
				else out.write(c);
		}
		catch (IOException e)
		{}
	}

	public PrintWriter getWriter() {
		if (!setType) { setContentType("text/html"); }
		return new PrintWriter(out);
	}

	public PrintStream getPStream() { return new PrintStream(out); }

	// lager object
	public void s(String param, Object o)
	{
		for (int i = 0; i < objList[0].size(); i++)
		{
			String s = (String)objList[0].elementAt(i);
			if (s.equals(param))
			{
				objList[1].setElementAt(o, i);
				return;
			}
		}
		objList[0].addElement(param.trim() );
		objList[1].addElement(o);
	}
	// henter object
	public Object g(String param)
	{
		for (int i = 0; i < objList[0].size(); i++)
		{
			String s = (String)objList[0].elementAt(i);
			if (s.equals(param))
			{
				return objList[1].elementAt(i);
			}
		}
		return null;
	}


	public ConfigParser getConf() { return cp; }
	public void setConf(ConfigParser Icp) { cp = Icp; }

	public ConfigParser getNavConf() { return navCp; }
	public void setNavConf(ConfigParser Icp) { navCp = Icp; }

	public HttpServletRequest getReq() { return req; }
	public void setReq(HttpServletRequest Ireq) { req = Ireq; }

	public HttpServletResponse getRes() { return res; }
	public void setRes(HttpServletResponse Ires) { res = Ires; }

	public HttpSession getSes() { return session; }
	public void setSes(HttpSession Isession) { session = Isession; }

	public ServletOutputStream getOut() { return out; }
	public void setOut(ServletOutputStream Iout) { out = Iout; }
	public void setStandardOutput(boolean b) { stdout = b; setType = b; }

	public ServletContext getContext() { return sc; }
	public void setContext(ServletContext sc) { this.sc = sc; }

	//public Sql getDb() { return db; }
	//public void setDb(Sql Idb) { db = Idb; }

	public User getUser() { return user; }
	public void setUser(User Iuser) { user = Iuser; }

	public Handler getHandler() { return handler; }
	public void setHandler(Handler Ihandler) { handler = Ihandler; }

	public boolean getDelOutput() { return delOutput; }
	public void setDelOutput(boolean IDelOutput) { delOutput = IDelOutput; }

	public String get(String param) { return user.get(param); }
	public void set(String param, String value) { user.set(param, value); }
	public void set(String param, String value, boolean b) { user.set(param, value, b); }

	public Object getData(String param) { return user.getData(param); }
	public void setData(String param, Object value) { user.setData(param, value); }
	public void setData(String param, Object value, boolean b) { user.setData(param, value, b); }

	public String getp(String param) { return (stdout) ? null : req.getParameter(param); }

	public boolean auth() { return user.getAuth(); }

	public boolean doauth()
	{
		if (!user.getAuth() )
		{
			user.set("message", "noauth", false);
			return false;
		}
		return true;
	}

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
	ServletContext sc;
	PrintWriter writer;

	ConfigParser cp;
	ConfigParser navCp;
	//Sql db;
	User user;
	Handler handler;

	boolean delOutput = false;
	boolean setType = false;
	boolean stdout = false;

	Vector[] objList = new Vector[2];
}

