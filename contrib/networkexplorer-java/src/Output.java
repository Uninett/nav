/*
 * $Id$
 *
 * Copyright 2002-2004 Norwegian University of Science and Technology
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


import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.util.Stack;

import javax.servlet.ServletContext;

public class Output
{
	private Com com;
	private Handler h;
	private String html;
	private ServletContext sc;

	public Output(String InHtml, Com InCom, ServletContext sc)
	{
		html = InHtml;
		com = InCom;
		this.sc = sc;
		//PATH = com.getConf().get("ServletRoot");
	}

	public void begin()
	{
		h = com.getHandler();
		try
		{
			if (html.endsWith("html") || html.endsWith("htm"))
			{
				com.setContentType("text/html"); // Required for HTTP

				char c;
				InputStream istream = sc.getResourceAsStream("WEB-INF/" + html);
				if (istream == null) {
					com.out("(Output: File not found: " + html + ")");
					return;
				}
				BufferedReader in = new BufferedReader(new InputStreamReader(istream));
				Stack stack = new Stack();
				stack.push(in);

				while (!stack.empty() )
				{
					in = (BufferedReader)stack.pop();

					while (in.ready())
					{
						c = (char)in.read();

						if (c == '[')
						{
							in.mark(50);
							c = (char)in.read();
							if (c == '/')
							{
								getTag(in);
							} else
							{
								com.out("[");
								in.reset();
							}
						} else
						// virtual includes
						if (c == '<')
						{
							in.mark(50);
							c = (char)in.read();
							if (c == '!')
							{
								char[] cin = new char[20];
								in.read(cin, 0, 20);
								String s = new String(cin);
								if (s.equals("--#include virtual=\"") )
								{
									cin = new char[20];
									int i = 0;

									c = (char)in.read();
									while (c != '\"')
									{
										cin[i] = c;
										c = (char)in.read();
										i++;
									}
									s = new String(cin);
									s = s.trim();

									while (c != '>')
									{
									c = (char)in.read();
									}


									//html = "html/" + s;

									istream = sc.getResourceAsStream("WEB-INF/html/" + s);
									if (istream == null) {
										com.out("(Virtual include: File not found: " + s + ")");
									} else {
										stack.push(in);
										in = new BufferedReader(new InputStreamReader(istream));
									}

									//<!--#include virtual="menu.tdp" -->
								} else
								{
									com.out("<");
									in.reset();
								}
							} else
							{
								com.out("<");
								in.reset();
							}

						} else
						{
							try
							{
								com.getOut().print(c);
							}
							catch (java.io.IOException e)
							{ }
						}
					}
				}
			} else
			{
				// just send the file, no parsing
				sendfile(html, com);
			}



		}
		catch (java.io.IOException e)
		{
			// Config-fil mangler, bruker kun default-verdier. Skriver likevel en advarsel.
			error("Error1: " + e.getMessage());
		}

	}

	private void getTag(BufferedReader in)
	{
		getTag(in, 0);
	}

	private void getTag(BufferedReader in, int tempNr)
	{
		char c = 0;
		int num = 0;
		StringBuffer s = new StringBuffer();

		try
		{
			while (c != ']')
			{
				c = (char)in.read();
				if (c == '(')
				{
					StringBuffer s2 = new StringBuffer();
					c = (char)in.read();

					while (c != ')')
					{
						s2.append(c);
						c = (char)in.read();
						// missing error-handler
					}
					if (s2 != null)
					{
						num = Integer.parseInt(s2.toString());
					}
					c = (char)in.read();
				}

				if (c != ']')
				{
					s.append(c);
				}
				// missing error-handler
			}

			if (s != null)
			{
				if (s.toString().length() >= 8 && s.toString().substring(0, 8).equals("template"))
				{
					template(num, h.getLoops(s.toString(), num), s.toString() );

				} else
				{
					h.handle(s.toString(), num, tempNr);
				}
			}

		}
		catch (java.io.IOException e)
		{ error("Error2: " + e.getMessage()); }

	}

	private void template(int num, int loop, String s)
	{
		for (int i = 0; i < loop; i++)
		{

			try
			{
				InputStream istream = sc.getResourceAsStream("WEB-INF/" + html + ".temp");
				if (istream == null) {
					com.out("(Template: File not found: " + html + ".temp)");
					return;
				}
				BufferedReader in = new BufferedReader(new InputStreamReader(istream));

				char c;

				while (in.ready())
				{
					c = (char)in.read();

					if (c == '[')
					{
						in.mark(50);
						c = (char)in.read();
						if (c == '/')
						{
							getTag(in, i+1);

						String antLoops = com.get(s);
						if (antLoops != null)
						{
							loop = Integer.parseInt(antLoops);
							if (loop == 0)
							{
								break;
							}
						}


						} else
						{
							in.reset();
						}
					} else
					{
						try
						{
							com.getOut().print(c);
						}
						catch (java.io.IOException e)
						{ }
					}
				}
			}
			catch (java.io.IOException e)
			{
				// Config-fil mangler, bruker kun default-verdier. Skriver likevel en advarsel.
				error("Error1: " + e.getMessage());
			}

		}
	}

	public static void sendfile(String file, Com com)
	{
		if (file.endsWith("java"))
		{
			com.setContentType("text/html"); // Required for HTTP
			com.out("<html>\n<head>\n</head>\n<body>\n<pre>\n");
		}
		if (file.endsWith("zip"))
		{
			com.setContentType("application/zip"); // Required for HTTP
		}
		if (file.substring(file.length()-2, file.length()).equals("gz"))
		{
			com.setContentType("application/x-gzip"); // Required for HTTP
		}
		if (file.endsWith("doc"))
		{
			com.setContentType("application/msword"); // Required for HTTP
		}
		if (file.endsWith("xls"))
		{
			com.setContentType("application/x-excel"); // Required for HTTP
		}
		if (file.endsWith("pdf"))
		{
			com.setContentType("application/pdf"); // Required for HTTP
		}

		try
		{

			BufferedReader in = new BufferedReader(new FileReader(file));

			while (in.ready())
			{
				com.bout( (char)in.read());
			}

			if (file.endsWith("java"))
			{
				com.out("\n</pre>\n</body>\n</html>");
			}

			com.getOut().close();

			if (com.getDelOutput() )
			{
				File f = new File(file);
				f.delete();
			}

		} catch (Exception e) {}

	}

	private void error(String err)
	{
		try
		{
			com.getOut().print(err);
		}
		catch (java.io.IOException e)
		{ }
	}

}

