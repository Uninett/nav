/*
 * reg.java
 *
 */


import java.io.*;

import javax.servlet.*;
import javax.servlet.http.*;

public class navAdmin extends HttpServlet
{
	public void init(ServletConfig conf) throws ServletException
	{
		super.init(conf);
		// init SQL etc.
		//db = new Sql();

	}

	public void service(HttpServletRequest req, HttpServletResponse res) throws IOException
	{
		long beginTime = new java.util.GregorianCalendar().getTime().getTime();

		String html;
		Com com = new Com();
		ServletOutputStream out = res.getOutputStream();

		String navRoot = getServletContext().getInitParameter("navRoot");
		String configFile = getServletContext().getInitParameter("configFile");

		ConfigParser cp;
		try {
			cp = new ConfigParser(navRoot + configFile);
		} catch (IOException e) {
			out.println("Error, could not read config file: " + navRoot + configFile);
			return;
		}
		if (!Database.openConnection(cp.get("SQLServer"), cp.get("SQLDb"), cp.get("SQLUser"), cp.get("SQLPw"))) {
			out.println("Error, could not connect to database!");
			return;
		}
		com.setConf(cp);

		Sql db;
		{
			//Sql db = new Sql(com);
			String server = cp.get("SQLServer");
			String dbname = cp.get("SQLDb");
			String login = cp.get("SQLLogin");
			String pw = cp.get("SQLPw");

			db = new Sql(server, dbname, login, pw);
		}

		//db.sql_init();
		HttpSession session = req.getSession(true);

		if (db.getSqlStatus())
		{
			out.print("SQL no good");
		} else
		{
			com.setReq(req);
			com.setRes(res);
			com.setSes(session);
			com.setOut(out);
			com.setDb(db);

			//com.outl("Found auth: " + req.getAuthType() );
			//com.outl("Found user: " + req.getRemoteUser() );

			User u = new User(req, res, db, com);
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

			Output o = new Output(html, com);
			o.begin();

/*

			//out.print("<br>User: " + u.getLogin() + "<br>");
			//out.print("Pass: " + u.getPw() + "<br>");
			//out.print("CUser: " + u.getCookie("login") + "<br>");
			//out.print("CPass: " + u.getCookie("pass") + "<br>");
			//out.print("Html: " + html);
*/
		}


		//db.sql_close(); // Close the SQL connection
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

	//Sql db;

}

