/*
 * NTNU ITEA Nettnu prosjekt
 *
 * Skrvet av: Kristian Eide
 *
 */

import java.util.*;

import java.io.*;
import java.net.*;


class Input
{
	// Default verdier
	//public static String vPServerURLDefault = "http://www.nav.ntnu.no/vPServerNG/servlet/vPServer";
	public static String vPServerURLDefault = "https://beta.nav.ntnu.no/vPServer/servlet/vPServer";
	public static String lastURLDefault = "http://www.nav.ntnu.no/vlanPlotNG/common/vPLast/last_ny.pl";
	public static String cricketURLDefault = "http://www.nav.ntnu.no/~cricket/";
	public static String netflowURLDefault = "http://manwe.itea.ntnu.no/";

	//http://www.nav.ntnu.no/vPServer/servlet/vPServer?section=boks&request=listBoks&boksid=271&kat=sw
	//http://www.nav.ntnu.no/vPServerNG/servlet/vPServer?section=boks&boksid=271&kat=&request=listConfig,listRouterGroups,listBoks


	// URL for vPServer-modulen
	public static String vPServerURL;
	
	public static String rootURL;

	// URL for last-scriptet
	public static String lastURL;

	// URL til cricket
	public static String cricketURL;

	// URL til Netflow, hvis det er aktivt
	public static String netflowURL;

	public static String sessionid;
	public static String authuser;


	Com com;
	// Caches
	Hashtable netCache = new Hashtable();
	Hashtable boksCache = new Hashtable();


	Vector listRouters;
	Vector listRouterLinks;
	Vector listNetRouters;
	Vector listNetLinks;
	Vector listRouterGroups;
	Vector listLinkInfo;


	Vector listCPULast;
	Vector listLinkLast;
	Vector listNetLast;

	int[][] nettelXY = new int[3][];
	int[] index;

	//boolean fetchConfig = true;
	boolean fetchConfig = false;

	ServerFetcher serverFetcher;
	Vector inputQ;

	public Input(Com InCom)
	{
		com = InCom;
	}

	public void getDefaultInputNotify(int grp)
	{
		//if(!ht.containsKey(new Integer(grp)))
		//{


	}

	public Hashtable getDefaultInput(int grp)
	{
		/*
		if(netCache.containsKey(new Integer(grp))) {
			com.d("Found grp " + grp + " in cache! :-)", 2);
			return (Hashtable)netCache.get(new Integer(grp));
		}
		*/

		// Ikke i cache, så vi må hente struktur-info fra server
		Vector v = new Vector();
		if (!Net.setConfig) v.addElement("listConfig");

		String[] def = {
			"listRouters",
			"listRouterGroups",
			"listRouterXY"
		};

		String[] s = new String[v.size()+def.length];
		for (int i=0; i < v.size(); i++) {
			s[i] = (String)v.elementAt(i);
		}
		for (int i=0; i < def.length; i++) {
			s[v.size()+i] = def[i];
		}

		String param = "gruppeid=" + grp;
		Hashtable h = fetch(s, param, vPServerURL);

		netCache.put(new Integer(grp), h);
		return h;
	}

	// Fetch fra vPServer
	public Hashtable fetch(String[] req, String param, String serverURL)
	{
		return fetch(req, param, serverURL, null);
	}
	public Hashtable fetch(String[] req, String param, String serverURL, String hashKey)
	{
		// Check if we have this in boksCache
		/*
		if (hashKey != null && boksCache.containsKey(hashKey)) {
			com.d("fetch(): Found hashKey: " + hashKey + " in cache", 2);
			return (Hashtable)boksCache.get(hashKey);
		}
		*/

		Hashtable ret;

		try
		{
			StringBuffer b = new StringBuffer();

			// lag URL
			b.append(serverURL);
			b.append("?section=boks&");
			if (param.length() > 0)
			{
				b.append(param + "&");
			}
			b.append("request=");
			for (int i = 0; i < req.length; i++)
			{
				b.append(req[i]);
				if ((i+1) < req.length)
				{
					b.append(",");
				}
			}

			{
				long[] lastInterval = com.getLastInterval();
				b.append("&time=" + lastInterval[0] + ",");
				b.append( (lastInterval[1] >= 0 ? "0" : ""+lastInterval[1]) );
				b.append("&" + (com.getTidAvg() ? "type=avg" : "type=max"));
			}

			//b.append("&");
			//b.append("send=Send\n");

			com.d("URL: " + b.toString(), 2);
			URL url = new URL(b.toString() );
			inputQ = new Vector();
			com.d("Create new ServerFetcher",2);
			serverFetcher = new ServerFetcher(url, inputQ);
			serverFetcher.start();
			synchronized (inputQ) {
				if (inputQ.isEmpty()) {
					com.d("Waiting on inputQ...",2);
					inputQ.wait();
				}
				com.d("Wait over",2);
				ret = (Hashtable)inputQ.elementAt(0);
				inputQ.removeElementAt(0);
			}

		} catch (Exception e) {
			com.d("Error: " + e.getMessage(), 0);
			throw new ServerFetchException("Error: " + e.getMessage());
		}

		if (hashKey != null) boksCache.put(hashKey, ret);
		return ret;
	}

	class ServerFetcher extends Thread {
		private URL url;
		private Vector q;

		public ServerFetcher(URL myUrl, Vector queue) {
			url = myUrl;
			q = queue;
		}

		public void run() {
			try {
				String name = null;
				Hashtable ret = new Hashtable();
				URLConnection connection = url.openConnection();
				connection.setRequestProperty("Cookie", "nav_sessid="+sessionid);
				connection.connect();

				BufferedReader in = new BufferedReader(new InputStreamReader(connection.getInputStream()));
				String line;
				Hashtable hash = null;
				while ((line = in.readLine()) != null) {
						if (line.equals("---")) {
							synchronized (q) {
								System.out.println("  Adding 1");
								q.addElement(ret);
								q.notify();
							}
							ret = new Hashtable();
							continue;
						} else
						if (line.length() >= 4 && line.substring(0, 4).equals("list")) {
							ret.put(line, hash = new Hashtable());
							continue;
						} else {
							String[] s = misc.tokenize(line, "^");
							hash.put(s[0], s);
						}
				}
				System.out.println("About to enter q");
				synchronized (q) {
					q.addElement(ret);
					q.notify();
				}
			} catch (Exception e) {
				com.d("Exception: " + e.getMessage(), 0);
			}
		}
	}

	public Hashtable getDefaultLast()
	{
		try {
			synchronized (inputQ) {
				if (inputQ.isEmpty()) {
					inputQ.wait();
				}
				Hashtable ht = (Hashtable)inputQ.elementAt(0);
				inputQ.removeElementAt(0);
				return ht;
			}
		} catch (Exception e) {
			com.d("Error: " + e.getMessage(), 0);
		}
		return null;
	}

	public Hashtable getDefaultLast2()
	{
		// kun ruter-linker
		String[] param = new String[4];
		StringBuffer b = new StringBuffer();
		Hashtable dup = new Hashtable();

		com.d("Now in getDefaultLast", 4);

		//Hashtable h = getDefaultInput(com.getNet().getVisGruppe());
		//h = (Hashtable)h.get("listRouterLinks");

		com.d("  Adding links", 4);

		// Legg til linkId'ene
		String type;

		if (com.getNet().getVisNettel() == null || com.getNet().getVisNettel().getKat().equals("gw"))
		{
			type = "net=";
		} else
		{
			type = "sw=";
		}
		b.append(type);

		Enumeration e = com.getNet().getLinkHash().elements();
		while (e.hasMoreElements())
		{
			Link l = (Link)e.nextElement();

			if (!dup.containsKey(""+l.getId()) )
			{
				b.append(l.getId() + ",");
				dup.put(""+l.getId(),"");
			}

			/*
			if (l.getKat().equals("net"))
			{
				net.append(l.getId() + ",");
			} else
			if (l.getKat().equals("sw"))
			{
				sw.append(l.getId() + ",");
			}
			*/
		}

		//if (!net.toString().equals("net=")) net.setLength(net.length()-1); else net.append("0");
		//if (!sw.toString().equals("sw=")) sw.setLength(sw.length()-1); else sw.append("0");
		if (!b.toString().equals(type)) b.setLength(b.length()-1); else b.append("0");

		if (com.getNet().getVisNettel() == null || com.getNet().getVisNettel().getKat().equals("gw"))
		{
			param[0] = b.toString();
			param[1] = "sw=0";
		} else
		{
			param[0] = "net=0";
			param[1] = b.toString();
		}

		long[] lastInterval = com.getLastInterval();
		param[2] = "time=" + lastInterval[0] + ",";
		param[2] += (lastInterval[1] >= 0) ? "now" : ""+lastInterval[1];
		param[3] = com.getTidAvg() ? "type=avg" : "type=max";
		/*
		if (lastTid[1] >= 0)
		{
			param[2] = "time=" + lastTid[0] + ",now";
		} else
		{
			param[2] = "time=" + lastTid[0] + "," + lastTid[1];
		}
		*/


		/*
		if (com.getTidAvg())
		{
			param[3] = "type=avg";
		} else
		{
			param[3] = "type=max";
		}
		*/

		//com.d("Fetching last from: " + lastURL, 3);

		Hashtable h = fetch(param, lastURL);

		/*
		//if (true) return h;

		Hashtable link = (Hashtable)h.get("listLinkLast");
		Hashtable cpu = (Hashtable)h.get("listCPULast");
		Hashtable tmp;

		// Put listSwitchlast inn i listCPUlast
		tmp = (Hashtable)h.get("listSwitchLast");
		e = tmp.elements();
		while (e.hasMoreElements())
		{
			String[] s = (String[])e.nextElement();
			cpu.put(s[0], s);
		}

		// Put listStamLast inn i listLinkLast
		tmp = (Hashtable)h.get("listStamLast");
		e = tmp.elements();
		while (e.hasMoreElements())
		{
			String[] s = (String[])e.nextElement();
			link.put(s[0], s);
		}

		// Put listElinkLast inn i listLinkLast
		tmp = (Hashtable)h.get("listElinkLast");
		e = tmp.elements();
		while (e.hasMoreElements())
		{
			String[] s = (String[])e.nextElement();
			link.put(s[0], s);
		}

		// Put listLanLast inn i listLinkLast
		tmp = (Hashtable)h.get("listLanLast");
		e = tmp.elements();
		while (e.hasMoreElements())
		{
			String[] s = (String[])e.nextElement();
			link.put(s[0], s);
		}

		// Put listSwitchPortlast inn i listLinkLast
		tmp = (Hashtable)h.get("listSwitchPortLast");
		e = tmp.elements();
		while (e.hasMoreElements())
		{
			String[] s = (String[])e.nextElement();
			link.put(s[0], s);
		}
		*/


		return h;



/*
		listCPULast = v[4];
		listLinkLast = v[0];
		listNetLast = v[2];
		Vector elinkLast = v[3];

		// putt elink inn i netLast
		for (int i = 0; i < elinkLast.size(); i++)
		{
			listNetLast.addElement(elinkLast.elementAt(i));
		}


		for (int i = 0; i < listCPULast.size(); i++)
		{
			com.d("" + i + ": " + ((String[])listCPULast.elementAt(i))[0] + ", " + ((String[])listCPULast.elementAt(i))[1] ,1 );

		}
*/

	}

	// Fetch fra last-script
	public Hashtable fetch(String param[], String serverURL)
	{
		Hashtable ret = new Hashtable();
		String name = null;
		Hashtable hash = null;

		try
		{
			StringBuffer b = new StringBuffer();

			// lag URL
			b.append(serverURL + "?");

			for (int i = 0; i < param.length; i++)
			{
				b.append(param[i]);
				if ((i+1) < param.length)
				{
					b.append("&");
				}

			}
			//b.append("send=Send\n");

			com.d("URL: " + b.toString(), 2);

			URL url = new URL(b.toString() );
			URLConnection connection = url.openConnection();
			connection.connect();

			BufferedReader in = new BufferedReader(new InputStreamReader(connection.getInputStream()));
			String line;
			while ((line = in.readLine()) != null)
			{
				if (line.length() >= 4 && line.substring(0, 4).equals("list"))
				{
					if (name != null) ret.put(name, hash);
					name = line;
					hash = new Hashtable();
					continue;
				}
				String[] s = misc.tokenize(line, ",");
				hash.put(s[0], s);
			}
			if (name != null) ret.put(name, hash);
		}
		catch (Exception e)
		{
			com.d("Error: " + e.getMessage(), 0);
		}
		return ret;
	}


























/*
	public void getDefaultInput()
	{
		String[] s;
		if (fetchConfig)
		{
			s = new String[8];
		} else
		{
			s = new String[7];
		}

		s[0] = "listRouters";
		s[1] = "listRouterLinks";
		s[2] = "listNetRouters";
		s[3] = "listNetLinks";
		s[4] = "listRouterGroups";
		s[5] = "listLinkInfo";
		s[6] = "listRouterXY";

		if (fetchConfig)
		{
			s[7] = "listConfig";
		}

		String param = "gruppeId=" + com.getNet().getVisGruppe();

		Vector[] v = fetch(s, param, "http://bigbud.itea.ntnu.no/vlanPlot/vPServer/vPServer");

		listRouters = v[0];
		listRouterLinks = v[1];
		listNetRouters = v[2];
		listNetLinks = v[3];
		listRouterGroups = v[4];
		listLinkInfo = v[5];


		nettelXY[0] = new int[v[0].size()+v[3].size() ];
		nettelXY[1] = new int[v[0].size()+v[3].size() ];
		nettelXY[2] = new int[v[0].size()+v[3].size() ];

		for (int i = 0; i < v[6].size(); i++)
		{
			s = (String[])v[6].elementAt(i);

			nettelXY[0][i] = Integer.parseInt(s[0]);
			nettelXY[1][i] = Integer.parseInt(s[1]);
			nettelXY[2][i] = Integer.parseInt(s[2]);

		}

		if (fetchConfig)
		{
			fetchConfig = false;

			Cnf cnf = new Cnf(v[7]);
			com.setCnf(cnf);

			//String[] scnf = cnf.get("dbCnf.nettel.1");
			//for (int i = 0; i < scnf.length; i++)
			//{
			//	com.d("cnf: " + scnf[i] + "|\n", 2);
			//}

		}
	}
*/

/*
	public void getDefaultLast()
	{
		// kun ruter-linker
		String[] param = new String[4];
		StringBuffer b = new StringBuffer();

		Vector routerLinks = com.getInput().getListRouterLinks();
		Vector netLinks = com.getInput().getListNetLinks();

		b.append("net=");

		// legg til id for vanlige linker
		for (int i = 0; i < routerLinks.size(); i++)
		{
			String[] s = (String[])routerLinks.elementAt(i);

			for (int j = 1; j < s.length; j++)
			{
				String[] linkInfo = misc.tokenize(s[j], ",");
				b.append(linkInfo[1] + ",");
			}
		}

		// legg til id for stam-linker
		for (int i = 0; i < netLinks.size(); i++)
		{
			String[] s = (String[])netLinks.elementAt(i);

			for (int j = 1; j < s.length; j++)
			{
				String[] linkInfo = misc.tokenize(s[j], ",");
				b.append(linkInfo[1] + ",");
			}
		}


		b.setLength(b.length()-1);

		param[0] = b.toString();
		param[1] = "sw=0";
		//param[2] = "time=-3600,now";

		long[] lastTid = com.getLastTid();

		if (lastTid[1] >= 0)
		{
			param[2] = "time=" + lastTid[0] + ",now";
		} else
		{
			param[2] = "time=" + lastTid[0] + "," + lastTid[1];
		}

		if (com.getTidAvg() )
		{
			param[3] = "type=avg";
		} else
		{
			param[3] = "type=max";
		}

		Vector[] v = fetch(param, "http://bigbud.itea.ntnu.no/cgi-bin/vPLast/last.pl");

		listCPULast = v[4];
		listLinkLast = v[0];
		listNetLast = v[2];
		Vector elinkLast = v[3];

		// putt elink inn i netLast
		for (int i = 0; i < elinkLast.size(); i++)
		{
			listNetLast.addElement(elinkLast.elementAt(i));
		}


		for (int i = 0; i < listCPULast.size(); i++)
		{
			com.d("" + i + ": " + ((String[])listCPULast.elementAt(i))[0] + ", " + ((String[])listCPULast.elementAt(i))[1] ,1 );

		}

	}
*/

	public Vector[] getLastData(Vector nettel, Vector nettelLinks)
	{
		// hent ut alle id'er
		Vector net = new Vector();
		Vector sw = new Vector();

		for (int i = 0; i < 3; i++)
		{
			String[] s = (String[])nettelLinks.elementAt(i);
			for (int j = 1; j < s.length; j++)
			{
				int nettelId = Integer.parseInt( (misc.tokenize(s[j], ","))[0] );
				String linkId = (misc.tokenize(s[j], ","))[1];
				String type = (misc.tokenize(s[j], ","))[2];

/*
				if (type.equals("sw") )
				{
					sw.addElement(linkId);
				} else
				{
					net.addElement(linkId);
					if (type.equals("gw"))
					{
						String linkIdInn = (misc.tokenize(s[j], ","))[4];
						net.addElement(linkIdInn);
					}
				}
*/

				if (type.equals("gw") || type.equals("net") )
				{
					net.addElement(linkId);
					if (type.equals("gw"))
					{
						String linkIdInn = (misc.tokenize(s[j], ","))[6];
						net.addElement(linkIdInn);
					}

				} else
				{
					sw.addElement(linkId);
				}


			}
		}

		String[] param = new String[4];
		StringBuffer b = new StringBuffer();

		// legg til id for net (router) linker
		b.append("net=");
		for (int i = 0; i < net.size(); i++)
		{
			String s = (String)net.elementAt(i);
			b.append(s + ",");
		}
		if (net.size() > 0)
		{
			b.setLength(b.length()-1);
		} else
		{
			b.append("0");
		}
		param[0] = b.toString();

		// legg til id for sw linker
		b = new StringBuffer();
		b.append("sw=");
		for (int i = 0; i < sw.size(); i++)
		{
			String s = (String)sw.elementAt(i);
			b.append(s + ",");
		}
		if (sw.size() > 0)
		{
			b.setLength(b.length()-1);
		} else
		{
			b.append("0");
		}
		param[1] = b.toString();

		// tid
		long[] lastInterval = com.getLastInterval();

		if (lastInterval[1] >= 0) {
			param[2] = "time=" + lastInterval[0] + ",now";
		} else {
			param[2] = "time=" + lastInterval[0] + "," + lastInterval[1];
		}

		if (com.getTidAvg()) {
			param[3] = "type=avg";
		} else {
			param[3] = "type=max";
		}

		Vector[] lastData = fetch_old(param, lastURL);

com.d("Last hentet", 1);
		Vector CPULast = lastData[4];
		Vector BakplanLast = lastData[5];
		Vector linkLast = lastData[0];
		Vector elinkLast = lastData[3];
		Vector lanLast = lastData[1];
		Vector netLast = lastData[2];
		Vector swLast = lastData[6];
com.d("Vectorer OK", 1);
		// putt lan inn i netLast
		for (int i = 0; i < lanLast.size(); i++)
		{
			netLast.addElement(lanLast.elementAt(i));
		}
		// putt elink inn i netLast
		for (int i = 0; i < elinkLast.size(); i++)
		{
			netLast.addElement(elinkLast.elementAt(i));
		}
com.d("put OK", 1);
		return lastData;

	}

	public static String processText(String text, String[] data, Hashtable keywords)
	{
		// && = variabelnavn fra hashtable, ## = bytt ut med gitt verdi, !! = \n
		int i, tagLen="##".length();
		int cnt=1; // data starter på andre element (det første er en id)

		// Først bytter vi ut alle ##
		while ( (i=text.indexOf("##")) != -1) {
			if (cnt == data.length) {
				// Error, flere ## enn elementer i data
				break;
			}
			text = text.substring(0, i)+data[cnt++]+text.substring(i+tagLen, text.length());
		}

		// Så sjekker vi for && og evt. bytter ut fra keywords
		while ( (i=text.indexOf("&&")) != -1) {
			// Dersom teksten inneholder "!!", ")" eller " " etter && tar vi den som er nærmest,
			// i motsatt fall slutten på strengen
			int end = text.indexOf("!!", i);
			int end2 = text.indexOf(")", i);
			int end3 = text.indexOf(" ", i);
			end = min(end, end2, end3, text.length() );
			/*
			if (end == -1 && end2 == -1) {
				end = text.length();
			} else
			if (end == -1) {
				end = end2;
			} else
			if (end != -1 && end2 != -1) {
				if (end > end2) end = end2;
			}
			*/

			String word = text.substring(i+tagLen, end).toLowerCase();
			word = (String)keywords.get(word);
			if (word == null) word = "";
			//if (end == text.length()) end--;

			text = text.substring(0, i)+word+text.substring(end, text.length());
			//System.out.println("WORD: " + word);
		}

		// Så setter vi inn linjeskift
		while ( (i=text.indexOf("!!")) != -1) text = text.substring(0, i)+"\n"+text.substring(i+tagLen, text.length());

		return text;
	}

	private static int min(int i1, int i2, int i3, int i4)
	{
		if (i1 < 0) i1 = Integer.MAX_VALUE;
		if (i2 < 0) i2 = Integer.MAX_VALUE;
		if (i3 < 0) i3 = Integer.MAX_VALUE;
		if (i4 < 0) i4 = Integer.MAX_VALUE;

		i1 = Math.min(i1, i2);
		i1 = Math.min(i1, i3);
		i1 = Math.min(i1, i4);
		return i1;
	}




	public Vector[] fetch_old(String[] req, String param, String serverURL)
	{
		Vector[] ret = new Vector[req.length];
		int teller = 0;
		Vector v = new Vector();
		Vector v2 = new Vector();

		try
		{
			StringBuffer b = new StringBuffer();

			// lag URL
			//b.append("http://bigbud.itea.ntnu.no/vlanPlot/vPServer/vPServer");
			b.append(serverURL);
			b.append("?section=nettel&");
			if (param.length() > 0)
			{
				b.append(param + "&");
			}
			b.append("request=");
			for (int i = 0; i < req.length; i++)
			{
				b.append(req[i]);
				if ((i+1) < req.length)
				{
					b.append("^");
				}
			}
			//b.append("&");
			//b.append("send=Send\n");

			com.d("URL: " + b.toString(), 2);

			//URL url = new URL("http://home.dataparty.no/kristian/itea/nettelServer/nettelServer");
			URL url = new URL(b.toString() );
			URLConnection connection = url.openConnection();
			connection.connect();

			//connection.setRequestProperty("Referer", "http://www.itea.ntnu.no/");
/*
			connection.setDoOutput(true);
			PrintWriter out = new PrintWriter(connection.getOutputStream());

			out.print("section=nettel&");

			if (param.length() > 0)
			{
				out.print(param + "&");
			}

			out.print("request=");
			for (int i = 0; i < req.length; i++)
			{
				out.print(req[i]);
				if ((i+1) < req.length)
				{
					out.print("^");
				}
			}
			out.print("&");
			out.print("send=Send\n");

			out.close();
*/
			BufferedReader in = new BufferedReader(new InputStreamReader(connection.getInputStream()));
			String line;
			while ((line = in.readLine()) != null)
			{
				v.addElement(misc.tokenize(line, "^"));
			}

			for (int i = 1; i < v.size(); i++)
			{
				String[] s = (String[])v.elementAt(i);
				if (s[0].length() >= 4)
				{
					if (s[0].substring(0, 4).equals("list"))
					{
						ret[teller] = v2;
						v2 = new Vector();
						teller++;
					} else
					{
						v2.addElement(s);
					}
				} else
				{
					v2.addElement(s);
				}
			}
			ret[teller] = v2;

		}
		catch (Exception e)
		{
			com.d("Error: " + e.getMessage(), 0);
		}
		return ret;
	}

	public Vector[] fetch_old(String[] param, String serverURL)
	{
		Vector retV = new Vector();
		int teller = 0;
		Vector v = new Vector();
		Vector v2 = new Vector();

		try
		{
			StringBuffer b = new StringBuffer();

			// lag URL
			b.append(serverURL + "?");

			for (int i = 0; i < param.length; i++)
			{
				b.append(param[i]);

			}
			//b.append("send=Send\n");

			com.d("URL: " + b.toString(), 2);

			URL url = new URL(b.toString() );
			URLConnection connection = url.openConnection();
			connection.connect();

			BufferedReader in = new BufferedReader(new InputStreamReader(connection.getInputStream()));
			String line;
			while ((line = in.readLine()) != null)
			{
				v.addElement(misc.tokenize(line, ","));
			}

			for (int i = 1; i < v.size(); i++)
			{
				String[] s = (String[])v.elementAt(i);
				if (s[0].length() >= 4)
				{
					if (s[0].substring(0, 4).equals("list"))
					{
						retV.addElement(v2);
						v2 = new Vector();
						teller++;
					} else
					{
						v2.addElement(s);
					}
				} else
				{
					v2.addElement(s);
				}
			}
			retV.addElement(v2);

		}
		catch (Exception e)
		{
			com.d("Error: " + e.getMessage(), 0);
		}

		Vector[] ret = new Vector[retV.size()];
		for (int i = 0; i < retV.size(); i++)
		{
			ret[i] = (Vector)retV.elementAt(i);
		}

		return ret;
	}


	public int getNettelIndex(int n)
	{
		for (int i = 0; i < listRouters.size(); i++)
		{
			String[] s = (String[])listRouters.elementAt(i);
			int index = Integer.parseInt(s[0]);

			if (index == n)
			{
				return i;
			}
		}
		return -1;
	}

	public int getIndex(Vector v, int n)
	{
		for (int i = 0; i < v.size(); i++)
		{
			String[] s = (String[])v.elementAt(i);
			int index = Integer.parseInt(s[0]);

			if (index == n)
			{
				return i;
			}
		}
		return -1;
	}

	public int getXYIndex(int[][] xy, int n)
	{
		for (int i = 0; i < xy[0].length; i++)
		{
			if (xy[0][i] == n)
			{
				return i;
			}
		}
		return -1;
	}

	public int getId(Vector v, int n)
	{
		for (int i = 0; i < v.size(); i++)
		{
			if (n == ((Nettel)v.elementAt(i)).getBoksid() )
			{
				return i;
			}
		}
		return -1;
	}


	public int lookupIndex(Vector v, int n)
	{
		String[] s = (String[])v.elementAt(n);

		return Integer.parseInt(s[0]);
	}



	public boolean getAuth(String user, String pw)
	{
		/*
		if ( user.equals("admin") && pw.equals("admin") )
		{
			return true;
		} else
		{
			return false;
		}
		*/
		return user.equals("admin") ? true : false;
	}


	public Vector getListRouters() { return listRouters; }
	public Vector getListRouterLinks() { return listRouterLinks; }
	public Vector getListNetRouters() { return listNetRouters; }
	public Vector getListNetLinks() { return listNetLinks; }
	public Vector getRouterGroups() { return listRouterGroups; }

	public Vector getCPULast() { return listCPULast; }
	public Vector getLinkLast() { return listLinkLast; }
	public Vector getNetLast() { return listNetLast; }

	public int[][] getNettelXY() { return nettelXY; }
	//public int[][] getNettelXYGrp() { return nettelXYGrp; }
}




















