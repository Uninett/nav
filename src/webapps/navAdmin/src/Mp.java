/*
 * Mp.java
 *
 */

import java.io.*;
import java.util.*;


public class Mp
{
	public String modul;
	public String port;
	String mp;

	public Mp(String mp)
	{
		this.mp = mp;
		if (mp != null) {
			StringTokenizer st = new StringTokenizer(mp, ":");
			if (st.countTokens() == 2) {
				modul = st.nextToken();
				port = st.nextToken();
			}
		}
	}

	public String toString()
	{
		return mp;
	}
}
