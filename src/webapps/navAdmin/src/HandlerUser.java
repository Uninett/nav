/*
 * HandlerUser.java
 *
 */

import java.io.*;
import java.util.*;
import java.text.*;

import javax.servlet.*;
import javax.servlet.http.*;

class HandlerUser
{
	public HandlerUser(String[] Is, Com Icom, int InNum, int InTempNr)
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
			if (s[1].equals("temp"))
			{
				userTemp();
			}


			// handle functions on this level
			// (session)
			/*
			if (s[1].equals("saveuser"))
			{
				saveuser();
			} else
			*/
			/*
			if (s[1].equals("endreUser"))
			{
				endreUser();
			} else
			*/
			if (s[1].equals("saveError"))
			{
				saveError();
			}






		}

		return null;
	}

	/************************************************************
	* Level 2 handler											*
	* user.<>.*													*
	************************************************************/

	private void userTemp()
	{
		if (s.length >= 3)
		{
			// identify sub-levels


			// handle functions on this level
			if (s[2].equals("info"))
			{
				//info();
			}




		}
	}



	/************************************************************
	* Level 1 functions											*
	* user.*													*
	************************************************************/

	/* [/user.saveuser]
	 * lagrer ny bruker, kalles fra form.
	 */
	 // old
/*
	private void saveuser() throws PError
	{
		String[] info;
		String[] user = new String[8];
		String p;

		// sjekk om login er opptatt
		p = com.getp("login");
		info = db.exec("select login from users where login='" + p + "';");
		if (info[0] != null)
		{
			throw new PError("dupUser");
		}

		// sjekk om passord er likt
		if (!(com.getp("pass1").equals(com.getp("pass2")) ))
		{
			throw new PError("passNoMatch");
		}

		// sjekk om nødvendige felter er på plass
		if (com.getp("fornavn").equals("") )
		{
			throw new PError("missingFirst");
		}
		if (com.getp("etternavn").equals("") )
		{
			throw new PError("missingLast");
		}
		if (com.getp("email").equals(""))
		{
			throw new PError("missingEmail");
		}

		info = db.exec("select PASSWORD('" + com.getp("pass1") + "');");

		// registrer brukeren
		user[0] = com.getp("login");
		user[1] = info[0];
		user[2] = com.getp("fornavn") + " " + com.getp("etternavn");
		user[3] = com.getp("email");

		db.insert("users", user, 4);

		// oppdater login/pw
		com.getUser().setLogin(user[0]);
		com.getUser().setPw(user[1]);
		com.getUser().refresh();

		// registrer brukerinfo
		user[1] = com.getp("fornavn");
		user[2] = com.getp("etternavn");
		user[3] = com.getp("adresse");
		user[4] = com.getp("postby");
		user[5] = com.getp("telefon");
		user[6] = com.getp("mobil");

		db.insert("personalia", user, 0);

	}
*/

	/* [/user.saveuser]
	 * lagrer ny bruker, kalles fra form.
	 */
	/*
	private void saveuser() throws PError
	{
		String[] info;
		String[] user = new String[8];
		String pw;
		String p;

		// sjekk om login er opptatt
		p = com.getp("login");
		p = misc.encSql(p);
		info = db.exec("select login from users where login='" + p + "';");
		if (info[0] != null)
		{
			throw new PError("dupUser");
		}

		// sjekk om passord er likt
		if (!(com.getp("pass1").equals(com.getp("pass2")) ))
		{
			throw new PError("passNoMatch");
		}


		// sjekk om nødvendige felter er på plass
		if (com.getp("login").equals("") )
		{
			throw new PError("missingLogin");
		}
		if (com.getp("pass1").equals("") )
		{
			throw new PError("missingPass");
		}
		if (com.getp("fornavn").equals("") )
		{
			throw new PError("missingFirst");
		}
		if (com.getp("etternavn").equals("") )
		{
			throw new PError("missingLast");
		}
		if (com.getp("email").equals(""))
		{
			throw new PError("missingEmail");
		}

		// sjekk om login inneholder ulovlige tegn
		if (!com.getp("login").equals(misc.encSql(com.getp("login"))) )
		{
			throw new PError("illegalLogin");
		}

		// generer random passord
		//pw = misc.getRandomPw();
		pw = com.getp("pass1");
		info = db.exec("select PASSWORD('" + pw + "');");

		// Get current time
		Calendar calendar = new GregorianCalendar();
		Date currentTime = calendar.getTime();
		// Format the current time.
		SimpleDateFormat formatter = new SimpleDateFormat("dd/MM/yyyy G',' HH:mm:ss");
		String dato = formatter.format(currentTime);


		// registrer brukeren
		user[0] = misc.encSql(com.getp("login"));
		user[1] = info[0];
		user[2] = misc.encSql(com.getp("fornavn") + " " + com.getp("etternavn"));
		user[3] = misc.encSql(com.getp("email"));
		user[4] = misc.encSql(com.getp("email"));
		user[5] = dato;
		user[6] = "0";
		user[7] = "[nofile]";

		db.insert("users", user, 8);

		// oppdater login/pw
		com.getUser().setLogin(user[0]);
		com.getUser().setPw(user[1]);
		com.getUser().refresh();

		// oppdater login/pw
		//com.getUser().setLogin(user[0]);
		//com.getUser().setPw(user[1]);
		//com.getUser().refresh();

		// registrer brukerinfo
		user[1] = misc.encSql(com.getp("fornavn"));
		user[2] = misc.encSql(com.getp("etternavn"));

		if (com.getp("adresse") != null)
		{
			user[3] = misc.encSql(com.getp("adresse"));
		} else
		{
			user[3] = "";
		}
		if (com.getp("postnr") != null)
		{
			user[4] = misc.encSql(com.getp("postnr"));
		} else
		{
			user[4] = "";
		}
		if (com.getp("postby") != null)
		{
			user[5] = misc.encSql(com.getp("postby"));
		} else
		{
			user[5] = "";
		}
		if (com.getp("telefon") != null)
		{
			user[6] = misc.encSql(com.getp("telefon"));
		} else
		{
			user[6] = "";
		}
		if (com.getp("mobil") != null)
		{
			user[7] = misc.encSql(com.getp("mobil"));
		} else
		{
			user[7] = "";
		}

		db.insert("personalia", user, 0);

		// send mail til bruker
/*
		String subject = "Passord for PartyReg";
		StringBuffer body = new StringBuffer();

		body.append("Her er innloggings-info for PartyReg. Du finner systemet her:\r\n\r\n");
		body.append("http://partyreg.dataparty.no\r\n\r\n");
		body.append("Brukerinformasjon:\r\n\r\n");
		body.append("Navn: " + misc.encSql(com.getp("login")) + "\r\n");
		body.append("Passord: " + pw + "\r\n\r\n");
		body.append("\r\n\r\n---\r\n");
		body.append("TDP");

		Mail mail = new Mail(com);

		mail.sendmail(com.getp("email"), "admin@dataparty.no", subject, body.toString(), com);

		com.getUser().set("message", "Du mottar snart en e-mail med brukernavn og passord for &aring; logge inn.", false);
*/
	//}



	/* [/user.saveuser]
	 * lagrer ny bruker, kalles fra form.
	 */
/*	private void saveuser() throws PError
	{
		String[] info;
		String[] user = new String[8];
		String pw;
		String p;

		// sjekk om login er opptatt
		p = com.getp("login");
		p = misc.encSql(p);
		info = db.exec("select login from users where login='" + p + "';");
		if (info[0] != null)
		{
			throw new PError("dupUser");
		}

		// sjekk om nødvendige felter er på plass
		if (com.getp("login").equals("") )
		{
			throw new PError("missingLogin");
		}
		if (com.getp("fornavn").equals("") )
		{
			throw new PError("missingFirst");
		}
		if (com.getp("etternavn").equals("") )
		{
			throw new PError("missingLast");
		}
		if (com.getp("email").equals(""))
		{
			throw new PError("missingEmail");
		}

		// sjekk om login inneholder ulovlige tegn
		if (!com.getp("login").equals(misc.encSql(com.getp("login"))) )
		{
			throw new PError("illegalLogin");
		}

		// generer random passord
		pw = misc.getRandomPw();
		info = db.exec("select PASSWORD('" + pw + "');");

		// Get current time
		Calendar calendar = new GregorianCalendar();
		Date currentTime = calendar.getTime();
		// Format the current time.
		SimpleDateFormat formatter = new SimpleDateFormat("dd/MM/yyyy G',' HH:mm:ss");
		String dato = formatter.format(currentTime);


		// registrer brukeren
		user[0] = misc.encSql(com.getp("login"));
		user[1] = info[0];
		user[2] = misc.encSql(com.getp("fornavn") + " " + com.getp("etternavn"));
		user[3] = misc.encSql(com.getp("email"));
		user[4] = misc.encSql(com.getp("email"));
		user[5] = dato;
		user[6] = "0";
		user[7] = "[nofile]";

		db.insert("users", user, 8);

		// oppdater login/pw
		//com.getUser().setLogin(user[0]);
		//com.getUser().setPw(user[1]);
		//com.getUser().refresh();

		// registrer brukerinfo
		user[1] = misc.encSql(com.getp("fornavn"));
		user[2] = misc.encSql(com.getp("etternavn"));

		if (com.getp("adresse") != null)
		{
			user[3] = misc.encSql(com.getp("adresse"));
		} else
		{
			user[3] = "";
		}
		if (com.getp("postnr") != null)
		{
			user[4] = misc.encSql(com.getp("postnr"));
		} else
		{
			user[4] = "";
		}
		if (com.getp("postby") != null)
		{
			user[5] = misc.encSql(com.getp("postby"));
		} else
		{
			user[5] = "";
		}
		if (com.getp("telefon") != null)
		{
			user[6] = misc.encSql(com.getp("telefon"));
		} else
		{
			user[6] = "";
		}
		if (com.getp("mobil") != null)
		{
			user[7] = misc.encSql(com.getp("mobil"));
		} else
		{
			user[7] = "";
		}

		db.insert("personalia", user, 0);

		// send mail til bruker

		String subject = "Passord for PartyReg";
		StringBuffer body = new StringBuffer();

		body.append("Her er innloggings-info for PartyReg. Du finner systemet her:\r\n\r\n");
		body.append("http://partyreg.dataparty.no\r\n\r\n");
		body.append("Brukerinformasjon:\r\n\r\n");
		body.append("Navn: " + misc.encSql(com.getp("login")) + "\r\n");
		body.append("Passord: " + pw + "\r\n\r\n");
		body.append("\r\n\r\n---\r\n");
		body.append("TDP");

		Mail mail = new Mail(com);

		mail.sendmail(com.getp("email"), "admin@dataparty.no", subject, body.toString(), com);

		com.getUser().set("message", "Du mottar snart en e-mail med brukernavn og passord for &aring; logge inn.", false);

	}
*/

	/* [/user.endreUser]
	 * Endre info fra bruker, data hentes fra form.
	 */
	/*
	private void endreUser() throws PError
	{
		if (!com.doauth() )
		{
			return;
		}
		String user = com.getUser().getLogin();

		// sjekk om passord er likt
		if (!(misc.encSql(com.getp("pass1")).equals(misc.encSql(com.getp("pass2"))) ))
		{
			throw new PError("passNoMatch");
		}

		// sjekk om nødvendige felter er på plass
		if (com.getp("fornavn").equals("") )
		{
			throw new PError("missingFirst");
		}
		if (com.getp("etternavn").equals("") )
		{
			throw new PError("missingLast");
		}
		if (com.getp("email").equals(""))
		{
			throw new PError("missingEmail");
		}

		// endre info
		if (!com.getp("pass1").equals("") )
		{
			db.exec("update users set pw=PASSWORD('" + misc.encSql(com.getp("pass1")) + "') where login='" + user + "';");
			String[] info = db.exec("select PASSWORD('" + misc.encSql(com.getp("pass1")) + "');");
			com.getUser().setPw(info[0]);
			com.getUser().refresh();
		}
		db.exec("update users set navn='" + misc.encSql(com.getp("fornavn")) + " " + misc.encSql(com.getp("etternavn")) + "' where login='" + user + "';");
		db.exec("update users set email='" + misc.encSql(com.getp("email")) + "' where login='" + user + "';");
		db.exec("update personalia set first='" + misc.encSql(com.getp("fornavn")) + "' where login='" + user + "';");
		db.exec("update personalia set last='" + misc.encSql(com.getp("etternavn")) + "' where login='" + user + "';");

		if (com.getp("adresse") != null)
		{
			db.exec("update personalia set adresse='" + misc.encSql(com.getp("adresse")) + "' where login='" + user + "';");
		}
		if (com.getp("postnr") != null)
		{
			db.exec("update personalia set postnr='" + misc.encSql(com.getp("postnr")) + "' where login='" + user + "';");
		}
		if (com.getp("postby") != null)
		{
			db.exec("update personalia set postby='" + misc.encSql(com.getp("postby")) + "' where login='" + user + "';");
		}
		if (com.getp("telefon") != null)
		{
			db.exec("update personalia set telefon='" + misc.encSql(com.getp("telefon")) + "' where login='" + user + "';");
		}
		if (com.getp("mobil") != null)
		{
			db.exec("update personalia set mobil='" + misc.encSql(com.getp("mobil")) + "' where login='" + user + "';");
		}

		com.getUser().set("message", "Din bruker-informasjon er oppdatert.", false);

	}
	*/

	/* [/user.saveError]
	 * Viser evt. feil-melding fra registrering
	 */
	private void saveError()
	{
		String err = com.get("saveError");

		if (err != null)
		{
			com.out(err);
		}
	}

	/* [/user.login]
	 * Viser login
	 */
	private void login()
	{
		if (com.doauth() )
		{
			com.out(com.getUser().getLogin() );
		}
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
			if (subSect.equals("reguser"))
			{
				html = "html/reguser.htm";
			} else
			if (subSect.equals("saveuser"))
			{
				try
				{
					String stat = com.getHandler().handle("user.saveuser");
					html = "html/main.htm";
				} catch (PError e)
				{
					if (e.msg.equals("dupUser") )
					{
						com.set("saveError","Beklager, men brukernavnet er opptatt.");
						html = "html/reguser.htm";
					} else
					if (e.msg.equals("passNoMatch") )
					{
						com.set("saveError","Passordene du oppgav er ikke like.");
						html = "html/reguser.htm";
					} else
					if (e.msg.equals("missingLogin") )
					{
						com.set("saveError","Du er n&oslash;dt til &aring; fylle ut login.");
						html = "html/reguser.htm";
					} else
					if (e.msg.equals("missingPass") )
					{
						com.set("saveError","Du er n&oslash;dt til &aring; fylle ut passord.");
						html = "html/reguser.htm";
					} else
					if (e.msg.equals("illegalLogin") )
					{
						com.set("saveError","Du har skrevet inn ulovlige tegn i login-navn.");
						html = "html/reguser.htm";
					} else
					if (e.msg.equals("missingFirst") )
					{
						com.set("saveError","Du er n&oslash;dt til &aring; fylle ut fornavn.");
						html = "html/reguser.htm";
					} else
					if (e.msg.equals("missingLast") )
					{
						com.set("saveError","Du er n&oslash;dt til &aring; fylle ut etternavn.");
						html = "html/reguser.htm";
					} else
					if (e.msg.equals("missingEmail") )
					{
						com.set("saveError","Du er n&oslash;dt til &aring; fylle ut <b>korrekt</b>e-mail.");
						html = "html/reguser.htm";
					} else
					{
						html = "html/main.htm";
					}
				}
			} else
			if (subSect.equals("vis"))
			{
				html = "html/user/vis.htm";
			} else
			if (subSect.equals("endre"))
			{
				html = "html/user/endre.htm";
			} else
			if (subSect.equals("endreUser"))
			{
				try
				{
					String stat = com.getHandler().handle("user.endreUser");
					html = "html/user/vis.htm";
				} catch (PError e)
				{
					if (e.msg.equals("passNoMatch") )
					{
						com.set("saveError","Passordene du oppgav er ikke like.");
						html = "html/user/endre.htm";
					} else
					if (e.msg.equals("missingFirst") )
					{
						com.set("saveError","Du er n&oslash;dt til &aring; fylle ut fornavn.");
						html = "html/user/endre.htm";
					} else
					if (e.msg.equals("missingLast") )
					{
						com.set("saveError","Du er n&oslash;dt til &aring; fylle ut etternavn.");
						html = "html/user/endre.htm";
					} else
					if (e.msg.equals("missingEmail") )
					{
						com.set("saveError","Du er n&oslash;dt til &aring; fylle ut <b>korrekt</b>e-mail.");
						html = "html/user/endre.htm";
					} else
					{
						html = "html/user/vis.htm";
					}
				}
			} else
			if (subSect.equals("visMailpw"))
			{
				html = "html/user/mailpw.htm";
			} else
			if (subSect.equals("mailpw"))
			{
				try
				{
					String stat = com.getHandler().handle("user.mailpw");
				} catch (PError e) { }

				html = "html/main.htm";
			} else
			if (subSect.equals("info"))
			{
				html = "html/user/userinfo.htm";
			}






		} else
		{
			html = "html/main.htm";
		}

		return html;
	}




	// klasse vars
	String[] s;
	Com com;
	int num;
	int tempNr;


}
