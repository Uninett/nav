/*
 * NTNU ITEA "nav" prosjekt
 *
 * Configfil-parser
 *
 * Skrvet av: Kristian Eide <kreide@online.no>
 *
 */

import java.io.*;
import java.util.*;

class PasswdParser
{
	HashMap map = new HashMap();

	public PasswdParser(String passwdFile) throws IOException
	{
		addDefaults();
		BufferedReader in = new BufferedReader(new FileReader(passwdFile));

		while (in.ready()) {
			String line = in.readLine().trim();
			if (line.length() == 0) continue;

			switch (line.charAt(0)) {
				case ';':
				case '#':
				break;

				default:
				StringTokenizer st = new StringTokenizer(line, ":", true);
				if (st.countTokens() == 0) break;

				ArrayList l = new ArrayList();
				int i=0;
				while (st.hasMoreTokens()) {
					String t = st.nextToken();
					if (t.equals(":")) t = "";
					else if (st.hasMoreTokens()) st.nextToken();

					l.add(t);
				}
				String[] s = new String[l.size()];
				for (int j=0; j < s.length; j++) s[j] = (String)l.get(j);

				map.put(s[0], s);
			}
		}
	}

	public String[] get(String key)
	{
		return (String[])map.get(key);
	}

	public String getUserClass(String user)
	{
		String[] s = (String[])map.get(user);
		if (s == null || s.length < 5) return null;

		return s[4];
	}

	private void addDefaults()
	{
		//map.put("SQLServer", "localhost");
	}
}

