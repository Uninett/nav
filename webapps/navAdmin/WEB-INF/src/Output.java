/*
 * Output.java
 *
 */


import java.io.*;
import java.util.*;

import javax.servlet.*;
import javax.servlet.http.*;

public class Output
{
	public Output(String InHtml, Com InCom)
	{
		html = InHtml;
		com = InCom;
		PATH = com.getConf().get("ServletRoot");
	}

	public void begin()
	{
		h = com.getHandler();
		try
		{
			if ((html.substring(html.length()-4, html.length()).equals("html")) ||
				(html.substring(html.length()-3, html.length()).equals("htm")) )
			{
				com.setContentType("text/html"); // Required for HTTP

				char c;
				BufferedReader in = new BufferedReader(new FileReader(PATH + html));
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

									stack.push(in);
									//html = "html/" + s;
									in = new BufferedReader(new FileReader(PATH + "html/" + s));

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
			//System.out.println("Konfigurasjonsfil 'Bowling.conf' mangler. Bruker standard-konfigurasjon.");
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
					try
					{
						h.handle(s.toString(), num, tempNr);
					}
					catch (PError p)
					{ }
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
				BufferedReader in = new BufferedReader(new FileReader(PATH + html + ".temp"));

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
				//System.out.println("Konfigurasjonsfil 'Bowling.conf' mangler. Bruker standard-konfigurasjon.");
				error("Error1: " + e.getMessage());
			}

		}
	}

	public static void sendfile(String file, Com com)
	{
		if (file.substring(file.length()-4, file.length()).equals("java"))
		{
			com.setContentType("text/html"); // Required for HTTP
			com.out("<html>\n<head>\n</head>\n<body>\n<pre>\n");
		}
		if (file.substring(file.length()-3, file.length()).equals("zip"))
		{
			com.setContentType("application/zip"); // Required for HTTP
		}
		if (file.substring(file.length()-2, file.length()).equals("gz"))
		{
			com.setContentType("application/x-gzip"); // Required for HTTP
		}
		if (file.substring(file.length()-3, file.length()).equals("doc"))
		{
			com.setContentType("application/msword"); // Required for HTTP
		}
		if (file.substring(file.length()-3, file.length()).equals("xls"))
		{
			com.setContentType("application/x-excel"); // Required for HTTP
		}
		if (file.substring(file.length()-3, file.length()).equals("pdf"))
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

			if (file.substring(file.length()-4, file.length()).equals("java"))
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

	final String PATH;
	//ServletOutputStream out;
	Com com;
	Handler h;
	String html;

}

