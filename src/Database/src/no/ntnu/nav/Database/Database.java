/*
 * Database
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
 * <p> Wrapper around the JDBC API to simplify working with the
 * database. This class contains only static methods any may thus be
 * used without needing a reference to it. It is also
 * thread-safe. However, it only supports connecting to one database
 * at a time.  </p>
 *
 * @version $LastChangedRevision$ $LastChangedDate$
 * @author Kristian Eide &lt;kreide@online.no&gt;
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
	 * <p> Open a connection to the database. Note that simultanious
	 * connections to different databases are not supported; if a
	 * connection is already open when this method is called a
	 * connection will be opened to the same database which is already
	 * connected.  </p>
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
	 * <p> When returnOnReconnectFail is true and the connection to the
	 * database is lost, only a single reconnect is tried. If it fails
	 * control is returned to the calling method with an error.  </p>
	 *
	 * If returnOnReconnectFail is false (default) a reconnect will be
	 * tried every few seconds until the connection is restored.  </p>
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
	 * <p> Return the number of database connections. Note that this may
	 * not reflect the number of actual connections to the database, as
	 * they may be shared.  </p>
	 *
	 * @return the number of database connections
	 */
	public static synchronized int getConnectionCount() { return connectionCount; }

	/**
	 * <p> Close the connection to the database.  </p>
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
	 * <p> This class keeps a buffer of Statment objects (currently 40),
	 * and when the buffer is full the first Statment (and its
	 * ResultSet) object is closed. Use this method to specify that the
	 * returned ResultSet for all subsequent query requests should never
	 * be closed.  </p>
	 *
	 * @param def specifies if the ResultSet returned for subsequent querys should never be closed.
	 */
	public static void setDefaultKeepOpen(boolean def)
	{
		defaultKeepOpen = def;
	}

	/**
	 * <p> Execute the given query.  </p>
	 *
	 * @param statement The SQL query statement to exectute
	 * @return the result of the query
	 */
	public static ResultSet query(String statement) throws SQLException
	{
		return query(statement, defaultKeepOpen);
	}

	/**
	 * <p> Execute the given query.  </p>
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
	 * <p> Begin a transaction. The database will not be changed until
	 * either commit() or rollback() is called.  </p>
	 */
	public static synchronized void beginTransaction() {
		/*
		try {
			connection.setAutoCommit(false);
		} catch (SQLException e) {
			System.err.println("setAutoCommit error: " + e.getMessage());
		}
		*/
	}

	/**
	 * <p> If a transaction is in progress, commit it, then go back to
	 * autocommit mode. Use beginTransaction() to start a new
	 * transaction.  </p>
	 */
	public static synchronized void commit() {
		/*
		try {
			connection.commit();
			connection.setAutoCommit(true);
		} catch (SQLException e) {
			System.err.println("Commit error: ".concat(e.getMessage()));
		}
		*/
	}

	/**
	 * <p> If a transaction is in progress, roll back any changes, then
	 * go back to autocommit mode. Use beginTransaction() to start a new
	 * transaction.  </p>
	 */
	public static synchronized void rollback() {
		/*
		try {
			connection.rollback();
			connection.setAutoCommit(true);
		} catch (SQLException e) {
			System.err.println("Rollback error: ".concat(e.getMessage()));
		}
		*/
	}

	/**
	 * <p> Insert a row in the database and return the sequence number
	 * used for the row.  </p>
	 *
	 * <p> Currently this only works for the PostgreSQL database.  This
	 * method assumes that the first two elements of the fieldValues
	 * argument are the name of the id-column which is to be assigned
	 * the sequence number and a dummy value respectably.  </p>
	 *
	 * <p> If the given seqName is null, it is assumed to be
	 * "tablename_idfieldname_seq".  </p>
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
	 * <p> Insert a row in the specified table.  </p>
	 *
	 * <p> The fieldValues argument must contain an even number of
	 * elements, and each pair of consecutive elements must specify the
	 * name of the column and the value to be inserted in said column
	 * respectably.  </p>
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
		boolean first = true;
		for (int i = 0; i < fieldValues.length; i += 2) {
			if (fieldValues[i+1] != null) {
				if (!first) {
					query += ",";
				} else {
					first = false;
				}
				query += addSlashesStrict(fieldValues[i]);
			}
		}

		query += ") VALUES (";
		first = true;
		for (int i = 1; i < fieldValues.length; i += 2) {
			if (fieldValues[i] != null) {
				if (!first) {
					query += ",";
				} else {
					first = false;
				}

				boolean fnutt = true;
				if (fieldValues[i].equals("NOW()") ||
						fieldValues[i].equals("null") ||
						(fieldValues[i].startsWith("(") && !fieldValues[i].equals("(null)"))) {
					fnutt = false;
				}

				if (fnutt) {
					query += "'" + addSlashesStrict(fieldValues[i]) + "'";
				} else {
					query += fieldValues[i];
				}
			}
		}
		query += ")";
		return update(query);
	}

	/**
	 * <p> Update rows in the specified table.  </p>
	 *
	 * <p> The fieldValues argument must contain an even number of
	 * elements, and each pair of consecutive elements must specify the
	 * name of the column and the new value to be set in said column
	 * respectably.  </p>
	 *
	 * <p> The keyFieldValues specifies which rows to update; it must
	 * contain an even number of elements, and each pair of consecutive
	 * elements must specify the name of the column and the value said
	 * column must have for the row to be included in the update
	 * respectable.  </p>
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
		boolean noUpdate = true;
		boolean first = true;
		for (int i = 0; i < fieldValues.length; i += 2) {
			if (fieldValues[i+1] != null) {
				if (!first) {
					query += ",";
				} else {
					first = false;
				}

				noUpdate = false;
				boolean fnutt = true;
				if (fieldValues[i+1].equals("NOW()") ||
						fieldValues[i+1].equals("null") ||
						(fieldValues[i+1].startsWith("(") && !fieldValues[i+1].equals("(null)"))) {
					fnutt = false;
				}

				if (fnutt) {
					query += fieldValues[i] + "=" + "'" + addSlashesStrict(fieldValues[i+1]) + "'";
				} else {
					query += fieldValues[i] + "=" + fieldValues[i+1];
				}
			}
		}
		if (noUpdate) return 0;

		query += " WHERE ";
		for (int i = 0; i < keyFieldValues.length; i += 2) {
			if (i != 0) query += " AND ";

			query += keyFieldValues[i] + "='" + addSlashesStrict(keyFieldValues[i+1]) + "'";
		}
		return update(query);
	}

	/**
	 * <p> Execute the given statement, and return the number of rows
	 * updated.  </p>
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
	 * <p> Return all columns from the current row in rs in a HashMap
	 * </p>
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
	 * <p> Make the given string "safe" (e.g. do not allow ( at the begining).
	 * \) </p>
	 *
	 * @param s The string to make safe
	 * @return a safe version of the string 
	 */
	public static String addSlashes(String s) {
		if (s == null) return null;
		if (s.startsWith("(")) return "\\" + s;
		return s;
	}

	/**
	 * <p> Escape any special characters in the given string (e.g. ' and
	 * \) </p>
	 *
	 * @param s The string to escape
	 * @return the string with special characters escaped
	 */
  private static String addSlashesStrict(String s) {
		if (s == null) return null;
		s = insertBefore(s, "\\", "\\");
		s = insertBefore(s, "'", "\\");
		return s;
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

}
