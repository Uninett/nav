/* NTNU ITEA Nettnu prosjekt
 *
 * Skrvet av: Kristian Eide
 *
 */

import java.util.*;


class misc
{
	/************************************************************
	* Static misc-functions										*
	*															*
	************************************************************/


	/************************************************************
	* Tokenize functions										*
	************************************************************/
	public static String[] tokenize(String h, String c)
	{
		return tokenize(h, c, false, true);
	}

	public static String[] tokenizen(String h, String c)
	{
		return tokenize(h, c, false, false);
	}

	public static String[] tokenizel(String h, String c)
	{
		return tokenize(h, c, true, true);
	}

	public static String[] tokenize(String h, String c, boolean single, boolean trim)
	{
		if (h.length() <= 0)
		{
			// return dummy token
			String[] s = new String[1];
			s[0] = "";
			return s;
		}
		StringTokenizer st = new StringTokenizer(h, c, false);
		String[] s;

		if (single && st.countTokens() > 1)
		{
			s = new String[2];
			StringBuffer b = new StringBuffer();
			int tokens = st.countTokens();

			if (trim)
			{
				b.append(st.nextToken().trim() );
			} else
			{
				b.append(st.nextToken() );
			}
			for (int i = 1; i < tokens-1; i++)
			{
				if (trim)
				{
					b.append(c + st.nextToken().trim() );
				} else
				{
					b.append(c + st.nextToken() );
				}
			}
			s[0] = b.toString();
			s[1] = st.nextToken();

		} else
		{
			s = new String[st.countTokens()];

			int i = 0;
			while (st.hasMoreTokens())
			{
				if (trim)
				{
					s[i] = st.nextToken().trim();
				} else
				{
					s[i] = st.nextToken();
				}
				i++;
			}
		}
		return s;

	}





}
