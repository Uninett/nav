/*
 * reg.java
 *
 */

import no.ntnu.nav.ConfigParser.*;
import no.ntnu.nav.Database.*;

import java.io.*;

import javax.servlet.*;
import javax.servlet.http.*;

public class navAdmin extends HttpServlet
{
	public static final String scriptName = "navAdmin";

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

		String navRoot = getServletContext().getInitParameter("navRoot");
		String dbConfigFile = getServletContext().getInitParameter("dbConfigFile");
		String configFile = getServletContext().getInitParameter("configFile");
		String navConfigFile = getServletContext().getInitParameter("navConfigFile");

		ConfigParser cp, dbCp, navCp;
		try {
			cp = new ConfigParser(navRoot + configFile);
		} catch (IOException e) {
			cp = null;
			/*
			out.println("Error, could not read config file: " + navRoot + configFile);
			return;
			*/
		}
		try {
			dbCp = new ConfigParser(navRoot + dbConfigFile);
		} catch (IOException e) {
			out.println("Error, could not read database config file: " + navRoot + dbConfigFile);
			return;
		}
		if (!Database.openConnection(dbCp.get("dbhost"), dbCp.get("dbport"), dbCp.get("db_nav"), dbCp.get("script_"+scriptName), dbCp.get("userpw_"+dbCp.get("script_"+scriptName)))) {
			out.println("Error, could not connect to database!");
			return;
		}
		try {
			navCp = new ConfigParser(navRoot + navConfigFile);
		} catch (IOException e) {
			out.println("Error, could not read nav config file: " + navRoot + navConfigFile);
			return;
		}
		com.setConf(cp);
		com.setNavConf(navCp);

		/*
		out.println("gfx, " + getServletContext().getResourceAsStream("gfx/dumhub.gif"));
		InputStream is = getServletContext().getResourceAsStream("WEB-INF/html/cpdata.bat");
		if (is != null) {
			BufferedReader bf = new BufferedReader(new InputStreamReader(is));
			//out.println("cpdata.bat ->" + is.available() );
			//int i=is.available();
			//while (i-- > 0) { int c = is.read(); out.println("char: " + (char)c + " int: " + c); i++; }
			while (bf.ready()) out.print((char)bf.read());
			//out.println("cpdata.bat ->Done");
		}
		*/
		//out.println("getContextPath(), " + req.getContextPath() );
		//out.println("getServletPath(), " + req.getServletPath() );

		HttpSession session = req.getSession(true);

		com.setContext(getServletContext());
		com.setReq(req);
		com.setRes(res);
		com.setSes(session);
		com.setOut(out);

		//com.outl("Found auth: " + req.getAuthType() );
		//com.outl("Found user: " + req.getRemoteUser() );

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

