/*
 * HandlerMain.java
 *
 */

import java.io.*;
import java.util.*;

import javax.servlet.*;
import javax.servlet.http.*;

class HandlerMain
{
	public HandlerMain(String[] Is, Com Icom, int InNum, int InTempNr)
	{
		s = Is;
		com = Icom;
		tempNr = InTempNr;
		num = InNum;
	}

	public String begin() throws PError
	{
		/************************************************************
		* Level 1 handler											*
		* user.*													*
		************************************************************/

		if (s.length >= 2)
		{
			// identify sub-levels


			// handle functions on this level
			// (session)
			if (s[1].equals("appInfo"))
			{
				appInfo();
			} else
			if (s[1].equals("servletPath"))
			{
				servletPath();
			} else
			if (s[1].equals("loginForm"))
			{
				loginForm();
			} else
			if (s[1].equals("message"))
			{
				message();
			} else
			if (s[1].equals("param"))
			{
				param();
			} else
			if (s[1].equals("ifLogin"))
			{
				ifLogin();
			} else
			if (s[1].equals("ifNotLogin"))
			{
				ifNotLogin();
			} else
			if (s[1].equals("loopNr"))
			{
				loopNr();
			}




		}

		return null;
	}

	/************************************************************
	* Level 2 handler											*
	* user.<>.*													*
	************************************************************/


	/************************************************************
	* Level 1 functions											*
	* user.*													*
	************************************************************/

	/* [/main.appInfo]
	 * viser application info
	 */
	private void appInfo()
	{
		//com.out("<a href=\"/partyreg/ChangeLog.htm\">PartyReg v0.01</a>");
		com.out("PartyReg v0.10");
	}

	/* [/main.servletPath]
	 * viser path til servlet
	 */
	private void servletPath()
	{
		com.out(com.getConf().get("ServletPath"));
	}

	/* [/main.loginForm]
	 * viser login-form, evt. div. info hvis innlogget.
	 */
	private void loginForm()
	{
		if (com.getUser().getAuth() )
		{
			com.out("User: <b>" + com.getUser().getLogin() + "</b><br>");
			com.out("<br>\n");

		} else
		{
			com.out("<form action=\"" + com.getConf().get("ServletPath") + "\" METHOD=POST>\n");
			com.out("<center>\n");
			com.out("  <p>Login: <input type=\"text\" name=\"login\" size=\"10\"></p>\n");
			com.out("  <p>Passord: <input type=\"password\" name=\"pass\" size=\"8\"></p>\n");
			//com.out("  <p><input type=\"submit\" value=\"Logg inn\" name=\"B1\"><input type=\"reset\" value=\"Blank\" name=\"B2\"></p>\n");
			com.out("  <input type=\"submit\" value=\"Logg inn\" name=\"B1\">\n");
			//com.out("  <p><a href=\"" + com.getConf().get("ServletPath") + "?section=user&func=reguser\">Ny bruker</a></p>\n");
			com.out("</center>\n");
			com.out("</form>\n");



		}
	}

	/* [/main.message]
	 * Viser evt. feil-melding
	 */
	private void message()
	{
		String err = com.get("message");

		if (err != null)
		{
			com.out("<font face=\"verdana\" size=2>\n");
			com.out(" <center><b>\n");
			com.out("  Melding\n");
			com.out(" </b><br><br>\n");
			com.out("<font face=\"verdana\" size=1>\n");

			if (err.equals("noauth") )
			{
				com.out("Ingen tilgang: Du m&aring; v&aelig;re logget inn for den funksjonen.\n");
			} else
			if (err.equals("noCapability") )
			{
				com.out("Ingen tilgang til den funksjonen.\n");
			} else
			{
				com.out(err + "\n");
			}

			com.out("</font></center><br>\n");
		}

	}

	/* [/main.param]
	 * Viser en paramater-variabel
	 */
	private void param()
	{
		if (s.length >= 3)
		{
			String param = com.getp(s[2]);
			if (param != null)
			{
				com.out(param);
			}
		}
	}

	/* [/main.ifLogin]
	 * Viser en <!-- --> tags dersom ikke bruker er logget inn.
	 */
	private void ifLogin()
	{
		if (!com.auth() )
		{
			if (num == 1)
			{
				com.out("<!--");
			} else
			if (num == 2)
			{
				com.out("-->");
			}
		}
	}

	/* [/main.ifNotLogin]
	 * Viser en <!-- --> tags dersom bruker er logget inn.
	 */
	private void ifNotLogin()
	{
		if (com.auth() )
		{
			if (num == 1)
			{
				com.out("<!--");
			} else
			if (num == 2)
			{
				com.out("-->");
			}
		}
	}

	/* [/main.randomHeading]
	 * Viser en random fil fra html/headings diret.
	 */
	/*
	private void randomHeading()
	{
		String header = com.get("headingFile");

		if (header == null)
		{
			File f = new File(com.getConf().get("ServletRoot") + "html/headings" );

			Random rand = new Random();
			// java 1 syntax
			int min = 0;
			int max = f.list().length-1;

			int i = rand.nextInt();
			if (i < 0)
			{
				i *= -1;
			}
			i = (i%(max - min + 1) + min);

			String[] fn = f.list();

			f = new File(com.getConf().get("ServletRoot") + "html/headings/" + fn[i]);

			header = f.getAbsolutePath();

			com.set("headingFile", header);
		}

		try
		{
			BufferedReader in = new BufferedReader(new FileReader(header ));

			while (in.ready())
			{
				com.bout( (char)in.read());
			}
		} catch (IOException e) { }


	}
	*/

	/* [/main.loopNr]
	 * Viser nummeret på loop i template-fil
	 */
	private void loopNr()
	{
		com.out("" + tempNr);
	}



	/************************************************************
	* Level 2 functions											*
	* user.<>.*													*
	************************************************************/


	/************************************************************
	* End functions												*
	* admin.*													*
	************************************************************/





	public static String handle(Com com)
	{
		String html = null;
		String subSect = com.getReq().getParameter("func");

		if (subSect != null)
		{
			if (subSect.equals("fagliste"))
			{
				html = "html/admin/multiklasse.htm";
			}
		} else
		{
			html = "html/admin/velg_oving.htm";
		}

		return html;
	}




	// klasse vars
	String[] s;
	Com com;
	int num;
	int tempNr;


}
