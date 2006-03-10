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
			/*
			if (s[1].equals("showConfig"))
			{
				showConfig();
			} else
			if (s[1].equals("antUserTreff"))
			{
				antUserTreff();
			}
			*/




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
			/*
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
			*/






		}
	}



	/************************************************************
	* Level 1 functions											*
	* user.*													*
	************************************************************/

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


	/************************************************************
	* Level 2 functions											*
	* user.<>.*													*
	************************************************************/

	/* [/vp.dbcnf.selectText]
	 * Viser alle tekster som er lagt inn for editering
	 */
	/*
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
	*/

	/* [/vp.dbcnf.addText]
	 * Lagrer ny tekst i database
	 */
	/*
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
	*/

	/* [/vp.dbcnf.editText]
	 * Editerer info om elementer i en tekst
	 */
	/*
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
	*/

	/* [/vp.dbcnf.removeText]
	 * Editerer info om elementer i en tekst
	 */
	/*
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
	*/

	/* [/vp.dbcnf.editField]
	 * Skriver ut eksisterende info i feltene
	 */
	/*
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
	*/











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
	int num;
	int tempNr;


}
