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

import java.io.*;
import java.util.*;

/**
 * Class for parsing a config file in &lt;key&gt; = &lt;value&gt;
 * format. The value can be retrieved by calling get() with the
 * corresponding key.
 *
 * @version $LastChangedRevision$ $LastChangedDate$
 * @author Kristian Eide
 */

public class ConfigParser
{
    HashMap map = new HashMap();

    /**
     * Construct a new ConfigParser.
     *
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
}
