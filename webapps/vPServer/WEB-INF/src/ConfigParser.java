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

class ConfigParser
{
	HashMap map = new HashMap();

	public ConfigParser(String confFile) throws IOException
	{
		addDefaults();
		BufferedReader in = new BufferedReader(new FileReader(confFile));

		while (in.ready()) {
			String line = in.readLine().trim();
			if (line.length() == 0) continue;

			switch (line.charAt(0)) {
				case ';':
				case '#':
				break;

				default:
				StringTokenizer st = new StringTokenizer(line, "=");
				if (st.countTokens() < 2) break;
				map.put(st.nextToken().trim(), st.nextToken().trim());
			}
		}
	}

	private void setOption(String key, String value)
	{
		map.put(key, value);
	}

	public String get(String key)
	{
		return (String)map.get(key);
	}

	private void addDefaults()
	{
		map.put("SQLServer", "localhost");
	}
}

