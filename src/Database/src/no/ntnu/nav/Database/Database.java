/*******************
*
* $Id: Database.java,v 1.4 2003/03/03 10:44:53 kristian Exp $
* This file is part of the NAV project.
* Database interface class
*
* Copyright (c) 2002 by NTNU, ITEA nettgruppen
* Authors: Kristian Eide <kreide@online.no>
*
*******************/

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
import java.net.SocketException;

import no.ntnu.nav.logger.Log;

/**
 * Wrapper around the JDBC API to simplify working with the
 * database. This class contains only static methods any may thus be
 * used without needing a reference to it. It is also
 * thread-safe. However, it only supports connecting to one database
 * at a time.
 */
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
	private static String connectionString;
	private static String connectionUser;
	private static String connectionPw;

	private static Statement[] stQuery = new Statement[ST_BUFFER];
	private static boolean[] stKeepOpen = new boolean[ST_BUFFER];
	private static boolean defaultKeepOpen = false;

	private static Statement stUpdate;
	private static int queryCount;
	private static int queryPos;
	private static boolean queryQFull = false;

	private static int reconnectWaitTime = 10000; // 10 seconds
	private static boolean returnOnReconnectFail = false;

	private static int connectionCount = 0;

	// Contains only static methods
	private Database() {
	}

	/**
	 * Open a connection to the database. Note that simultanious
	 * connections to different databases are not supported; if a
	 * connection is already open when this method is called a
	 * connection will be opened to the same database which is already
	 * connected.
	 *
	 * @param serverName Name of server to connect to
	 * @param serverPort Network port on server to connect to
	 * @param dbName Name of database to connect to
	 * @param user Username to use for login to server
	 * @param pw Password to use for login to server
	 * @return true if connection was opened successfully; false otherwise
	 */
	public static synchronized boolean openConnection(String serverName, String serverPort, String dbName, String user, String pw) {
		boolean ret = false;
		if (serverName == null) { ret=true; System.err.println("Database.openConnection(): Error, serverName is null"); }
		if (serverPort == null) { ret=true; System.err.println("Database.openConnection(): Error, serverPort is null"); }
		if (dbName == null) { ret=true; System.err.println("Database.openConnection(): Error, dbName is null"); }
		if (user == null) { ret=true; System.err.println("Database.openConnection(): Error, user is null"); }
		if (pw == null) { ret=true; System.err.println("Database.openConnection(): Error, pw is null"); }
		if (ret) return false;

		if (connectionCount > 0) {
			// En connection er allerede åpen
			connectionCount++;
			return true;
		}

		try {
			Class.forName(dbDriver);
	
			connectionString = "jdbc:postgresql://" + serverName + ":"+serverPort+"/" + dbName;
			connectionUser = user;
			connectionPw = pw;
			connect();

			connectionCount++;
			return true;
		} catch (ClassNotFoundException e) {
			System.err.println("openConnection ClassNotFoundExecption error: ".concat(e.getMessage()));
		} catch (SQLException e) {
			System.err.println("openConnection error: ".concat(e.getMessage()));
		}
		return false;
	}

	/**
	 * When returnOnReconnectFail is true and the connection to the
	 * database is lost, only a single reconnect is tried. If it fails
	 * control is returned to the calling method with an error.
	 *
	 * If returnOnReconnectFail is false (default) a reconnect will be
	 * tried every few seconds until the connection is restored.
	 *
	 * @param b New value for returnOnReconnectFail
	 */
	public static void setReturnOnReconnectFail(boolean b) {
		returnOnReconnectFail = b;
	}

	private static void connect() throws SQLException {
		connection = DriverManager.getConnection(connectionString, connectionUser, connectionPw);

		//connection = DriverManager.getConnection(dbName, login, pw);
		//c = DriverManager.getConnection("jdbc:mysql://" + server + "/" + db + "?user=" + login + "&password=" + pw);
		//String dbNavn = "jdbc:oracle:thin:@loiosh.stud.idb.hist.no:1521:orcl";
		
		//connection = DriverManager.getConnection("jdbc:"+dbName+"://" + serverName + "/" + dbName, user, pw);
		//connection = DriverManager.getConnection("jdbc:mysql://"+serverName+"/"+dbName+"?user="+user+"&password="+pw);

		connection.setAutoCommit(true);
		stUpdate = connection.createStatement();

		queryPos = 0;
		for (int i=0; i < stKeepOpen.length; i++) stKeepOpen[i]=false;
	}

	/**
	 * Return the number of database connections. Note that this may not
	 * reflect the number of actual connections to the database, as they
	 * may be shared.
	 *
	 * @return the number of database connections
	 */
	public static synchronized int getConnectionCount() { return connectionCount; }

	/**
	 * Close the connection to the database.
	 */
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

	/**
	 * Execute the given query.
	 *
	 * @param statement The SQL query statement to exectute
	 * @return the result of the query
	 */
	public static ResultSet query(String statement) throws SQLException
	{
		return query(statement, defaultKeepOpen);
	}

	/**
	 * Execute the given query.
	 *
	 * @param statement The SQL query statement to exectute
	 * @param keepOpen If true, never close the returned ResultSet object
	 * @return the result of the query
	 */
	public static synchronized ResultSet query(String statement, boolean keepOpen) throws SQLException
	{
		// Try to execute. If we get a SocketException, wait and try again
		boolean firstTry = true;
		while (true) {
			try {

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
				
				ResultSet rs = st.executeQuery(statement);
				return rs;
			} catch (SQLException sqle) {
				throw sqle;
			} catch (Exception e) {
				// First try to reconnect
				if (firstTry) {
					connect();
					continue;
				}

				// That didn't work; log error
				Log.e("DATABASE-QUERY", "Got Exception; database is probably down: " + e.getMessage());

				if (returnOnReconnectFail) {
					throw new SQLException("Got Exception; database is probably down: " + e.getMessage());
				}

				try {
					Thread.currentThread().wait(reconnectWaitTime);
				} catch (InterruptedException ie) {
				}

				connect();

			}
		}
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

	/**
	 * Begin a transaction. The database will not be changed until
	 * either commit() or rollback() is called.
	 */
	public static synchronized void beginTransaction() {
		try {
			connection.setAutoCommit(false);
		} catch (SQLException e) {
			System.err.println("setAutoCommit error: " + e.getMessage());
		}
	}

	/**
	 * If a transaction is in progress, commit it, then go back to
	 * autocommit mode. Use beginTransaction() to start a new
	 * transaction.
	 */
	public static synchronized void commit() {
		try {
			//System.out.println("########## -COMMIT ON DATABASE- ##########");
			connection.commit();
			connection.setAutoCommit(true);
		} catch (SQLException e) {
			System.err.println("Commit error: ".concat(e.getMessage()));
		}
	}

	/**
	 * If a transaction is in progress, roll back any changes, then go
	 * back to autocommit mode. Use beginTransaction() to start a new
	 * transaction.
	 */
	public static synchronized void rollback() {
		try {
			//System.out.println("########## -ROLLBACK ON DATABASE- ##########");
			connection.rollback();
			connection.setAutoCommit(true);
		} catch (SQLException e) {
			System.err.println("Rollback error: ".concat(e.getMessage()));
		}
	}

	/**
	 * Insert a row in the database and return the sequence number used
	 * for the row.
	 *
	 * Currently this only works for the PostgreSQL database.  This
	 * method assumes that the first two elements of the fieldValues
	 * argument are the name of the id-column which is to be assigned
	 * the sequence number and a dummy value respectably.
	 *
	 * If the given seqName is null, it is assumed to be "tablename_idfieldname_seq".
	 *
	 * @param table The name of the table in which the row is to be inserted
	 * @param fieldValues The names of columns and the values to be inserted
	 * @param seqName The name of the sequence from which to obtain the sequence number, or null
	 *
	 * @return the sequence number for the row
	 */
	public static String insert(String table, String[] fieldValues, String seqName) throws SQLException {
		if (seqName == null) seqName = table + "_" + fieldValues[0] + "_seq";

		ResultSet rs = Database.query("SELECT nextval('" + seqName + "') AS seqnum");
		if (!rs.next()) throw new SQLException("Failed to get a sequence number from " + seqName);

		String seqNum = rs.getString("seqnum");
		fieldValues[1] = seqNum;

		insert(table, fieldValues);
		return seqNum;
	}

	/**
	 * Insert a row in the specified table.
	 *
	 * The fieldValues argument must contain an even number of elements,
	 * and each pair of consecutive elements must specify the name of
	 * the column and the value to be inserted in said column
	 * respectably.
	 *
	 * @param table The name of the table in which the row is to be inserted
	 * @param fieldValues The names of columns and the values to be inserted
	 *
	 * @return the number of inserted rows, which is always 1 
	 */
	public static int insert(String table, String[] fieldValues) throws SQLException
	{

		if ((fieldValues.length & 0x1) == 1)
			return -1;

		String query = "INSERT INTO " + table + " (";
		for (int i = 0; i < fieldValues.length; i += 2) {
			if (i != 0) query += ",";

			query += fieldValues[i];
		}

		query += ") VALUES (";
		for (int i = 1; i < fieldValues.length; i += 2) {
			if (i != 1) query += ",";

			String fnutt = "'";
			if (fieldValues[i].equals("NOW()") ||
					fieldValues[i].equals("null")) {
				fnutt = "";
			}

			query += fnutt + fieldValues[i] + fnutt;
		}
		query += ")";
		return update(query);
	}

	/**
	 * Update rows in the specified table.
	 *
	 * The fieldValues argument must contain an even number of elements,
	 * and each pair of consecutive elements must specify the name of
	 * the column and the new value to be set in said column
	 * respectably.
	 *
	 * The keyFieldValues specifies which rows to update; it must
	 * contain an even number of elements, and each pair of consecutive
	 * elements must specify the name of the column and the value said
	 * column must have for the row to be included in the update
	 * respectable.
	 *
	 * @param table The name of the table in which the row is to be inserted
	 * @param fieldValues The names of columns and the values to be inserted
	 *
	 * @return the number of updated rows.
	 */
	public static int update(String table, String[] fieldValues, String[] keyFieldValues) throws SQLException
	{
		if ((fieldValues.length & 0x1) == 1 || (keyFieldValues.length & 0x1) == 1)
			return -1;

		String query = "UPDATE " + table + " SET ";
		for (int i = 0; i < fieldValues.length; i += 2) {
			if (i != 0) query += ",";

			String fnutt = "'";
			if (fieldValues[i+1].equals("NOW()")) fnutt = "";
			else if (fieldValues[i+1].equals("null")) fnutt = "";

			query += fieldValues[i] + "=" + fnutt + addSlashes(fieldValues[i+1]) + fnutt;
		}

		query += " WHERE ";
		for (int i = 0; i < keyFieldValues.length; i += 2) {
			if (i != 0) query += " AND ";

			query += keyFieldValues[i] + "='" + addSlashes(keyFieldValues[i+1]) + "'";
		}
		return update(query);
	}

	/**
	 * Execute the given statement, and return the number of rows updated.
	 *
	 * @param statement The statement to execute
	 * @return the number of rows updated
	 */
	public static synchronized int update(String statement) throws SQLException
	{
		stUpdate.close();
		stUpdate = connection.createStatement();
		try {
			return stUpdate.executeUpdate(statement);
		} catch (SQLException e) {
			System.err.println("SQLException for update statement: " + statement);
			throw e;
		}
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
