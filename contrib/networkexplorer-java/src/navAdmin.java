/*
 * $Id$
 *
 * Copyright 2002-2005 Norwegian University of Science and Technology
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

import java.io.File;
import java.io.IOException;
import java.io.PrintStream;

import javax.servlet.ServletConfig;
import javax.servlet.ServletException;
import javax.servlet.ServletOutputStream;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.servlet.http.HttpSession;

import no.ntnu.nav.Path;
import no.ntnu.nav.ConfigParser.ConfigParser;
import no.ntnu.nav.Database.Database;

public class navAdmin extends HttpServlet
{
	public static final String scriptName = "default";

	public void init(ServletConfig conf) throws ServletException
	{
		super.init(conf);
	}

	public void service(HttpServletRequest req, HttpServletResponse res) throws IOException
	{
		long beginTime = new java.util.GregorianCalendar().getTime().getTime();

		String html;
		Com com = new Com();
		ServletOutputStream out = res.getOutputStream();

		String dbConfigFile = getServletContext().getInitParameter("dbConfigFile");
		String configFile = getServletContext().getInitParameter("configFile");
		String navConfigFile = getServletContext().getInitParameter("navConfigFile");

		ConfigParser cp, dbCp, navCp;
		try {
			cp = new ConfigParser(Path.sysconfdir + File.separatorChar + configFile);
		} catch (IOException e) {
			cp = null;
		}
		try {
			dbCp = new ConfigParser(Path.sysconfdir + File.separatorChar + dbConfigFile);
		} catch (IOException e) {
			out.println("Error, could not read database config file: " + Path.sysconfdir + File.separatorChar + dbConfigFile);
			return;
		}
		if (!Database.openConnection(dbCp.get("dbhost"), dbCp.get("dbport"), dbCp.get("db_nav"), dbCp.get("script_"+scriptName), dbCp.get("userpw_"+dbCp.get("script_"+scriptName)))) {
			out.println("Error, could not connect to database!");
			return;
		}
		try {
			navCp = new ConfigParser(Path.sysconfdir + File.separatorChar + navConfigFile);
		} catch (IOException e) {
			out.println("Error, could not read nav config file: " + Path.sysconfdir + File.separatorChar + navConfigFile);
			return;
		}
		com.setConf(cp);
		com.setNavConf(navCp);


		HttpSession session = req.getSession(true);

		com.setContext(getServletContext());
		com.setReq(req);
		com.setRes(res);
		com.setSes(session);
		com.setOut(out);


		User u = new User(req, res, com);
		u.begin();
		if (u.getSecurityError())
		{
			html = "html/security.htm";
		} else
		{
			com.setUser(u);

			Handler h = new Handler(com);
			com.setHandler(h);

			Input in = new Input(req, com);
			in.begin();

			html = in.getHtml();
		}

		Output o = new Output(html, com, getServletContext());
		o.begin();

		long usedTime = new java.util.GregorianCalendar().getTime().getTime() - beginTime;
		try {
			com.outl("\n<!-- Total time used: " + usedTime + " ms -->");
			com.outl("<!-- openConnections: " + Database.getConnectionCount() + " -->");
			Database.closeConnection();
			out.close();
		} catch (Exception e) {
			com.outl("Exception: " + e.getMessage());
			e.printStackTrace(new PrintStream(res.getOutputStream()));
		}

	}

}

