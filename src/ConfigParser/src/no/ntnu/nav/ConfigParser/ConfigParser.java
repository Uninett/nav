/*
 * NTNU ITEA "nav" prosjekt
 *
 * Configfil-parser
 *
 * Skrvet av: Kristian Eide <kreide@online.no>
 *
 */

package no.ntnu.nav.ConfigParser;

import java.io.*;
import java.util.*;

/**
 * Class for parsing a config file in <key> = <value> format. The value can be
 * retrieved by calling get() with the corresponding key.
 */
public class ConfigParser
{
    HashMap map = new HashMap();

        /**
         * Construct a new ConfigParser.
         * @param confFile Full path to the file to be parsed.
         */
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

       /**
        * Get the value for a key.
        * @param key The key
        * @return the value for the given key, or null if no such key exists.
        */
	public String get(String key)
	{
		return (String)map.get(key);
	}

	private void addDefaults()
	{
		map.put("SQLServer", "localhost");
	}
}

