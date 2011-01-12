/*
 * ConfigParser
 * 
 * $LastChangedRevision$
 *
 * $LastChangedDate$
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
 */

package no.ntnu.nav.ConfigParser;

import java.io.BufferedReader;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.util.HashMap;
import java.util.Map;
import java.util.StringTokenizer;

/**
 * Class for parsing a config file in &lt;key&gt; = &lt;value&gt;
 * format. The value can be retrieved by calling get() with the
 * corresponding key.
 *
 * @version $LastChangedRevision$ $LastChangedDate$
 * @author Kristian Eide &lt;kreide@online.no&gt;
 */

public class ConfigParser
{
    private HashMap map = new HashMap();
	private Map objectMap = new HashMap();
	private String conffile;

    /**
     * Construct a new ConfigParser.
     *
     * @param confFile Full path to the file to be parsed.
     */
    public ConfigParser(String confFile) throws IOException
    {
        addDefaults();
		this.conffile = confFile;
        BufferedReader in = new BufferedReader(new InputStreamReader(new FileInputStream(confFile), "UTF-8"));

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

	public void setObject(String key, Object o) {
		objectMap.put(key, o);
	}

	public Object getObject(String key) {
		return objectMap.get(key);
	}

    private void setOption(String key, String value)
    {
        map.put(key, value);
    }

    /**
     * Get the value for a key.
     *
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

	public String toString()
	{
		return "ConfigParser("+conffile+")";
	}
}
