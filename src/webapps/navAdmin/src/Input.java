/*
 * Handler.java
 *
 */

import java.io.*;
import java.util.*;
import java.text.*;
import javax.servlet.http.*;


public class Input
{
	public Input(HttpServletRequest InReq, Com InCom)
	{
		req = InReq;
		com = InCom;
		h = com.getHandler();
	}

	public void begin()
	{

			String sect;

			sect = req.getParameter("section");

			if (sect != null)
			{
				if (sect.length() > 0)
				{
					html = h.handleSection(sect);
				}
			}

			if (html == null || html.equals("") )
			{
				if (com.getUser().getAuth())
				{

					html = "html/nav/main.html";

				} else
				{
					html = "html/main.html";
				}
			}


	}

	public String getHtml()
	{
		return html;
	}

	HttpServletRequest req;
	Com com;
	User u;
	Handler h;
	String html;

}

