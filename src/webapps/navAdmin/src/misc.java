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

	/************************************************************
	* getIndex functions										*
	************************************************************/
	public static int getIndex(Vector v, int n)
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

	public static int getIndex(String[][] s, int n)
	{
		if (s == null)
		{
			return -1;
		}
		for (int i = 0; i < s[0].length; i++)
		{
			if (s[0][i] != null)
			{
				int index = Integer.parseInt(s[0][i]);

				if (index == n)
				{
					return i;
				}
			}
		}
		return -1;
	}

	public static int getIndex(String[] s, int n)
	{
		for (int i = 0; i < s.length; i++)
		{
			int index = Integer.parseInt( (tokenize(s[i], ","))[0] );

			if (index == n)
			{
				return i;
			}
		}
		return -1;
	}

	public static int getIndex(String[] s, String n)
	{
		for (int i = 0; i < s.length; i++)
		{
			if (s[i].equals(n) )
			{
				return i;
			}
		}
		return -1;
	}

	public static int[] getIndex2D(Vector v, int n, boolean y)
	{
		Vector ints = new Vector();
		for (int i = 0; i < v.size(); i++)
		{
			String[] s = (String[])v.elementAt(i);
			for (int j = 0; j < s.length; j++)
			{
				int index = Integer.parseInt( ((String[])misc.tokenize(s[j], ","))[0] );
				if (index == n)
				{
					if (y)
					{
						ints.addElement(new Integer(i));
					} else
					{
						ints.addElement(new Integer(j));
					}
				}
			}
		}

		if (ints.size() <= 0)
		{
			return new int[0];
		}

		int[] ret = new int[ints.size()];
		for (int i = 0; i < ints.size(); i++)
		{
			ret[i] = ((Integer)ints.elementAt(i)).intValue();
		}
		return ret;
	}

	/************************************************************
	* findValue functions										*
	************************************************************/
	public static String findValue(Vector v, int n, String val1, int ind1, String val2, int ind2)
	{
		for (int i = 0; i < v.size(); i++)
		{
			String[] s = (String[])v.elementAt(i);

			if (s[ind1].equals(val1) && s[ind2].equals(val2) )
			{
				return s[n];
			}
		}
		return null;
	}

	public static String[] findValues(Vector v, int n, String val1, int ind1)
	{
		Vector retV = new Vector();

		for (int i = 0; i < v.size(); i++)
		{
			String[] s = (String[])v.elementAt(i);

			if (s[ind1].equals(val1) )
			{
				retV.addElement(s[n]);
			}
		}
		if (retV.size() == 0)
		{
			return null;
		}

		String[] ret = new String[retV.size()];
		for (int i = 0; i < retV.size(); i++)
		{
			ret[i] = (String)retV.elementAt(i);
		}
		return ret;
	}
	public static String[] findValues(Vector v, int n, String val1, int ind1, String val2, int ind2)
	{
		Vector retV = new Vector();

		for (int i = 0; i < v.size(); i++)
		{
			String[] s = (String[])v.elementAt(i);

			if (s[ind1].equals(val1) && s[ind2].equals(val2) )
			{
				retV.addElement(s[n]);
			}
		}
		if (retV.size() == 0)
		{
			return null;
		}

		String[] ret = new String[retV.size()];
		for (int i = 0; i < retV.size(); i++)
		{
			ret[i] = (String)retV.elementAt(i);
		}
		return ret;
	}


	/************************************************************
	* Other functions											*
	************************************************************/

	public static void quickSort(String[] s)
	{
		// quicksort the array
		int incr = s.length / 2;

		while (incr >= 1)
		{
			for (int i = incr; i < s.length; i++)
			{
				String tmp = s[i];
				int j = i;

				//while (j >= incr && tmp.angle() < ((vect)v.elementAt(j - incr)).angle() )
				while (j >= incr && tmp.compareTo(s[j - incr]) < 0 )
				{
					//v.setElementAt(v.elementAt(j - incr), j);
					s[j] = s[j - incr];
					j -= incr;
				}
				//v.setElementAt(tmp, j);
				s[j] = tmp;
			}
			incr /= 2;
		}

		//return s;
	}

	public static void quickSort(Object[][] array)
	{
		Comparator comparator = new Comparator()
		{
			public int compare(Object one, Object two)
			{
				String intOne = (String)((Object[])one)[0];
				String intTwo = (String)((Object[])two)[0];
				return intOne.compareTo(intTwo);
			}
			public boolean equals(Object object) { return false; }
		};
		Arrays.sort(array,comparator);
	}


	public static String hex(String s)
	{
		s = s.replace(' ', '+');
		return s;
	}

	public static String dehex(String s)
	{
		s = s.replace('+', ' ');
		return s;
	}

	public static String getRandomPw()
	{
		Random rand = new Random();
		StringBuffer buf = new StringBuffer();

		for (int j = 0; j < 6; j++)
		{
			// java 1 syntax
			int min = 0;
			int max = 61;

			int i = rand.nextInt();
			if (i < 0)
			{
				i *= -1;
			}
			i = (i%(max - min + 1) + min);



			// java 2 syntax
			//int i = rand.nextInt(62);

			if (i <= 9)
			{
				i += 48;
			} else
			if (i <= 35)
			{
				i -= 10;
				i += 65;
			} else
			if (i <= 61)
			{
				i -= 36;
				i += 97;
			}

			buf.append("" + (char)i);
		}

		return buf.toString();

	}

	public static String encSql(String s)
	{
		StringBuffer b = new StringBuffer();

		for (int i = 0; i < s.length(); i++)
		{
			if (s.charAt(i) == 0)
			{
				b.append("\\0");
			} else
			if (s.charAt(i) == 34)
			{
				b.append("\\\"");
			} else
			if (s.charAt(i) == 39)
			{
				b.append("\\'");
			} else
			if (s.charAt(i) == 92)
			{
				b.append("\\\\");
			} else
			if (s.charAt(i) == 'µ')
			{
				b.append("&aelig;");
			} else
			if (s.charAt(i) == '°')
			{
				b.append("&oslash;");
			} else
			if (s.charAt(i) == 'Õ')
			{
				b.append("&aring;");
			} else
			if (s.charAt(i) == 'ã')
			{
				b.append("&AElig;");
			} else
			if (s.charAt(i) == 'Ï')
			{
				b.append("&Oslash;");
			} else
			if (s.charAt(i) == '+')
			{
				b.append("&Aring;");
			} else
			{
				b.append(s.charAt(i) );
			}
		}

		return b.toString();
	}

	public static String decSql(String s)
	{
		if (s == null)
		{
			return null;
		} else
		if (s.length() < 2)
		{
			return s;
		}
		StringBuffer b = new StringBuffer();

		for (int i = 0; i < s.length()-1; i++)
		{
			if (s.substring(i, i+2).equals("\\0") )
			{
				b.append( (char)0 );
				i++;
			} else
			if (s.substring(i, i+2).equals("\\\"") )
			{
				b.append( (char)34 );
				i++;
			} else
			if (s.substring(i, i+2).equals("\\'") )
			{
				b.append( (char)39 );
				i++;
			} else
			if (s.substring(i, i+2).equals("\\\\") )
			{
				b.append( (char)92 );
				i++;
			} else
			if (i+7 < s.length() )
			{
				if (s.substring(i, i+7).equals("&aelig;") )
				{
					b.append("µ");
					i += 6;
				} else
				if (s.substring(i, i+7).equals("&oslash;") )
				{
					b.append("°");
					i += 6;
				} else
				if (s.substring(i, i+7).equals("&aring;") )
				{
					b.append("Õ");
					i += 6;
				} else
				if (s.substring(i, i+7).equals("&AElig;") )
				{
					b.append("ã");
					i += 6;
				} else
				if (s.substring(i, i+7).equals("&Oslash;") )
				{
					b.append("Ï");
					i += 6;
				} else
				if (s.substring(i, i+7).equals("&Aring;") )
				{
					b.append("+");
					i += 6;
				} else
				{
					b.append(s.charAt(i) );
				}
			} else
			{
				b.append(s.charAt(i) );
			}
		}
		b.append(s.charAt(s.length()-1) );

		return b.toString();
	}



}
