/*
 * sql.java
 *
 */

//import com.codestudio.util.*;
import java.sql.*;
import java.util.*;

public class Sql
{
/*
	String server = "localhost";
	String login = "vPServer";
	String pw = "h4Ua7D";
	String db = "manage";
*/
	String server;
	String db;
	String login;
	String pw;

	//public Sql(Com InCom, String InServer, String InDb, String InLogin, String InPw)
	public Sql(String InServer, String InDb, String InLogin, String InPw)
	{
		/*
		//com = InCom;
		server = InServer;
		db = InDb;
		login = InLogin;
		pw = InPw;

		try
		{
			// The newInstance() call is a work around for some
			// broken Java implementations

			Class.forName("org.gjt.mm.mysql.Driver").newInstance();

		}
		catch (Exception E)
		{
			System.err.println("Unable to load driver.");
			E.printStackTrace();
		}
		*/
/*
		try
		{
			c = DriverManager.getConnection("jdbc:mysql://129.241.150.60/oving?user=kristian&password=kcyb");

			if (c == null)
			{
				sql_error = true;
			}

			// Do something with the Connection

			 s = c.createStatement();

			//s.executeQuery("create table dill (user varchar(8) DEFAULT '' NOT NULL);");
			//s.execute("insert into dill values ('kristian');");



		}
		catch (SQLException E)
		{
			System.out.println("SQLException: " + E.getMessage());
			System.out.println("SQLState:     " + E.getSQLState());
			System.out.println("VendorError:  " + E.getErrorCode());
		}
*/
	}

	public void sql_init()
	{
		try
		{
			// PoolMan
			//SQLManager manager = SQLManager.getInstance();
			//c = manager.requestConnection();

			// Normal
			//c = DriverManager.getConnection("jdbc:mysql://129.241.150.60/oving?user=kristian&password=kcyb");
			//c = DriverManager.getConnection("jdbc:mysql://158.38.48.44/oving?user=kristian&password=kcyb");

			//String server = com.getConf().get("SQLServer");
			//String login = com.getConf().get("SQLLogin");
			//String pw = com.getConf().get("SQLPw");
			//String db = com.getConf().get("SQLDb");


			c = DriverManager.getConnection("jdbc:mysql://" + server + "/" + db + "?user=" + login + "&password=" + pw);

			if (c == null)
			{
				sql_error = true;
			}

			// Do something with the Connection

			s = c.createStatement();

			//s.executeQuery("create table dill (user varchar(8) DEFAULT '' NOT NULL);");
			//s.execute("insert into dill values ('kristian');");



		}
		catch (SQLException E)
		{
			System.out.println("SQLException: " + E.getMessage());
			System.out.println("SQLState:     " + E.getSQLState());
			System.out.println("VendorError:  " + E.getErrorCode());
		}
		// PoolMan
		//catch (PoolPropsException e)
		//{

		//}

	}

	public void sql_close()
	{
		try
		{
			s.close();
			c.close();


		    //manager.returnConnection(c);

		}
		catch (SQLException E)
		{
			System.out.println("SQLException: " + E.getMessage());
			System.out.println("SQLState:     " + E.getSQLState());
			System.out.println("VendorError:  " + E.getErrorCode());

		}
	}
/*
	public String[] exec(String statement)
	{
		int i = 2;
		String[] result;

		try
		{
			rs = s.executeQuery(statement);
			if (statement.substring(0, 6).equals("select"))
			{
				rs.last();
				i = rs.getRow();
				rs.first();
			}
		}
		catch  (SQLException E)
		{
			com.out("SQLException: " + E.getMessage() + "<br>\n");
			com.out("SQLState:     " + E.getSQLState() + "<br>\n");
			com.out("VendorError:  " + E.getErrorCode() + "<br>\n");
			com.out("Statement:  " + statement + "<br>\n");
			com.out("Loops(1):  " + i + "<br>\n");

		}

		result = new String[i];

		try
		{
			if (statement.substring(0, 6).equals("select"))
			{

				for (int j = 1; j <= i; j++)
				{
					result[j-1] = rs.getString(1);
					rs.next();
				}
			}
			// Clean up after ourselves
			rs.close();
		}
		catch  (SQLException E)
		{
			com.out("SQLException: " + E.getMessage() + "<br>\n");
			com.out("SQLState:     " + E.getSQLState() + "<br>\n");
			com.out("VendorError:  " + E.getErrorCode() + "<br>\n");
			com.out("Statement:  " + statement + "<br>\n");
			com.out("Loops(2):  " + i + "<br>\n");
		}

		return result;
	}
*/

	public String[] exec(String statement)
	{
		return exec(statement, false);
	}

	public String[] exec(String statement, boolean ant)
	{
		return (exece(statement, 0, ant))[0];
	}

	public String[][] exece(String statement)
	{
		return exece(statement, 0, false);
	}



/*
	public String[] exec(String statement, boolean ant)
	{
		String[] result = null;
		Vector v = new Vector();
		try
		{
			rs = s.executeQuery(statement);
		}
		catch  (SQLException E)
		{
			com.out("SQLException: " + E.getMessage() + "<br>\n");
			com.out("SQLState:     " + E.getSQLState() + "<br>\n");
			com.out("VendorError:  " + E.getErrorCode() + "<br>\n");
			com.out("Statement:  " + statement + "<br>\n");
			com.out("Loops(1):  " + "<br>\n");
		}

		try
		{
			if (statement.substring(0, 6).equals("select"))
			{
				while (rs.next())
				{
					v.addElement(rs.getString(1));
				}

				if (ant)
				{
					String[] size = new String[1];
					size[0] = "" + v.size();
					return size;
				}

				result = new String[v.size()];
				for (int j = 0; j < v.size(); j++)
				{
					result[j] = (String)v.elementAt(j);
				}
			}
			// Clean up after ourselves
			rs.close();
			//manager.closeResources(s, rs);
		}
		catch  (SQLException E)
		{
			com.out("SQLException: " + E.getMessage() + "<br>\n");
			com.out("SQLState:     " + E.getSQLState() + "<br>\n");
			com.out("VendorError:  " + E.getErrorCode() + "<br>\n");
			com.out("Statement:  " + statement + "<br>\n");
			com.out("Loops(2):  " + "<br>\n");
		}

		if (result != null)
		{
			if (result.length == 0)
			{
				result = new String[1];
				//result[0] = "";
			}
		} else
		{
			result = new String[1];
		}
		return result;
	}
*/

	public String[][] exece(String statement, int row, boolean ant)
	{
		String[][] result = null;
		Vector v;
		try
		{
			//rs = s.executeQuery(statement);
			rs = Database.query(statement);
		}
		catch  (SQLException E)
		{
			System.out.println("SQL: " + statement);
			System.out.println("SQLException: " + E.getMessage());
			System.out.println("SQLState:     " + E.getSQLState());
			System.out.println("VendorError:  " + E.getErrorCode());

			/*
			com.out("SQLException: " + E.getMessage() + "<br>\n");
			com.out("SQLState:     " + E.getSQLState() + "<br>\n");
			com.out("VendorError:  " + E.getErrorCode() + "<br>\n");
			com.out("Statement:  " + statement + "<br>\n");
			com.out("Loops(1):  " + "<br>\n");
			*/
		}

		try
		{
			if (statement.substring(0, 6).toLowerCase().equals("select"))
			{
				 metaData = rs.getMetaData();

			//com.out("columns: " + metaData.getColumnCount() + "\n");
			//com.out("sql: " + statement + "\n");

				int columnCount = metaData.getColumnCount();
				result = new String[columnCount][];

				if (!rs.next())
				{
					columnCount = 0;
				}

				for (int i = 1; i <= columnCount; i++)
				{
					v = new Vector();
			//com.out("new vector\n");
					do
					{
			//com.out("add element\n");
						v.addElement(rs.getString(i));
					} while (rs.next());
					rs.first();

					if (ant && row == i)
					{
						String[][] size = new String[1][1];
						size[0][0] = "" + v.size();
						return size;
					}

					result[i-1] = new String[v.size()];
					for (int j = 0; j < v.size(); j++)
					{
						result[i-1][j] = (String)v.elementAt(j);
					}
				}
			}
			// Clean up after ourselves
			rs.close();
			//manager.closeResources(s, rs);
		}
		catch  (SQLException E)
		{
			/*
			com.out("SQLException: " + E.getMessage() + "<br>\n");
			com.out("SQLState:     " + E.getSQLState() + "<br>\n");
			com.out("VendorError:  " + E.getErrorCode() + "<br>\n");
			com.out("Statement:  " + statement + "<br>\n");
			com.out("Loops(2):  " + "<br>\n");
			*/
		}

		if (result != null)
		{
			if (result[0] == null)
			{
				for (int i = 0; i < result.length; i++)
				{
					result[i] = new String[1];
				}
			}
		} else
		{
			result = new String[1][1];
		}

		return result;
	}

	public HashMap exech(int key, String statement)
	{
		int[] keys = { key };
		return exech(keys, statement);
	}

	public HashMap exech(int[] keys, String statement)
	{
		// Only selected allowed
		if (!statement.substring(0, 6).toLowerCase().equals("select")) return null;
		HashMap h = new HashMap();

		try
		{
			//rs = s.executeQuery(statement);
			rs = Database.query(statement);
		}
		catch  (SQLException E)
		{
			/*
			com.out("SQLException: " + E.getMessage() + "<br>\n");
			com.out("SQLState:     " + E.getSQLState() + "<br>\n");
			com.out("VendorError:  " + E.getErrorCode() + "<br>\n");
			com.out("Statement:  " + statement + "<br>\n");
			com.out("Loops(1):  " + "<br>\n");
			*/
		}

		try
		{
			int columnCount = rs.getMetaData().getColumnCount();
			//System.out.println("cnt: " + columnCount);
			for (int i=0; i < keys.length; i++) if (keys[i] >= columnCount) return null;

			while (rs.next())
			{
				//System.out.println("rs.next: " + rs.getString(1) );
				String[] s = new String[columnCount];
				for (int i=0; i < columnCount; i++) s[i] = rs.getString(i+1);
				String k = "";
				for (int i=0; i < keys.length; i++) k+=s[keys[i]];
				//System.out.println("Insert, Key: " + k + " Data: " + s);
				h.put(k, s);
			}

			// Clean up after ourselves
			rs.close();
		}
		catch  (SQLException E)
		{
			System.out.println("SQLException: " + E.getMessage());
			System.out.println("SQLState:     " + E.getSQLState());
			System.out.println("VendorError:  " + E.getErrorCode());
			/*
			com.out("SQLException: " + E.getMessage() + "<br>\n");
			com.out("SQLState:     " + E.getSQLState() + "<br>\n");
			com.out("VendorError:  " + E.getErrorCode() + "<br>\n");
			com.out("Statement:  " + statement + "<br>\n");
			com.out("Loops(2):  " + "<br>\n");
			*/
		}

		return h;
	}


	public void insert(String table, String[] data, int num)
	{
		StringBuffer st = new StringBuffer();

		if (num == 0)
		{
			//num = data.length-1;
			num = data.length;
		}

		// først bygge opp statementet
		//info = com.getDb().exec("insert into " + table + " values ('" + user[0] + "','" + user[1] + "');");
		//update users set pw='3' where login='dill3';

		st.append("insert into " + table + " values (");

		for (int i = 0; i < num; i++)
		{
			if (data[i].equals("NOW()"))
			{
				st.append("" + data[i] + "");
			} else
			{
				st.append("'" + data[i] + "'");
			}

			// java1 syntax
			if (i != num-1)
			{
				st.append(",");
			}

		}
		// kun java2 :(
		//st.deleteCharAt(st.length()-1);
		st.append(");");

		try
		{
			//rs = s.executeQuery(st.toString());
			rs = Database.query(st.toString());
		}
		catch  (SQLException E)
		{
			System.out.println("SQLException: " + E.getMessage());
			System.out.println("SQLState:     " + E.getSQLState());
			System.out.println("VendorError:  " + E.getErrorCode());
			//throw new DBError("insertError");
		}

		try
		{
			// Clean up after ourselves
			rs.close();
		}
		catch  (SQLException E)
		{
			System.out.println("SQLException: " + E.getMessage());
			System.out.println("SQLState:     " + E.getSQLState());
			System.out.println("VendorError:  " + E.getErrorCode());
		}
	}

	public void replace(String table, String[] data, int num)
	{
		StringBuffer st = new StringBuffer();

		if (num == 0)
		{
			num = data.length-1;
		}

		// først bygge opp statementet
		//info = com.getDb().exec("insert into " + table + " values ('" + user[0] + "','" + user[1] + "');");
		//update users set pw='3' where login='dill3';

		// først slette gammel row
		try
		{
			rs = s.executeQuery("delete from " + table + " where login='" + data[0] + "';");
		}
		catch  (SQLException E)
		{
			System.out.println("SQLException: " + E.getMessage());
			System.out.println("SQLState:     " + E.getSQLState());
			System.out.println("VendorError:  " + E.getErrorCode());
			//throw new DBError("insertError");
		}

		// så bygge opp statementet
		st.append("insert into " + table + " values (");

		for (int i = 0; i < num; i++)
		{
			st.append("'" + data[i] + "'");

			// java1 syntax
			if (i != num-1)
			{
				st.append(",");
			}
		}
		// ikke java1
		//st.deleteCharAt(st.length()-1);
		st.append(");");

		try
		{
			//rs = s.executeQuery(st.toString());
			rs = Database.query(st.toString());
		}
		catch  (SQLException E)
		{
			System.out.println("SQLException: " + E.getMessage());
			System.out.println("SQLState:     " + E.getSQLState());
			System.out.println("VendorError:  " + E.getErrorCode());
			//throw new DBError("insertError");
		}

		try
		{
			// Clean up after ourselves
			rs.close();
		}
		catch  (SQLException E)
		{
			System.out.println("SQLException: " + E.getMessage());
			System.out.println("SQLState:     " + E.getSQLState());
			System.out.println("VendorError:  " + E.getErrorCode());
		}
	}

	public boolean getSqlStatus()
	{
		return sql_error;
	}


	// class vars
	//SQLManager manager;
	Connection c;
	Statement s;
	ResultSet rs;
	ResultSetMetaData metaData;
	boolean sql_error = false;

	//Com com;
}

class DBError extends Throwable
{
	public DBError(String InMsg)
	{
		msg = InMsg;
	}

	public DBError(String InMsg, String[] InS)
	{
		msg = InMsg;
		s = InS;
	}

	public String getError()
	{
		return msg;
	}

	public String[] getData()
	{
		return s;
	}

	String msg;
	String[] s;
}