/*
 * HandlerVlanPlot.java
 *
 */

import java.io.*;
import java.util.*;

import javax.servlet.*;
import javax.servlet.http.*;

class HandlerVlanPlot
{
	public HandlerVlanPlot(String[] Is, Com Icom, int InNum, int InTempNr)
	{
		s = Is;
		com = Icom;
		db = com.getDb();
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
			if (s[1].equals("dbcnf"))
			{
				vpDbcnf();
			}

			// handle functions on this level
			// (session)
			if (s[1].equals("showConfig"))
			{
				showConfig();
			} else
			if (s[1].equals("antUserTreff"))
			{
				antUserTreff();
			}




		}

		return null;
	}

	/************************************************************
	* Level 2 handler											*
	* user.<>.*													*
	************************************************************/

	private void vpDbcnf()
	{
		if (s.length >= 3)
		{
			// identify sub-levels


			// handle functions on this level
			if (s[2].equals("selectText"))
			{
				selectText();
			} else
			if (s[2].equals("addText"))
			{
				addText();
			} else
			if (s[2].equals("editText"))
			{
				editText();
			} else
			if (s[2].equals("removeText"))
			{
				removeText();
			} else
			if (s[2].equals("editField"))
			{
				editField();
			}






		}
	}



	/************************************************************
	* Level 1 functions											*
	* user.*													*
	************************************************************/

	/* [/vp.showConfig]
	 * Skriv ut config databasen
	 */
	private void showConfig()
	{
		String[][] data = db.exece("select id,value from vpConfig where parent='0' order by id;");

		String[] id = data[0];
		String[] value = data[1];

		com.outl("<table>");
		for (int i = 0; i < id.length; i++)
		{
			expand(id[i], value[i], 0);
		}
		com.outl("</table>");





	}
	private void expand(String id, String value, int depth)
	{
		String[][] data = db.exece("select id,value from vpConfig where parent='" + id + "' order by parent,id;");
		printValue(id, value, depth);

		for (int j = 0; j < data[0].length; j++)
		{
			if (data[0][0] == null) break;

			String[] info = db.exec("select id from vpConfig where parent='" + data[0][j] + "';");

			if (info[0] != null)
			{
				// ny underlevel fins
				expand(data[0][j], data[1][j], depth+1);

			} else
			{
				// ingen underlevel
				printValue(data[0][j], data[1][j], depth+1);
			}
		}
	}
	private void printValue(String id, String value, int depth)
	{

		//com.out("<table>\n");
		com.out("  <tr>\n");
		com.out("    <td>\n");

		printDepth(depth);
		com.out(value + " <a href=\"");
		link("link.vp.removeRecord." + id );
		com.out("\">[X]</a><br>\n");

		com.out("    </td>\n");
		com.out("  </tr>\n");
		//com.out("</table>\n");
	}
	private void printDepth(int depth)
	{
		for (int i = 0; i < depth; i++)
		{
			com.out("&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;");
			//com.out("---->");
		}

	}



	/* [/admin.antUserTreff]
	 * Viser antall treff fra user-søk
	 */
	private void antUserTreff()
	{
		String field = com.getp("searchField");
		String search = com.getp("searchString");
		if (search == null)
		{
			search = "";
		}

		if (field.equals("login"))
		{
			field = "users.login";
		}

		String[] info = db.exec("select users.login from users left join personalia on users.login=personalia.login where " +
										field + " like '%" + search + "%';", true);

		if (info[0] != null)
		{
			com.out(info[0]);
		} else
		{
			com.out("0");
		}

	}


	/************************************************************
	* Level 2 functions											*
	* user.<>.*													*
	************************************************************/

	/* [/vp.dbcnf.selectText]
	 * Viser alle tekster som er lagt inn for editering
	 */
	private void selectText()
	{
		DbCnf cnf = new DbCnf(com);

		String[] txt = null;
		if (com.get("nettel") != null && !com.get("nettel").equals("") )
		{
			txt = cnf.get("dbcnf.nettel.txt." + com.get("nettel") );
		} else
		if (com.get("linkFra") != null && !com.get("linkFra").equals("") )
		{
			txt = cnf.get("dbcnf.link.txt." + com.get("linkFra") + "." + com.get("linkTil") );
		}

		if (txt != null)
		{
			for (int i = 0; i < txt.length; i++)
			{
				String tekst = misc.hex(misc.encSql(txt[i]));

				// link to remove tekst
				com.outl("<tr>");
				com.outl("  <td>");

				com.out("<a href=\"");
				link("link.vp.removeText." + misc.hex(misc.encSql(txt[i])) );
				com.outl("\">(remove)</a>");

				com.outl("  </td>");


				// tekst
				com.outl("  <td>");

				for (int j = 0; j < txt[i].length(); j++)
				{
					// fint index for ¤
					int index = txt[i].indexOf('¤', j);
					if (index == -1)
					{
						// just print the rest of the string
						com.out( txt[i].substring(j, txt[i].length() ));
						j = txt[i].length();
					} else
					{
						// print everything before ¤
						com.out( txt[i].substring(j, index) );

						// find end of keyword
						int end = txt[i].indexOf('¤', index+1);
						if (end == -1)
						{
							// the rest of the string is a keyword
							end = txt[i].length();
						}

						// print the keyword
						com.out("<a href=\"");
						link("link.vp.editText." + tekst + "." + txt[i].substring(index, end+1) );
						com.out("\">" + txt[i].substring(index+1, end) + "</a>");

						j = end;
					}
				}
				com.outl("");

				com.outl("  </td>");
				com.outl("</tr>");


			}


		}
	}

	/* [/vp.dbcnf.addText]
	 * Lagrer ny tekst i database
	 */
	private void addText()
	{
		String tekst = com.getp("tekst");

		if (tekst != null)
		{
			DbCnf cnf = new DbCnf(com);

			tekst = misc.encSql(tekst);

			if (com.get("nettel") != null && !com.get("nettel").equals("") )
			{
				cnf.set("dbcnf.nettel.txt." + com.get("nettel"), tekst);
			} else
			if (com.get("linkFra") != null && !com.get("linkFra").equals("") )
			{
				cnf.set("dbcnf.link.txt." + com.get("linkFra") + "." + com.get("linkTil"), tekst);
			}
		}

	}

	/* [/vp.dbcnf.editText]
	 * Editerer info om elementer i en tekst
	 */
	private void editText()
	{
		String tekst = com.getp("tekst");
		String keyword = com.getp("keyword");

		tekst = misc.decSql(misc.dehex(tekst));
		keyword = misc.decSql(keyword);

		if (tekst == null)
		{
			return;
		}

		String[] ins = new String[3];
		ins[0] = misc.encSql( com.getp("tabell") );
		ins[1] = misc.encSql( com.getp("nettelid") );
		ins[2] = misc.encSql( com.getp("incfelt") );

		DbCnf cnf = new DbCnf(com);

		if (com.get("nettel") != null && !com.get("nettel").equals("") )
		{
			//ins[3] = misc.encSql( com.get("nettel") );

			cnf.remove("dbcnf.nettel.txt." + com.get("nettel") + "." + tekst + "." + keyword);
			cnf.set("dbcnf.nettel.txt." + com.get("nettel") + "." +  tekst + "." + keyword, ins);

		} else
		if (com.get("linkFra") != null && !com.get("linkFra").equals("") )
		{
			//ins[3] = com.get("linkFra");
			//ins[4] = com.get("linkTil");

			cnf.remove("dbcnf.link.txt." + com.get("linkFra") + "." + com.get("linkTil") + "." + tekst + "." + keyword);
			cnf.set("dbcnf.link.txt." + com.get("linkFra") + "." + com.get("linkTil") + "." + tekst + "." + keyword, ins);
		}



	}

	/* [/vp.dbcnf.removeText]
	 * Editerer info om elementer i en tekst
	 */
	private void removeText()
	{
		String tekst = com.getp("p1");
		tekst = misc.decSql(misc.dehex(tekst));

		DbCnf cnf = new DbCnf(com);

		if (com.get("nettel") != null && !com.get("nettel").equals("") )
		{
			cnf.remove("dbcnf.nettel.txt." + com.get("nettel") + "." + tekst);
		} else
		if (com.get("linkFra") != null && !com.get("linkFra").equals("") )
		{
			cnf.remove("dbcnf.link.txt." + com.get("linkFra") + "." + com.get("linkTil") + "." + tekst);
		}
	}

	/* [/vp.dbcnf.editField]
	 * Skriver ut eksisterende info i feltene
	 */
	private void editField()
	{
		String tekst = com.getp("p1");
		String keyword = com.getp("p2");
		String felt = s[3];

		if (felt == null || tekst == null || keyword == null)
		{
			return;
		}

		DbCnf cnf = new DbCnf(com);

		String[] data = null;
		if (com.get("nettel") != null && !com.get("nettel").equals("") )
		{
			data = cnf.get("dbcnf.nettel.txt." + com.get("nettel") + "." + tekst + "." + keyword);
		} else
		if (com.get("linkFra") != null && !com.get("linkFra").equals("") )
		{
			data = cnf.get("dbcnf.nettel.txt." + com.get("linkFra") + "." + com.get("linkTil") + "." + tekst + "." + keyword);
		}

		if (data == null)
		{
			return;
		}

		if (felt.equals("tabell"))
		{
			com.out(data[0]);
		} else
		if (felt.equals("nettelid"))
		{
			com.out(data[1]);
		} else
		if (felt.equals("incfelt"))
		{
			com.out(data[2]);
		}


	}









	/* [/admin.temp.list.*]
	 * Viser verdi fra felt i users-tabell
	 */
	private void list()
	{
		if (!com.cap("viewUsers")) { return; }

		if (s.length < 3)
		{
			return;
		}

		String field = com.getp("searchField");

		String[] info = (String[])com.getUser().getData("adminListUsers" + s[3]);
		if (info == null)
		{
			String tabell;

			if (s[3].equals("login"))
			{
				tabell = "users.login";
			} else
			{
				tabell = s[3];
			}

			if (field.equals("login"))
			{
				field = "users.login";
			}

			String search = com.getp("searchString");
			if (search == null)
			{
				search = "";
			}

			info = db.exec("select " + tabell + " from users left join personalia on users.login=personalia.login where " +
									field + " like '%" + search + "%';");

			com.getUser().setData("adminListUsers" + s[3], info, false);

		}

		if (info[0] != null)
		{
			com.out(info[tempNr-1]);
		}



	}




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
			if (subSect.equals("showconfig"))
			{
				html = "html/nav/showdb.html";

			} else
			if (subSect.equals("removeRecord"))
			{
				String removeId = com.getp("p1");
				if (removeId != null)
				{
					DbCnf cnf = new DbCnf(com);
					cnf.removeId(removeId);
				}
				html = "html/nav/showdb.html";

			}
			if (subSect.equals("conf"))
			{
				String p1 = com.getReq().getParameter("p1");

				if (p1 != null)
				{
					if (p1.equals("enkel"))
					{
						html = "html/vp/enkelcnf.html";
					} else
					if (p1.equals("grupper"))
					{
						html = "html/vp/grpcnf.html";
					} else
					if (p1.equals("database"))
					{
						if (com.getReq().getParameter("nettel") != null)
						{
							// vis html-side for config av nettel
							html = "html/vp/dbcnf/selecttext.html";

							com.getUser().set("nettel", com.getReq().getParameter("nettel") );
							com.getUser().set("linkFra", "" );

						} else
						if (com.getReq().getParameter("linkFra") != null)
						{
							// vis html-side for config av linker
							html = "html/vp/dbcnf/selecttext.html";

							com.getUser().set("nettel", "" );
							com.getUser().set("linkFra", com.getReq().getParameter("linkFra") );
							com.getUser().set("linkTil", com.getReq().getParameter("linkTil") );

						} else
						{
							// ingen form, vis hmtl-side med form
							html = "html/vp/dbcnf/dbcnf.html";
						}

					}
				}

			} else
			if (subSect.equals("addText"))
			{
				String p1 = com.getReq().getParameter("p1");

				if (p1 != null && p1.equals("save") )
				{
					try
					{
						com.getHandler().handle("vp.dbcnf.addText");
					} catch (PError e)
					{ }

					html = "html/vp/dbcnf/selecttext.html";
				} else
				{
					//if (!com.cap("viewUsers")) { return ""; }
					html = "html/vp/dbcnf/addtext.html";
				}

			} else
			if (subSect.equals("editText"))
			{
				String p1 = com.getReq().getParameter("p1");

				if (p1 != null && p1.equals("save") )
				{
					try
					{
						com.getHandler().handle("vp.dbcnf.editText");
					} catch (PError e)
					{ }

					html = "html/vp/dbcnf/selecttext.html";
				} else
				{
					//if (!com.cap("viewUsers")) { return ""; }
					html = "html/vp/dbcnf/edittext.html";
				}

			} else
			if (subSect.equals("removeText"))
			{
				try
				{
					com.getHandler().handle("vp.dbcnf.removeText");
				} catch (PError e)
				{ }

				html = "html/vp/dbcnf/selecttext.html";

			} else


			if (subSect.equals("visBillettservice"))
			{
				if (!com.cap("viewBillettservice")) { return ""; }

				html = "html/admin/sokbs.htm";
			} else
			if (subSect.equals("visInsertBillettservice"))
			{
				if (!com.cap("insertBillettservice")) { return ""; }

				html = "html/admin/insertbs.htm";
			} else
			if (subSect.equals("insertBillettservice"))
			{
				if (!com.cap("insertBillettservice")) { return ""; }

				try
				{
					com.getHandler().handle("admin.insertBillettservice");
					html = "html/admin/sokbs.htm";
				} catch (PError e)
				{
					if (e.msg().equals("ingenLedigPlasser") )
					{
						com.getUser().set("message", "Det er ingen ledige plasser p&aring; billetten.", false);
						html = "html/pres/main.htm";

					} else
					if (e.msg().equals("billettError") )
					{
						com.getUser().set("message", "Ugyldig billett-nummer", false);
						html = "html/pres/main.htm";
					}
				}
			} else
			if (subSect.equals("listUser"))
			{
				if (!com.cap("viewUsers")) { return ""; }

				html = "html/admin/listusers.htm";
			} else
			if (subSect.equals("presMail"))
			{
				if (!com.cap("presSendMail")) { return ""; }

				html = "html/admin/presmail.htm";
			} else
			if (subSect.equals("presSendMail"))
			{
				if (!com.cap("presSendMail")) { return ""; }

				html = "html/admin/sendpresmail.htm";
			}


		} else
		{
			html = "html/vp/main.html";
		}

		return html;
	}

	private void link(String s)
	{
		try
		{
			com.getHandler().handle(s);
		} catch (PError e)
		{
			com.outl("Error: " + e.getMessage() );
		}
	}




	// klasse vars
	String[] s;
	Com com;
	Sql db;
	int num;
	int tempNr;


}
