/*
 * $Id$
 *
 * Copyright 2002, 2004 Norwegian University of Science and Technology
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


import java.util.Vector;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

public class User
{
	public User(HttpServletRequest InReq, HttpServletResponse InRes, Com InCom)
	{
		req = InReq;
		res = InRes;
		com = InCom;
		dataList = new Vector();
		objList[0] = new Vector();
		objList[1] = new Vector();
	}

	public void begin()
	{
		getInfo();
		authUser();
	}

	private void getInfo()
	{
		name = "admin";
	}

	// henter typen String
	public String get(String param)
	{
		String data = null;

		if (session)
		{
			data = (String)com.getSes().getAttribute(param);
		}

		if (data == null)
		{
			for (int i = 0; i < dataList.size(); i++)
			{
				String[] s = (String[])dataList.elementAt(i);
				if (s[0].equals(param))
				{
					return s[1];
				}
			}
		}

		return data;
	}

	public void set(String param, String value)
	{
		set(param, value, true);
	}

	// lagrer typen String
	public void set(String param, String value, boolean persistent)
	{
		if (value != null)
		{
			value = value.trim();
		}

		if ( (persistent) && (session) )
		{
			com.getSes().setAttribute(param.trim(), value );
		}

		String[] s = new String[2];
		s[0] = param.trim();
		s[1] = value;

		for (int i = 0; i < dataList.size(); i++)
		{
			String[] t = (String[])dataList.elementAt(i);
			if (t[0].equals(param.trim() ))
			{
				dataList.setElementAt(s, i);
				return;
			}
		}

		dataList.addElement(s);
	}

	// henter typen Object
	public Object getData(String param)
	{

		for (int i = 0; i < objList[0].size(); i++)
		{
			String s = (String)objList[0].elementAt(i);
			if (s.equals(param))
			{
				return objList[1].elementAt(i);
			}
		}

		if (session)
		{
			try
			{
				return com.getSes().getAttribute(param);
			} catch (Exception e)
			{
				com.outl("Error in getData(): session not found, "+ e.getMessage() + "<br>" );
			}
		}

		return null;
	}

	// lagrer typen Object
	public void setData(String param, Object o)
	{
		setData(param, o, true);
	}


	// lagrer typen Object
	public void setData(String param, Object o, boolean persistent)
	{
		if ( (persistent) && (session) )
		{
			try
			{
				com.getSes().setAttribute(param.trim(), o);
			} catch (Exception e)
			{
				com.outl("Error in setData(): session not found, "+ e.getMessage() + "<br>" );
			}
		}

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


	private void authUser()
	{
		if (name != null) {
			auth = true;
		} else {
			com.getSes().invalidate();
			auth = false;
		}

	}

	public void refresh()
	{
		authUser();
		if (auth)
		{
			set("login", name);
		}
	}

	public void logout()
	{
		com.getSes().invalidate();
		auth = false;
		logout = true;
		session = false;
	}

	public String getLogin() { return name; }
	public void setLogin(String InLogin) { name = InLogin; }
	public void setNoSession() { session = false; }
	public String getMessage() { return message; }
	public void setMessage(String InMessage) { message = InMessage; set("message", message); }
	public boolean getAuth() { return auth;	}
	public boolean isAdmin() { return admin;	}
	public boolean getLoginParam() { return loginParam;	}
	public boolean getCookieSet() { return cookieSet;	}
	public boolean getSecurityError() { return securityError;	}

	HttpServletRequest req;
	HttpServletResponse res;

	String name;
	String message;
	boolean auth = false;
	boolean loginParam = false;
	boolean cookieSet = false;
	boolean admin = false;
	boolean securityError = false;
	boolean valgtKlasse = false;
	boolean logout = false;
	boolean session = true;
	Com com;

	Vector dataList;
	Vector[] objList = new Vector[2];


}

