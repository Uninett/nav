/*
 * User.java
 *
 */


import java.io.*;
import java.util.*;

import javax.servlet.http.*;

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
		//String cpw = get("pass");

		/*
		if (name == null) {
			name = req.getRemoteUser();
		}

		// først name
		if ( (cname != null) && (name != null) )
		{
			loginParam = true;
			cookieSet = true;

			name = misc.encSql(name);

			if (!(cname.equals(name))) {
				set("login", name);
			}
		} else if ( (cname == null) && (name != null) ) {
			loginParam = true;
			cookieSet = false;

			name = misc.encSql(name);

			set("login", name);
		} else if ( (name == null) && (cname != null) ) {
			loginParam = false;
			cookieSet = true;

			name = cname;
		} else {
			loginParam = false;
			cookieSet = false;
		}
		*/
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
		/*
		com.outl("getData!!<br>");
		com.outl("more: "+objList[0].size()+"!!<br>");
		com.outl("more2: "+objList[1].size()+"!!<br>");
		com.outl("session: "+session+"!!<br>");
		*/

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

		/*
		// dummy
		if (name != null && pw != null)
		{
			if (name.equals("admin") && pw.equals("admin"))
			{
				auth = true;
			} else
			{
				com.getSes().invalidate();
				auth = false;
			}
		} else
		{
			com.getSes().invalidate();
			auth = false;
		}
		*/

		/*
		String[] info = db.exec("select login from users where login='" + name + "';");

		if (info[0] != null)
		{
			info[0] = misc.decSql(info[0]);
			if (info[0].equals(name))
			{
				info = db.exec("select pw from users where login='" + name + "';");
				info[0] = misc.decSql(info[0]);
				if (info[0].equals(pw))
				{
					auth = true;
					if (loginParam)
					{
						incLoginCount();
					}
					//fetchInfo();

				} else
				{
					com.getSes().invalidate();
					auth = false;
					logout = true;
					session = false;
				}
			} else
			{
				com.getSes().invalidate();
				auth = false;
				logout = true;
				session = false;
			}
		}
		*/

	}

/*
	private void incLoginCount()
	{
		String[] info = db.exec("select ant_login from users where login='" + name + "';");
		int cnt = Integer.parseInt(info[0]);
		cnt++;
		db.exec("update users set ant_login='" + cnt + "' where login='" + name + "';");

	}

	public boolean hasCapability(String cap)
	{
		String[] info = db.exec("select gruppe from capabilities where capability='" + cap + "';");

		if (info[0] != null)
		{
			if (info[0].equals("user") )
			{
				return true;
			}
			if (!auth)
			{
				return false;
			}
			String grp = info[0];
			info = db.exec("select login from gruppe where login='" + name + "' and gruppe='" + grp + "';");

			if (info[0] != null)
			{
				return true;
			}
			info = db.exec("select login from userCapabilities left join capabilities on userCapabilities.capa_id=capabilities.id " +
							"where login='" + name + "' and capability='" + cap + "';");

			if (info[0] != null)
			{
				return true;
			}
		}

		return false;
	}
	*/

	public void refresh()
	{
		authUser();
		if (auth)
		{
			set("login", name);
			//set("pass", pw);
		}
	}

	public void logout()
	{
		try
		{
			com.getSes().invalidate();
		}
		catch (IllegalStateException e)
		{
			//com.out("IllegalStateException: " + e.getMessage() );
		}
		auth = false;
		logout = true;
		session = false;
	}

	public String getLogin() { return name; }
	public void setLogin(String InLogin) { name = InLogin; }
	//public String getPw() { return pw; }
	//public void setPw(String InPw) { pw = InPw; }
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
	//String pw;
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

