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
		db = com.getDb();

	}

	public String handleSection(String h)
	{
		//if (h.equals("oving")) return HandlerOving.handle(com);
		//if (h.equals("admin")) return HandlerAdmin.handle(com);
		if (h.equals("vp")) return HandlerVlanPlot.handle(com);
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
			com.out( com.getConf().get("ServletGFXRoot") );
		} else
		if (s[0].equals("link"))
		{
			HandlerLink handler = new HandlerLink(s, com, num, tempNr);
			//handler.begin();
		} else
		if (s[0].equals("main"))
		{
			HandlerMain handler = new HandlerMain(s, com, num, tempNr);
			handler.begin();
		} else
		if (s[0].equals("user"))
		{
			HandlerUser handler = new HandlerUser(s, com, num, tempNr);
			handler.begin();
		} else
		if (s[0].equals("vp"))
		{
			HandlerVlanPlot handler = new HandlerVlanPlot(s, com, num, tempNr);
			handler.begin();
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
/*
			if ( (s[1].equals("oving")) || (s[1].equals("velg_klasse")) )
			{
				//String info[] = db.exec("select klasse from users where login='" + com.getUser().getLogin() + "';");

				String[] info = db.exec("select antoving from klasser where klasse='" + com.getUser().getKlasse() + "';");

				return Integer.parseInt(info[0]);


			} else
			if (s[1].equals("rett_oving"))
			{

				String[] info;

				info = db.exec("select frist from klasser where klasse='" + com.getUser().getKlasse() +
										"' and ovingnr='" + com.getReq().getParameter("ovingnr") + "';");

				if (info[0] != null)
				{
					info = db.exec("select login from ovinger where klasse='" + com.getUser().getKlasse() +
											"' and ovingnr='" + com.getReq().getParameter("ovingnr") + "';");
					if (info[0] != null)
					{
						return info.length;
					} else
					{
						return 0;
					}
				}
			}

			if (s[1].equals("listall"))
			{
				String[] info = db.exec("select login from iklasse where klasse ='" + com.getUser().getKlasse() + "';");

				if (info[0] != null)
				{
					return info.length;
				} else
				{
					return 0;
				}
			} else
*/
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
	Sql db;


}
