/*
 * NTNU ITEA "nav" prosjekt
 *
 * Database interface class
 *
 * Skrvet av: Kristian Eide <kreide@online.no>
 *
 */

package no.ntnu.nav.Database;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.ResultSet;
import java.sql.ResultSetMetaData;
import java.sql.SQLException;
import java.sql.Statement;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.HashMap;
import java.util.Date;

public class Database
{
	private static final int ST_BUFFER = 40;
    private static final String dbDriverOracle = "oracle.jdbc.driver.OracleDriver";
    private static final String dbDriverPostgre = "org.postgresql.Driver";
    private static final String dbDriverMysql = "org.gjt.mm.mysql.Driver";

    private static final String dbName = "postgresql";
    //private static final String dbName = "mysql";

    private static final String dbDriver = dbDriverPostgre;

    private static Connection connection;

    private static Statement[] stQuery = new Statement[ST_BUFFER];
    private static boolean[] stKeepOpen = new boolean[ST_BUFFER];
    private static boolean defaultKeepOpen = false;

    private static Statement stUpdate;
    private static int queryCount;
    private static int queryPos;
    private static boolean queryQFull = false;

    private static int connectionCount = 0;

    public static synchronized boolean openConnection(String serverName, String serverPort, String dbName, String user, String pw) {
		boolean ret = false;
		if (serverName == null) { ret=true; System.err.println("Database.openConnection(): Error, serverName is null"); }
		if (serverPort == null) { ret=true; System.err.println("Database.openConnection(): Error, serverPort is null"); }
		if (dbName == null) { ret=true; System.err.println("Database.openConnection(): Error, dbName is null"); }
		if (user == null) { ret=true; System.err.println("Database.openConnection(): Error, user is null"); }
		if (pw == null) { ret=true; System.err.println("Database.openConnection(): Error, pw is null"); }
		if (ret) return false;

		for (int i=0; i < stKeepOpen.length; i++) stKeepOpen[i]=false;
		connectionCount++;
		if (connectionCount > 1) {
			// En connection er allerede åpen
			return true;
		}

		try {
			Class.forName(dbDriver);

			//connection = DriverManager.getConnection(dbName, login, pw);
			//c = DriverManager.getConnection("jdbc:mysql://" + server + "/" + db + "?user=" + login + "&password=" + pw);
			//String dbNavn = "jdbc:oracle:thin:@loiosh.stud.idb.hist.no:1521:orcl";

			connection = DriverManager.getConnection("jdbc:postgresql://" + serverName + ":"+serverPort+"/" + dbName, user, pw);
			//connection = DriverManager.getConnection("jdbc:"+dbName+"://" + serverName + "/" + dbName, user, pw);
			//connection = DriverManager.getConnection("jdbc:mysql://"+serverName+"/"+dbName+"?user="+user+"&password="+pw);

			connection.setAutoCommit(false);
			stUpdate = connection.createStatement();
			return true;
		} catch (ClassNotFoundException e) {
			System.err.println("openConnection ClassNotFoundExecption error: ".concat(e.getMessage()));
		} catch (SQLException e) {
			System.err.println("openConnection error: ".concat(e.getMessage()));
		}
		return false;
    }

    public static synchronized int getConnectionCount() { return connectionCount; }

    public static synchronized void closeConnection() {
	if (connectionCount == 0) return; // Ingen connection å lukke
		connectionCount--;
		if (connectionCount > 0) {
			// En connection er fortsatt åpen
			return;
		}

		try {
			//System.out.println("########## -CLOSE CONNECTION ON DATABASE- ##########");
			connection.close();
		} catch (SQLException e) {
			System.err.println("closeConnection error: ".concat(e.getMessage()));
		}
    }

    /**
     * This class keeps a buffer of Statment objects (currently 40), and when the
     * buffer is full the first Statment (and its ResultSet) object is closed. Use this method to
     * specify that the returned ResultSet for all subsequent query requests should
     * never be closed.
     *
     * @param def specifies if the ResultSet returned for subsequent querys should never be closed.
     */
    public static void setDefaultKeepOpen(boolean def)
    {
		defaultKeepOpen = def;
	}

    public static ResultSet query(String statement) throws SQLException
    {
		return query(statement, defaultKeepOpen);
	}
    public static synchronized ResultSet query(String statement, boolean keepOpen) throws SQLException
    {
		if (!findNotOpen()) throw new SQLException("There are no open statements left!");

		if (queryPos==stQuery.length) {
			if (!queryQFull) queryQFull = true;
			queryPos = 0;
		}
		if (queryQFull) stQuery[queryPos].close();

		Statement st = connection.createStatement();
		stQuery[queryPos] = st;
		stKeepOpen[queryPos] = keepOpen;
		queryCount++;
		queryPos++;
		ResultSet resultset = st.executeQuery(statement);
		return resultset;
    }
	private static boolean findNotOpen()
	{
		// Find a 'free' statement
		int startIndex = queryPos;
		do {
			if (queryPos==stQuery.length) queryPos = 0;
			if (!stKeepOpen[queryPos]) return true;
			queryPos++;
		} while (queryPos != startIndex);
		return false;
	}

    public static synchronized void commit() {
		try {
			//System.out.println("########## -COMMIT ON DATABASE- ##########");
			connection.commit();
		} catch (SQLException e) {
			System.err.println("Commit error: ".concat(e.getMessage()));
		}
    }

    public static synchronized void rollback() {
		try {
			//System.out.println("########## -ROLLBACK ON DATABASE- ##########");
			connection.rollback();
		} catch (SQLException e) {
			System.err.println("Rollback error: ".concat(e.getMessage()));
		}
    }

    public static int insert(String table, String[] feltVerdi) throws SQLException
    {
		if ((feltVerdi.length & 0x1) == 1)
			return -1;
		String query = String.valueOf(new StringBuffer("INSERT INTO ").append(table).append(" ("));
		for (int i = 0; i < feltVerdi.length; i += 2) {
			if (i != 0) query += ",";

			query += feltVerdi[i];
		}
		query += ") VALUES (";
		for (int i = 1; i < feltVerdi.length; i += 2) {
			if (i != 1) query += ",";

			String fnutt = "'";
			if (feltVerdi[i].equals("NOW()")) fnutt = "";
			else if (feltVerdi[i].equals("null")) fnutt = "";

			query += fnutt + feltVerdi[i] + fnutt;
			//if (feltVerdi[i - 1].toLowerCase().startsWith("dato") && feltVerdi[i].toLowerCase().equals("sysdate"))
			//query = query.concat(feltVerdi[i]);
			//else
			//query = query.concat(String.valueOf(new StringBuffer("'").append(feltVerdi[i]).append("'")));
		}
		query = query.concat(")");
		/*
		try {
			//System.out.println("Insert query: ".concat(query));
			stUpdate.close();
			stUpdate = connection.createStatement();
			stUpdate.executeUpdate(query);
			return true;
		} catch (SQLException e) {
			System.err.println("Insert query error: ".concat(e.getMessage()));
			return false;
		}
		*/
		return update(query);
    }

    public static int update(String table, String[] feltVerdi, String[] keyNavnVerdi) throws SQLException
    {
		if ((feltVerdi.length & 0x1) == 1 || (keyNavnVerdi.length & 0x1) == 1)
			return -1;
		String query = String.valueOf(new StringBuffer("UPDATE ").append(table).append(" SET "));
		for (int i = 0; i < feltVerdi.length; i += 2) {
			if (i != 0) query += ",";

			String fnutt = "'";
			if (feltVerdi[i+1].equals("NOW()")) fnutt = "";
			else if (feltVerdi[i+1].equals("null")) fnutt = "";

			query += feltVerdi[i] + "=" + fnutt + addSlashes(feltVerdi[i+1]) + fnutt;
		}
		query += " WHERE ";
		for (int i = 0; i < keyNavnVerdi.length; i += 2) {
			if (i != 0) query += " AND ";

			query += keyNavnVerdi[i] + "='" + addSlashes(keyNavnVerdi[i+1]) + "'";
			//query += String.valueOf(new StringBuffer().append().append().append());
		}
		/*
		try {
			//System.out.println("Update query: ".concat(query));
			stUpdate.close();
			stUpdate = connection.createStatement();
			stUpdate.executeUpdate(query);
			return true;
		} catch (SQLException e) {
			System.err.println("Update query error: ".concat(e.getMessage()));
			return false;
		}
		*/
		return update(query);
    }

    public static synchronized int update(String query) throws SQLException
    {
		/*
		try {
			//System.out.println("Update query: ".concat(query));
			stUpdate.close();
			stUpdate = connection.createStatement();
			stUpdate.executeUpdate(query);
			return true;
		} catch (SQLException e) {
			System.err.println("Update query error: ".concat(e.getMessage()));
			return false;
		}
		*/
		stUpdate.close();
		stUpdate = connection.createStatement();
		return stUpdate.executeUpdate(query);
	}

	/**
	 * Return all columns from the current row in rs in a HashMap
	 *
	 * @param rs ResultSet to fetch row from
	 * @param md Get column names from this object
	 * @return HashMap with all columns from the current row in rs
	 */
	public static HashMap getHashFromResultSet(ResultSet rs, ResultSetMetaData md) throws SQLException
	{
		HashMap hm = new HashMap();
		for (int i=md.getColumnCount(); i > 0; i--) {
			hm.put(md.getColumnName(i), rs.getString(i));
		}
		return hm;
	}


	/**
	 * Escape any special characters in the given string (e.g. ' and \)
	 *
	 * @param tekst The string to escape
	 * @return the string with special characters escaped
	 */
    public static String addSlashes(String tekst) {
		tekst = insertBefore(tekst, "\\", "\\");
		tekst = insertBefore(tekst, "'", "\\");
		return tekst;
    }

    private static String insertBefore(String tekst, String oldS, String newS) {
		if (tekst.indexOf(oldS) == -1)
			return tekst;
		StringBuffer b = new StringBuffer(tekst);
		int pos = -1 - newS.length();
		for (;;) {
			pos = b.toString().indexOf(oldS, pos + 1 + newS.length());
			if (pos == -1)
			break;
			b.insert(pos, newS);
		}
		return b.toString();
    }


	/*
    public static boolean isDouble(String s) {
		return isDoubleStrict(cleanString(s));
    }

    public static boolean isDoubleStrict(String s) {
		try {
			Double.parseDouble(s);
			boolean bool = true;
			return bool;
		} catch (NumberFormatException numberformatexception) {
			return false;
		}
    }

    public static boolean isInt(String s) {
		return isIntStrict(cleanString(s));
    }

    public static boolean isIntStrict(String s) {
		try {
			Integer.parseInt(s);
			boolean bool = true;
			return bool;
		} catch (NumberFormatException numberformatexception) {
			return false;
		}
    }

    protected static String cleanString(String s) {
		s = removeString(s, "*");
		return s;
    }

    protected static String removeString(String s, String rem) {
		StringBuffer b = new StringBuffer(s);
		for (int pos = b.toString().indexOf(rem); pos != -1; pos = b.toString().indexOf(rem))
			b = b.replace(pos, pos + rem.length(), "");
		return b.toString();
    }

    protected static String sqlMatch(String feltnavn, String søkeverdi) {
		if (søkeverdi.length() == 0)
			return "";
		return String.valueOf(new StringBuffer(" AND ").append(feltnavn).append(" like '").append(stjerneTilProsent(søkeverdi)).append("'"));
    }

    private static String stjerneTilProsent(String tekst) {
		return tekst.replace('*', '%');
    }

    protected static Date parseDate(String sqlDate) {
		if (sqlDate != null) {
			try {
			SimpleDateFormat sf = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
			Date date = sf.parse(sqlDate);
			return date;
			} catch (ParseException e) {
			System.err.println("parseDate Error: ".concat(e.getMessage()));
			}
		}
		return null;
    }

    protected static String formatDate(Date dato) {
		if (dato != null) {
			SimpleDateFormat sf = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
			return sf.format(dato);
		}
		return null;
    }
    */
}
