/*
 * DbCnf.java
 *
 */

import java.io.*;
import java.util.*;

class DbCnf
{
	Com com;
	Sql db;

	public DbCnf(Com InCom)
	{
		com = InCom;
		db = com.getDb();
	}

	public String getOne(String s)
	{
		return (get(s))[0];
	}
	public String[] get(String s)
	{
		String[][] s2 = getTree(s, false);

		if (s2 != null)
		{
			return s2[0];
		} else
		{
			return null;
		}
	}
	public String[][] getTree(String s, boolean b)
	{
		String[] t = misc.tokenizen(s, ".");
		String[] id = new String[1];
		id[0] = "0";

		for (int i = 0; i < t.length; i++)
		{
			id = db.exec("select id from vpConfig where parent='" + id[0] + "' and value='" + t[i] + "' order by id;");

			if (id[0] == null)
			{
				return null;
			}
		}

		//com.out("id: " + id[0] + "\n");
		/*
		Vector list = new Vector();

		for (int i = 0; i <= sublevels; i++)
		{
			String[] val = db.exec("select value from vpConfig where parent='" + id[0] + "' order by id;");

			id = db.exec("select id from vpConfig where parent='" + id[0] + "' order by id;");

			if (id[0] == null)
			{
				return null;
			}



		}
		*/

		String[][] ret;

		if (b)
		{
			// nå henter vi ut første verdi i neste undernivå og returnerer det også
			// nå henter vi ut hele undertreet



			ret = new String[1][];

		} else
		{
			// kun alle verdiene på dette nivået
			ret = new String[1][];

			ret[0] = db.exec("select value from vpConfig where parent='" + id[0] + "' order by id;");

			if (ret[0][0] == null)
			{
				return null;
			} else
			{
				return ret;
			}

		}

		return ret;
	}

	public void set(String s, String value)
	{
		String[] valueA = new String[1];
		valueA[0] = value;
		set(s, valueA);
	}
	public void set(String s, String[] value)
	{
		String[] t = misc.tokenizen(s, ".");
		String lastParent;
		String[] id = new String[1];
		id[0] = "0";

		for (int i = 0; i < t.length; i++)
		{
			lastParent = id[0];

			//com.outl("select id from vpConfig where parent='" + id[0] + "' and value='" + t[i] + "' order by id;");
			id = db.exec("select id from vpConfig where parent='" + id[0] + "' and value='" + t[i] + "' order by id;");

			if (id[0] == null)
			{
				String[] ins = new String[3];

				ins[0] = "null";
				ins[1] = lastParent;
				ins[2] = t[i];
				db.insert("vpConfig", ins, 0);

				id = db.exec("select id from vpConfig where parent='" + lastParent + "' and value='" + t[i] + "' order by id;");
			}
			//com.outl("ID is now: " + id[0]);
		}

		for (int i = 0; i < value.length; i++)
		{
			// insert ny record
			if (value[i] != null)
			{
				String[] ins = new String[3];

				ins[0] = "null";
				ins[1] = id[0];
				ins[2] = value[i];

				db.insert("vpConfig", ins, 0);
			}
		}

	}

	public void remove(String s)
	{
		String[] t = misc.tokenizen(s, ".");
		String[] id = new String[1];
		id[0] = "0";

		for (int i = 0; i < t.length; i++)
		{
			//com.outl("select id from vpConfig where parent='" + id[0] + "' and value='" + t[i] + "' order by id;");
			id = db.exec("select id from vpConfig where parent='" + id[0] + "' and value='" + t[i] + "' order by id;");

			if (id[0] == null)
			{
				return;
			}
		}

		String[] parent = db.exec("select id from vpConfig where parent='" + id[0] + "' order by id;");

		if (parent[0] != null)
		{
			for (int i = 0; i < parent.length; i++)
			{
				db.exec("delete from vpConfig where parent='" + parent[i] + "';");
			}
		}

		db.exec("delete from vpConfig where parent='" + id[0] + "';");
		db.exec("delete from vpConfig where id='" + id[0] + "';");

	}
	public void removeId(String id)
	{
		String[] parent = db.exec("select id from vpConfig where parent='" + id + "' order by id;");

		if (parent[0] != null)
		{
			for (int i = 0; i < parent.length; i++)
			{
				db.exec("delete from vpConfig where parent='" + parent[i] + "';");
			}
		}

		db.exec("delete from vpConfig where parent='" + id + "';");
		db.exec("delete from vpConfig where id='" + id + "';");

	}








}

























