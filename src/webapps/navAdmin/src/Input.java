/*
 * Handler.java
 *
 */

import java.io.*;
import java.util.*;
import java.text.*;
import javax.servlet.http.*;

import com.oreilly.servlet.MultipartRequest;
import com.oreilly.servlet.ParameterParser;


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
		if (req.getParameter("mailpw") != null)
		{
			String login = req.getParameter("mailpw");
			try
			{
				com.getHandler().handle("admin.mailPw", 0);
				html = "html/mailpw.htm";
				return;
			}
			catch (PError p)
			{
				com.out("msg: " + p.getError() + "<br>\n");
				html = "html/error.htm";
			}
		}

			String sect;

			if (sectionUpload())
			{
				html = "html/oving/innlever.htm";
				sect = null;
			} else
			{
				sect = req.getParameter("section");
			}

			if (sect != null)
			{
				if (sect.equals("logout"))
				{
					sectionLogout();
				} else
				if (sect.length() > 0)
				{
					html = h.handleSection(sect);
				}
			}
/*
			if (html == null)
			{
				html = "html/main.html";
			} else
			if (html.equals("") )
			{
				html = "html/main.html";
			}
*/
			if (html == null || html.equals("") )
			{
				if (com.getUser().getAuth())
				{
/*
					if (com.getUser().isAdmin())
					{
						if (com.getUser().getValgtKlasse())
						{
							html = "html/admin/velg_oving.htm";
						} else
						{
							html = "html/admin/multiklasse.htm";
						}
					} else
					{

						if (com.getUser().getValgtKlasse())
						{
							html = "html/oving/innlever.htm";
						} else

						{
							html = "html/nav/main.html";
						}
					}
*/
					html = "html/nav/main.html";

				} else
				{
					html = "html/main.html";
				}
			}


	}

	private void sectionLogout()
	{
		com.getUser().logout();
		html = "html/main.html";

	}
/*
	private void sectionSave()
	{
		String[] info = com.getDb().exec("select oving from ovinger where login='kristian'");

		if (info[0] != null)
		{
			String s = info[0];

			try
			{
				File f = new File("/tmp/ting.doc");
				PrintWriter out = new PrintWriter(new FileOutputStream(f));

				out.write(s);
				out.close();
			}
			catch (Exception e) { }
		}


	}

	private boolean sectionUpload()
	{

		Random rand = new Random();
		StringBuffer buf = new StringBuffer();

		for (int j = 0; j < 10; j++)
		{

			int i = rand.nextInt(26);

			i += 97;

			buf.append("" + (char)i);
		}

		String dirNavn = "/tmp/oving.tmp/" + buf.toString();

		try
		{
			File dir = new File(dirNavn);
			dir.mkdirs();

			MultipartRequest multi = new MultipartRequest(req, dirNavn, 5 * 1024 * 1024);

			// param recived
			int ovingnr = 0;
			Enumeration params = multi.getParameterNames();
			while (params.hasMoreElements())
			{
				String name = (String)params.nextElement();
				if (name.equals("ovingnr"))
				{
					ovingnr = Integer.parseInt(multi.getParameter(name));
					break;
				}
			}

			if (ovingnr == 0)
			{
				throw new Exception("Oving number is missing");
			}

			// files received
			String inFiles;
			File f;
			Enumeration files = multi.getFileNames();
			do
			{
				String name = (String)files.nextElement();
				//String filename = multi.getFilesystemName(name);
				//String type = multi.getContentType(name);
				f = multi.getFile(name);

				//com.out("name: " + name);
				//com.out("filename: " + filename);
				//com.out("type: " + type);
	        	//if (f != null)
	        	//{
				//	com.out("length: " + f.length());
				//	com.out("<br>\n");
				//}
			} while (files.hasMoreElements());

			BufferedReader in = new BufferedReader(new FileReader(f.getAbsolutePath()));
			StringBuffer infile = new StringBuffer();

			int c;

//NUL
//ASCII 0. You should represent this by `\0' (a backslash and an ASCII `0' character).
//\
//ASCII 92, backslash. Represent this by `\\'.
//'
//ASCII 39, single quote. Represent this by `\''.
//"
//ASCII 34, double quote. Represent this by `\"'.

			int a = 0;
			int b = 0;
			int c2 = 0;
			int d = 0;
			int e = 0;


			while (in.ready())
			{
				c = in.read();

				if (c == 0)
				{ a++;
					infile.append("\\0");
				} else
				if (c == 34)
				{ b++;
					infile.append("\\\"");
				} else
				if (c == 39)
				{
					infile.append("\\'");
				} else
				if (c == 92)
				{ d++;
					infile.append("\\\\");
				} else
				{
					infile.append((char)c);
				}

			}

			com.out("a: " + a + "<br>\n");
			com.out("b: " + b + "<br>\n");
			com.out("c: " + c2 + "<br>\n");
			com.out("d: " + d + "<br>\n");

			f.delete();
			dir.delete();
			File parent = new File(dir.getParent());
			parent.delete();

			String[] info;

			info = com.getDb().exec("select login from ovinger where login='" + com.getUser().getLogin()
							+ "' and ovingnr='" + ovingnr + "';");

			if (info[0] != null)
			{
				com.getDb().exec("update ovinger set oving='" + infile.toString() + "' where login='" + com.getUser().getLogin()
							+ "' and ovingnr='" + ovingnr + "';");
			} else
			{
				com.getDb().exec("insert into ovinger values ('" + com.getUser().getLogin() + "','"
							+ ovingnr + "','Enda ikke evaluert','" + infile.toString() + "');");
			}


		}
    	catch (Exception e)
		{
			if (e.getMessage().equals("Posted content type isn't multipart/form-data"))
			{
				return false;
			} else
			if (e.getMessage().equals("Oving number is missing"))
			{
				return false;
			}

		}

		return true;
	}

*/

	private boolean sectionUpload()
	{
/*
		Random rand = new Random();
		StringBuffer buf = new StringBuffer();

		int min = 0;
		int max = 25;

		for (int j = 0; j < 10; j++)
		{
			int x = rand.nextInt();
			if (x < 0)
			{
				x *= -1;
			}
			x = (x%(max - min + 1) + min);
			x += 97;
			buf.append("" + (char)x);

			// java 2 syntax
			//int i = rand.nextInt(26);
			//i += 97;
			//buf.append("" + (char)i);
		}

		String dirNavn = "/tmp/oving.tmp/" + buf.toString();

		try
		{
			File dir = new File(dirNavn);
			dir.mkdirs();

			MultipartRequest multi = new MultipartRequest(req, dirNavn, 5 * 1024 * 1024);

			// param recived
			int ovingnr = 0;
			Enumeration params = multi.getParameterNames();
			while (params.hasMoreElements())
			{
				String name = (String)params.nextElement();
				if (name.equals("ovingnr"))
				{
					ovingnr = Integer.parseInt(multi.getParameter(name));
					break;
				}
			}

			if (ovingnr == 0)
			{
				throw new Exception("Oving number is missing");
			}

			// files received
			File f;
			Enumeration files = multi.getFileNames();
			do
			{
				String fname = (String)files.nextElement();
				//String filename = multi.getFilesystemName(name);
				//String type = multi.getContentType(name);
				f = multi.getFile(fname);

				//com.out("name: " + name);
				//com.out("filename: " + filename);
				//com.out("type: " + type);
	        	//if (f != null)
	        	//{
				//	com.out("length: " + f.length());
				//	com.out("<br>\n");
				//}
			} while (files.hasMoreElements());

			File outf = new File(com.getConf().get("UploadRoot") + com.getUser().getKlasse() + "/ov" + ovingnr +
									"/" + com.getUser().getLogin() );

			if (!outf.isDirectory())
			{
				outf.mkdirs();
			}

			outf = new File("/home/kristian/ovinger/" + com.getUser().getKlasse() + "/ov" + ovingnr +
									"/" + com.getUser().getLogin() + "/" + f.getName() );

			copyFile(f, outf);

			f.delete();
			dir.delete();
			File parent = new File(dir.getParent());
			parent.delete();

			String[] info;

			info = com.getDb().exec("select login from ovinger where login='" + com.getUser().getLogin()
							+ "' and klasse='" + com.getUser().getKlasse() + "' and ovingnr='" + ovingnr + "';");

			// Get current time
			Calendar calendar = new GregorianCalendar();
			Date currentTime = calendar.getTime();

			// Format the current time.
			SimpleDateFormat formatter = new SimpleDateFormat("dd/MM/yyyy G',' HH:mm:ss");
			String dato = formatter.format(currentTime);

			if (info[0] != null)
			{
				// sett ny path til øvingen
				com.getDb().exec("update ovinger set oving='" + outf.getAbsolutePath() + "' where login='" + com.getUser().getLogin()
							+ "' and klasse='" + com.getUser().getKlasse() + "' and ovingnr='" + ovingnr + "';");

				// sett ny dato for upload
				com.getDb().exec("update ovinger set dato='" + dato + "' where login='" + com.getUser().getLogin()
							+ "' and klasse='" + com.getUser().getKlasse() + "' and ovingnr='" + ovingnr + "';");

				// sett comile til 'unknown'
				com.getDb().exec("update ovinger set compile='unknown' where login='" + com.getUser().getLogin()
							+ "' and klasse='" + com.getUser().getKlasse() + "' and ovingnr='" + ovingnr + "';");

			} else
			{
				com.getDb().exec("insert into ovinger values ('" + com.getUser().getLogin() + "','"	+ com.getUser().getKlasse() +
								"','" + ovingnr + "','" + dato + "','Enda ikke evaluert','unknown','" +
								outf.getAbsolutePath() + "','');");
			}


			FileTester ft = new FileTester(com, outf.getAbsolutePath() );

			ft.start();


		}
    	catch (Exception e)
		{
			if (e.getMessage().equals("Posted content type isn't multipart/form-data"))
			{
				return false;
			} else
			if (e.getMessage().equals("Oving number is missing"))
			{
				return false;
			}

		}

		return true;
		*/
		return false;
	}

	private void copyFile(File inf, File outf)
	{
		try
		{
			BufferedReader in = new BufferedReader(new FileReader(inf.getAbsolutePath()));
			PrintWriter out = new PrintWriter(new FileOutputStream(outf));

			while (in.ready())
			{
				out.write(in.read());
			}
			out.close();
		}
		catch (Exception e)
		{
			com.out("FileWriteError: " + e.getMessage() + "<br>\n");
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

