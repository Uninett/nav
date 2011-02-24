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

import java.io.File;
import java.io.IOException;
import java.net.SocketException;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.ResultSet;
import java.sql.ResultSetMetaData;
import java.sql.SQLException;
import java.sql.Statement;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.GregorianCalendar;
import java.util.HashMap;
import java.util.IdentityHashMap;
import java.util.Iterator;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;

import no.ntnu.nav.Path;
import no.ntnu.nav.ConfigParser.ConfigParser;
import no.ntnu.nav.logger.Log;

/**
 * <p> Wrapper around the JDBC API to simplify working with the
 * database. This class contains only static methods any may thus be
 * used without needing a reference to it. It is also fully
 * thread-safe and supports per-thread transactions. </p>
 *
 * @version $LastChangedRevision$ $LastChangedDate$
 * @author Kristian Eide &lt;kreide@online.no&gt;
 */

public class Database
{
	public static final long CONNECTION_IDLE_TIMEOUT = 60 * 60 * 1000; // 60 minutes

	public static final int POSTGRESQL_DRIVER = 0;
	public static final int MYSQL_DRIVER = 10;
	public static final int ORACLE_DRIVER = 20;

	public static final int DEFAULT_DRIVER = POSTGRESQL_DRIVER;
	
	public static final int DEFAULT_GLOBAL_STATEMENT_BUFFER = 32;
	public static final int DEFAULT_THREAD_STATEMENT_BUFFER = 2;
	public static final int DEFAULT_RECONNECT_WAIT_TIME = 10000;
	public static final int DEFAULT_MAX_CONNECTIONS = 6;
	public static final int DEFAULT_MAX_TRANS_CONNECTIONS = 4;

	private static final String dbDriverOracle = "oracle.jdbc.driver.OracleDriver";
	private static final String dbDriverPostgresql = "org.postgresql.Driver";
	private static final String dbDriverMysql = "org.gjt.mm.mysql.Driver";


	private static Map activeDB = Collections.synchronizedMap(new HashMap()); // Maps thread -> active connection identifier
	private static Map dbDescrs = Collections.synchronizedMap(new HashMap()); // Maps user-supplied connection identifier to DB descr

	private static Map statementMap = Collections.synchronizedMap(new IdentityHashMap()); // Used for freeing not autoclose statements

	private static SimpleDateFormat dateFormat = new SimpleDateFormat("MMM dd HH:mm:ss yyyy");

	private static class DBDescr {
		private int dbDriver;
		private String dbDriverString;
		public String serverName;
		public String serverPort;
		public String dbName;
		public String user;
		public String pw;
		private String conStr;

		private boolean returnOnReconnectFail = false;
		private int refCount;
		private LinkedList conQ;
		private LinkedList conQT;
		private Map activeTransactions = new HashMap();
		private int conCnt;
		private int conTCnt;

		private Map statementMap = Collections.synchronizedMap(new HashMap()); // Maps thread to a LinkedList of statements
		private LinkedList globStatementQ = new LinkedList();

		public DBDescr(int _dbDriver, String _serverName, String _serverPort, String _dbName, String _user, String _pw) {
			dbDriver = _dbDriver;
			serverName = _serverName;
			serverPort = _serverPort;
			dbName = _dbName;
			user = _user;
			pw = _pw;
			conQ = new LinkedList();
			conQT = new LinkedList();
			refCount = 0;
			storeConnectString();
		}

		public String getKey() {
			return conStr+":"+user+":"+pw;
		}

		public boolean verifyConnection() {
			try {
				Statement st = getStatement();
				ResultSet rs = st.executeQuery("SELECT 1");
				if (rs.next()) {
					// Connection OK
					return true;
				}
			} catch (Exception e) {
				String msg = e.getMessage();
				int idx;
				if (msg != null && (idx=msg.indexOf("Stack Trace")) >= 0) msg = msg.substring(0, idx-1);
				System.err.println("Connection verify failed: " + msg);
			}
			return false;
		}

		public int getConnectionCount() {
			return conCnt;
		}

		// Gets a connection for the current thread
		public ConnectionDescr getConnection() throws SQLException {
			synchronized (activeTransactions) {
				if (activeTransactions.containsKey(Thread.currentThread())) {
					ConnectionDescr transDescr = (ConnectionDescr)activeTransactions.get(Thread.currentThread());
					if (transDescr == null) throw new SQLException("Transaction aborted due to database reconnect");
					return transDescr;
				}
			}
			cleanConnectionQ();
			synchronized (conQ) {
				if (conQ.isEmpty()) {
					if (conCnt >= DEFAULT_MAX_CONNECTIONS) {
						waitForConnection(conQ);
					} else {
						if (!createConnection()) return null;
					}
				}
				return (ConnectionDescr)conQ.removeFirst();
			}
		}

		// Gets a transaction connection for the current thread
		public ConnectionDescr getTransConnection() throws SQLException {
			synchronized (activeTransactions) {
				if (activeTransactions.containsKey(Thread.currentThread())) {
					ConnectionDescr transDescr = (ConnectionDescr)activeTransactions.get(Thread.currentThread());
					if (transDescr == null) throw new SQLException("Transaction aborted due to database reconnect");
					return transDescr;
				}
			}
			cleanConnectionQT();
			synchronized (conQT) {
				if (conQT.isEmpty()) {
					if (conTCnt >= DEFAULT_MAX_TRANS_CONNECTIONS) {
						waitForConnection(conQT);
					} else {
						if (!createTransConnection()) return null;
					}
				}
				return (ConnectionDescr)conQT.removeFirst();
			}
		}

		public void waitForConnection(Collection waitQ) {
			// Wait for a free connection
			while (true) {
				try {
					//System.err.println("Waiting for connection...("+conQ.size()+")");
					waitQ.wait();
					//System.err.println("Got notify! ("+conQ.size()+")");
					if (!waitQ.isEmpty()) break;
				} catch (InterruptedException e) {
				}
				// There should now be a new connection available				
			}
		}

		/**
		 * <p>Free a given ConnectionDescr instance , by placing it back into 
		 * the connection queue, thus making it available for other threads to
		 * use.</p>
		 * 
		 * <p>If the given ConnectionDescr object happens to be a transaction
		 * connection for the current thread, this method does nothing.
		 * Transaction objects must be explicitly committed or rolled back 
		 * before they are freed.</p>
		 * 
		 * @param cd The ConnectionDescr object to free.
		 */
		public void freeConnection(ConnectionDescr cd) {
			synchronized (activeTransactions) {
				if (activeTransactions.get(Thread.currentThread()) == cd) {
					//System.out.println("["+Integer.toHexString(Thread.currentThread().hashCode())+"] "+"NOT freeing con");
					return;
				}
				//System.out.println("["+Integer.toHexString(Thread.currentThread().hashCode())+"] "+"FREEING con");
			}
			synchronized (conQ) {
				conQ.add(cd);
				conQ.notify();
			}
		}

		public void freeTransConnection(ConnectionDescr cd) {
			synchronized (conQT) {
				conQT.add(cd);
				conQT.notify();
			}
		}

		public Statement getStatement() throws SQLException {
			return getStatement(true);
		}

		public Statement getStatement(boolean autoclose) throws SQLException {
			ConnectionDescr cd = getConnection();
			Statement st = cd.getStatement(autoclose);
			freeConnection(cd);
			return st;
		}

		public Statement getUpdateStatement() throws SQLException {
			ConnectionDescr cd = getConnection();
			Statement st = cd.getUpdateStatement();
			/* XXX: The next line seems like a dubious scheme.  The connection 
			 * is freed and made available to other threads before the update 
			 * statement we've obtained is even used.  See further comments in 
			 * ConnectionDescr.getUpdateStatement(), called above. 
			 */
			freeConnection(cd);
			return st;
		}

		public boolean openConnection() {
			if (!connect()) return false;
			refCount++;
			return true;
		}

		private boolean connect() {
			synchronized (conQ) {
				if (conQ.isEmpty()) {
					if (!createConnection()) return false;
				}
			}
			return true;
		}

		public void closeConnection() {
			refCount--;
			if (refCount > 0) return; // Still open connections
			closeAllConnections();
		}

		public boolean reconnect() {
			synchronized (conQ) {
				//System.out.println("Closing all connections: " + conQ.size());
				closeAllConnections();
				//System.out.println("            connections: " + conQ.size());
				return connect();
			}
		}

		private void closeAllConnections() {
			synchronized (conQ) {
				closeAllConnections(conQ.iterator());
				statementMap.clear();
				globStatementQ.clear();
				conCnt = 0;
			}
			synchronized (conQT) {
				closeAllConnections(conQT.iterator());
				conTCnt = 0;
			}
			synchronized (activeTransactions) {
				List l = new ArrayList();
				for (Iterator it = activeTransactions.entrySet().iterator(); it.hasNext();) {
					Map.Entry me = (Map.Entry)it.next();
					try {
						((ConnectionDescr)me.getValue()).close();
					} catch (SQLException e) {
						String msg = e.getMessage();
						int idx;
						if (msg != null && (idx=msg.indexOf("Stack Trace")) >= 0) msg = msg.substring(0, idx-1);
						System.err.println("closeConnection error: " + msg);
					}
					l.add(me.getKey());
				}
				for (Iterator it = l.iterator(); it.hasNext();) {
					activeTransactions.put(it.next(), null);
				}
			}
		}

		private void closeAllConnections(Iterator conIt) {
			while (conIt.hasNext()) {
				try {
					((ConnectionDescr)conIt.next()).close();
				} catch (SQLException e) {
					String msg = e.getMessage();
					int idx;
					if (msg != null && (idx=msg.indexOf("Stack Trace")) >= 0) msg = msg.substring(0, idx-1);
					System.err.println("closeConnection error: " + msg);
				}
				conIt.remove();
			}
		}

		private void cleanConnectionQ() throws SQLException {
			synchronized (conQ) {
				conCnt -= cleanConnectionQ(conQ);
			}
		}

		private void cleanConnectionQT() throws SQLException {
			synchronized (conQT) {
				conTCnt -= cleanConnectionQ(conQT);				
			}			
		}

		private int cleanConnectionQ(LinkedList conQ) throws SQLException {
			int remCnt = 0;
			if (conQ.size() > 1) {
				Iterator it = conQ.iterator();
				while (it.hasNext()) {
					ConnectionDescr cd = (ConnectionDescr)it.next();
					if (System.currentTimeMillis() - cd.lastUsed > CONNECTION_IDLE_TIMEOUT) {
						cd.close();
						it.remove();
						remCnt++;
						if (conQ.size() == 1) break;
					}
				}
			}
			return remCnt;
		}

		private boolean createConnection() {
			ConnectionDescr cd = newConnection();
			if (cd != null) {
				synchronized (conQ) {
					conQ.add(cd);
					conCnt++;
					conQ.notify();
					return true;
				}
			}
			return false;
		}

		private boolean createTransConnection() {
			ConnectionDescr cd = newConnection();
			if (cd != null) {
				synchronized (conQT) {
					conQT.add(cd);
					conTCnt++;
					conQT.notify();
					return true;
				}
			}
			return false;
		}

		private ConnectionDescr newConnection() {
			try {
				Class.forName(dbDriverString);
				
				Connection con = DriverManager.getConnection(conStr, user, pw);
				ConnectionDescr cd = new ConnectionDescr(con);
				return cd;
				
			} catch (ClassNotFoundException e) {
				System.err.println("createConnection ClassNotFoundExecption error: " + e.getMessage());
			} catch (SQLException e) {
				System.err.println("createConnection error: " + e.getMessage());
			}
			return null;
		}
		
		public void setReturnOnReconnectFail(boolean b) {
			returnOnReconnectFail = b;
		}

		public boolean getReturnOnReconnectFail() {
			return returnOnReconnectFail;
		}

		public void beginTransaction() throws SQLException {
			//System.out.println("["+Integer.toHexString(Thread.currentThread().hashCode())+"] "+"Entering beginTransaction");
			//System.out.println("["+Integer.toHexString(Thread.currentThread().hashCode())+"] "+"* beginTransaction entered");
			ConnectionDescr cd = getTransactionCon(true);
			//System.out.println("["+Integer.toHexString(Thread.currentThread().hashCode())+"] "+"* getTransCont done..");
			cd.setAutoCommit(false);
		}

		public void commit() throws SQLException {
			//System.out.println("["+Integer.toHexString(Thread.currentThread().hashCode())+"] "+"Entering sync activeTrans");
			//System.out.println("["+Integer.toHexString(Thread.currentThread().hashCode())+"] "+"commit calling getTrans");
			ConnectionDescr cd = getTransactionCon(false);
			//System.out.println("["+Integer.toHexString(Thread.currentThread().hashCode())+"] "+"commit returned from getTrans");
			if (cd == null) return;
			cd.commit();
			cd.setAutoCommit(true);
			freeTransactionCon(cd);
		}

		public void rollback() throws SQLException {
			ConnectionDescr cd = getTransactionCon(false);
			if (cd == null) return;
			cd.rollback();
			cd.setAutoCommit(true);
			freeTransactionCon(cd);
		}

		private ConnectionDescr getTransactionCon(boolean create) throws SQLException {
			Thread t = Thread.currentThread();
			ConnectionDescr cd = null;
			//System.out.println("["+Integer.toHexString(Thread.currentThread().hashCode())+"] "+"getTransCon calling getCon");
			synchronized (activeTransactions) {
				cd = (ConnectionDescr)activeTransactions.get(t);
			}
			if (cd == null && create) {
				cd = getTransConnection();
				synchronized (activeTransactions) {
					activeTransactions.put(t, cd);
				}
			}
			//System.out.println("["+Integer.toHexString(Thread.currentThread().hashCode())+"] "+"getTransCon *done*");
			return cd;
		}

		private void freeTransactionCon(ConnectionDescr cd) {
			activeTransactions.remove(Thread.currentThread());
			freeTransConnection(cd);
		}
		
		private String getConnectString() {
			return conStr;
		}

		private void storeConnectString() {
			conStr = "jdbc:";

			switch (dbDriver) {
			case MYSQL_DRIVER:
				dbDriverString = dbDriverMysql;
				conStr += "mysql";
				break;

			case ORACLE_DRIVER:
				//"jdbc:oracle:thin:@loiosh.stud.idb.hist.no:1521:orcl";
				dbDriverString = dbDriverOracle;
				conStr += "oracle";
				break;

			case POSTGRESQL_DRIVER:
			default:
				dbDriverString = dbDriverPostgresql;
				conStr += "postgresql";
				break;
			}
			conStr += "://" + serverName;
			if (serverPort != null) conStr += ":"+serverPort;
			conStr += "/" + dbName;
		}


		private class ConnectionDescr {
			private Connection con;
			private long lastUsed;
			private Statement updateStatement;
			
			public ConnectionDescr(Connection _con) throws SQLException {
				con = _con;
				lastUsed = System.currentTimeMillis();
				newUpdateStatement();
				con.setAutoCommit(true);
			}

			public void close() throws SQLException {
				con.close();
			}

			public void setAutoCommit(boolean autoCommit) throws SQLException {
				con.setAutoCommit(autoCommit);
				lastUsed = System.currentTimeMillis();
			}

			public void commit() throws SQLException {
				con.commit();
				lastUsed = System.currentTimeMillis();
			}

			public void rollback() throws SQLException {
				con.rollback();
				lastUsed = System.currentTimeMillis();
			}

			private void newUpdateStatement() throws SQLException {
				/* XXX: The following if clause has been commented out because 
				 * it causes a race condition.  The updateStatement instance 
				 * may still be held by another thread, and so closing it 
				 * explicitly here may cause that thread to throw an 
				 * SQLException from using an already closed statement.  
				 * According to the Java Docs, a Statement object will be 
				 * closed when garbage collected, which seems to be a better 
				 * approach in this situation. 
				 */
//				if (updateStatement != null) {
//					updateStatement.close();
//				}
				updateStatement = con.createStatement();
				lastUsed = System.currentTimeMillis();
			}

			public Statement getStatement(boolean autoclose) throws SQLException {
				StatementQ stQ = getOrCreateStatementQ();
				synchronized (globStatementQ) {
					if (globStatementQ.size() > DEFAULT_GLOBAL_STATEMENT_BUFFER) {
						((Statement)globStatementQ.removeFirst()).close();
					}
				}
				return stQ.getStatement(autoclose);
			}

			public Statement getUpdateStatement() throws SQLException {
				newUpdateStatement();
				return updateStatement;
			}

			private StatementQ getOrCreateStatementQ() {
				Thread t = Thread.currentThread();
			    StatementQ q;
				if ((q=(StatementQ)statementMap.get(t)) == null) statementMap.put(t, q = new StatementQ());
				return q;
			}

			private class StatementQ {
				LinkedList statementQ; // FIFO list over statements
				int bufferSize;

				public StatementQ() {
					this(DEFAULT_THREAD_STATEMENT_BUFFER);
				}

				public StatementQ(int _bufferSize) {
					bufferSize = _bufferSize;
					statementQ = new LinkedList();
				}

				public Statement getStatement(boolean autoclose) throws SQLException {
					Statement st = con.createStatement(ResultSet.TYPE_SCROLL_INSENSITIVE, ResultSet.CONCUR_READ_ONLY);
					if (autoclose) {
						statementQ.add(st);
						if (statementQ.size() > bufferSize) {
							synchronized (globStatementQ) {
								globStatementQ.add(statementQ.removeFirst());
							}
						}
					}
					lastUsed = System.currentTimeMillis();
					return st;
				}
			}
		}		
	}


	// Changes the active DB that is to be used for subsequent DB calls
	public static void setActiveDB(String conId) {
		activeDB.put(Thread.currentThread(), conId);
	}

	private static Statement getStatement(String conId, boolean autoclose) throws SQLException {
		return getDBDescr(conId).getStatement(autoclose);
	}

	private static Statement getUpdateStatement(String conId) throws SQLException {
		return getDBDescr(conId).getUpdateStatement();
	}
		

	private static DBDescr getDBDescr(String conId) {
		conId = getConnectionId(conId);
		DBDescr db = (DBDescr)dbDescrs.get(conId);
		if (db == null) throw new RuntimeException("DBDescr not found, did you forget to call openConnection?");
		return db;
	}

	private static boolean removeDBDescr(String conId) {
		conId = getConnectionId(conId);
		return dbDescrs.remove(conId) != null;
	}


	private static String getConnectionId(String conId) {
		if (conId != null) return conId;
		if (activeDB.containsKey(Thread.currentThread())) return (String)activeDB.get(Thread.currentThread());
		return (String)activeDB.get(null);
	}
		


	// Contains only static methods
	private Database() {
	}

	/**
	 * <p>Return a set of connection parameters from db.conf, given a script
	 * and database name.
	 * </p>
	 * 
	 * <p>If the given script name isn't found in db.conf, the script name 
	 * &quot;default&quot; will be assumed.</p>
	 * 
	 * @param scriptName Script name, to find a matching db user name from db.conf
	 * @param database Database name. Not a real database name, but the name of a db_* parameter from db.conf.
	 * @return A String array with PostgreSQL connection parameters in the following order: server name, server port, database name, user name, password.  If there were errors reading the config file, a null value is returned.
	 */
	public static String[] getConnectionParameters(String scriptName, String database) {
		String dbConfigFile = (Path.sysconfdir + "/db.conf").replace('/', File.separatorChar);
		ConfigParser dbConfig;

		try {
			dbConfig = new ConfigParser(dbConfigFile);
		} catch (IOException e) {
			Log.e("DATABASE-PARAMETERS", "Could not read config file: " + dbConfigFile);
			return null;
		}
		String dbhost = dbConfig.get("dbhost");
		String dbport = dbConfig.get("dbport");
		String dbname = dbConfig.get("db_"+database);
		if (dbname == null) {
			Log.d("DATABASE-PARAMETERS", "Connection parameters for db_" + database + " not found, trying db_nav instead");
			dbname = dbConfig.get("db_nav");
		}
		String username = dbConfig.get("script_"+scriptName);
		if (username == null) {
			Log.d("DATABASE-PARAMETERS", "Connection parameters for scriptname " + scriptName + " not found, using default instead");
			username = dbConfig.get("script_default");
		}
		String password = dbConfig.get("userpw_"+username);

		String[] params = {dbhost, dbport, dbname, username, password};
		return params;
	}

	/**
	 * <p> Open a connection to the database, based on configuration 
	 * parameters from the db.conf configuration file.</p>
	 * 
	 * @see #openConnection(String, String, String, String, String)
	 * @see #getConnectionParameters(String, String)
	 *  
	 * @param scriptName Script name, to find a matching db user name from db.conf
	 * @param database Database name. Not a real database name, but the name of a db_* parameter from db.conf.
	 * @return true if connection was opened successfully; false otherwise
	 */
	public static boolean openConnection(String scriptName, String database) {
		String[] params = getConnectionParameters(scriptName, database);
		for (int i=0; i<params.length; i++) {
			if (params[i] == null) {
				Log.e("DATABASE-OPENCONNECTION", "Missing connection parameters, cannot connect to database");
				return false;
			}
		}
		return openConnection(params[0], params[1], params[2], params[3], params[4]);
	}
	
	public static boolean openConnection(String serverName, String serverPort, String dbName, String user, String pw) {
		return openConnection(null, DEFAULT_DRIVER, serverName, serverPort, dbName, user, pw);
	}

	/**
	 * <p> Open a connection to the database. Note that simultaneous
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
	public static boolean openConnection(String conId, int dbDriver, String serverName, String serverPort, String dbName, String user, String pw) {
		boolean ret = false;
		if (serverName == null) { ret=true; System.err.println("Database.openConnection(): Error, serverName is null"); }
		if (dbName == null) { ret=true; System.err.println("Database.openConnection(): Error, dbName is null"); }
		if (user == null) { ret=true; System.err.println("Database.openConnection(): Error, user is null"); }
		if (pw == null) { ret=true; System.err.println("Database.openConnection(): Error, pw is null"); }
		if (ret) return false;

		DBDescr db;
		synchronized (dbDescrs) {
			db = (DBDescr)dbDescrs.get(getConnectionId(conId));
			if (db == null) {
				db = new DBDescr(dbDriver, serverName, serverPort, dbName, user, pw);
				if (conId == null) {
					conId = db.getKey();
					DBDescr db2 = (DBDescr)dbDescrs.get(getConnectionId(conId));
					if (db2 != null) db = db2;
				}
			}
			dbDescrs.put(conId, db);
		}
		
		if (!db.openConnection()) {
			dbDescrs.remove(conId);
			return false;
		}
		
		activeDB.put(Thread.currentThread(), conId);
		if (!activeDB.containsKey(null)) activeDB.put(null, conId);
		return true;
	}

	/**
	 * <p> When returnOnReconnectFail is true and the connection to the
	 * database is lost, only a single reconnect is tried. If it fails
	 * control is returned to the calling method with an error.  </p>
	 *
	 * If returnOnReconnectFail is false (default) a reconnect will be
	 * tried every few seconds until the connection is restored.  </p>
	 *
	 * @param returnOnReconnectFail New value for returnOnReconnectFail
	 */
	public static void setReturnOnReconnectFail(String conId, boolean returnOnReconnectFail) {
		DBDescr db = getDBDescr(conId);
		db.setReturnOnReconnectFail(returnOnReconnectFail);
	}

	/**
	 * <p> Return the number of database connections. Note that this may
	 * not reflect the number of actual connections to the database, as
	 * they may be shared.  </p>
	 *
	 * @return the number of database connections
	 */
	public static int getConnectionCount() {
		synchronized (dbDescrs) {
			int cnt=0;
			for (Iterator it = dbDescrs.values().iterator(); it.hasNext();) {
				cnt += ((DBDescr)it.next()).getConnectionCount();
			}
			return cnt;
		}
	}

	public static void closeConnection() {
		closeConnection(null);
	}

	/**
	 * <p> Close the connection to the database.  </p>
	 */
	public static void closeConnection(String conId) {
		synchronized (dbDescrs) {
			DBDescr db = getDBDescr(conId);
			db.closeConnection();
			removeDBDescr(conId);
		}
	}

	public static Object getConnection() throws SQLException {
		DBDescr dbd = getDBDescr(null);
		return dbd.getConnection();
	}

	public static void freeConnection(Object o) {
		DBDescr dbd = getDBDescr(null);
		dbd.freeConnection((DBDescr.ConnectionDescr)o);
	}

	/**
	 * <p> Execute the given query.  </p>
	 *
	 * @param statement The SQL query statement to exectute
	 * @return the result of the query
	 */
	public static ResultSet query(String statement) throws SQLException
	{
		return query(statement, false);
	}


	/**
	 * <p> Free the given resultset.  </p>
	 *
	 * @param rs The resultset to free
	 */
	public static void free(ResultSet rs) throws SQLException
	{
		if (statementMap.containsKey(rs)) {
			Statement st = (Statement)statementMap.remove(rs);
			st.close();
		}
	}

	/**
	 * <p> Execute the given query.  </p>
	 *
	 * @param statement The SQL query statement to exectute
	 * @param keepOpen If true, the resultset must be closed with the free() method
	 * @return the result of the query
	 */
	public static ResultSet query(String statement, boolean keepOpen) throws SQLException
	{
		// Try to execute. If we get a SocketException, wait and try again
		while (true) {
			try {
				Statement st = getStatement(null, !keepOpen);
				ResultSet rs = st.executeQuery(statement);
				if (keepOpen) {
					statementMap.put(rs, st);
				}
				return rs;
			} catch (Exception e) {
				handleStatementException(e, statement, "DATABASE-QUERY");
			}
		}
	}

	/**
	 * <p> Begin a transaction. The database will not be changed until
	 * either commit() or rollback() is called.  </p>
	 */
	public static void beginTransaction() throws SQLException {
		try {
			getDBDescr(null).beginTransaction();
		} catch (SQLException e) {
			e.printStackTrace(System.err);
			throw e;
		}
	}

	/**
	 * <p> If a transaction is in progress, commit it, then go back to
	 * autocommit mode. Use beginTransaction() to start a new
	 * transaction.  </p>
	 */
	public static void commit() throws SQLException {
		//System.out.println("["+Integer.toHexString(Thread.currentThread().hashCode())+"] "+"Entering commit");
		try {
			getDBDescr(null).commit();
		} catch (SQLException e) {
			e.printStackTrace(System.err);
			throw e;
		}
	}

	/**
	 * <p> If a transaction is in progress, roll back any changes, then
	 * go back to autocommit mode. Use beginTransaction() to start a new
	 * transaction.  </p>
	 */
	public static void rollback() throws SQLException {
		try {
			getDBDescr(null).rollback();
		} catch (SQLException e) {
			e.printStackTrace(System.err);
			throw e;
		}
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

		Statement stUpdate = getUpdateStatement(null);
		ResultSet rs = stUpdate.executeQuery("SELECT nextval('" + seqName + "') AS seqnum");
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
	public static int update(String statement) throws SQLException
	{
		while (true) {
			try {
				Statement stUpdate = getUpdateStatement(null);
				return stUpdate.executeUpdate(statement);
			} catch (Exception e) {
				handleStatementException(e, statement, "DATABASE-UPDATE");
			}
		}
	}

	/**
	 * <p>Handle an exception thrown during the execution of an SQL statement,
	 * attempting to reconnect to the database if necessary.</p>
	 * 
	 * <p>If the exception is an SQLException, attempts to check whether it
	 * was caused by a loss of the database connection.  It checks the
	 * exception chain to find the root cause of the exception.  If no
	 * exception chain is available (not all JDBC drivers can be guaranteed to
	 * create one), exception message parsing is used as the fallback.</p>
	 * 
	 * <p>If the SQLException cannot be determined to come from a loss of db
	 * connection, its details are logged and it is re-thrown.</p>
	 * 
	 * <p>If the Exception was not an SQLException, it is logged, and then 
	 * chained to an SQLException which is thrown.</p>
	 * 
	 * @param exception The exception that was caught by the caller.
	 * @param statement The statement that was being executed.
	 * @param subroutine The subroutine name to use when logging.
	 * @throws SQLException
	 */
	private static void handleStatementException(Exception exception, String statement, String subroutine) throws SQLException
	{
		if (exception instanceof SQLException) {
			SQLException sqlException = (SQLException) exception;
			Throwable cause = sqlException.getCause();

			// Log useful details about this exception
			Log.e(subroutine, "Statement caused SQLException: " + statement);
			Log.e(subroutine, "Exception details: " + sqlException);
			Log.d(subroutine, "Exception cause: " + cause);
			Log.d(subroutine, "Exception error code: " + sqlException.getErrorCode());
			Log.d(subroutine, "Exception SQLState: " + sqlException.getSQLState());
			Log.d(subroutine, "Next exception in chain: " + sqlException.getNextException());

			/* 
			 * PostgreSQL's JDBC driver may be compiled without exception 
			 * chaining, in which case checking the root cause of the
			 * exception using the getCause() call is futile.  We fall back to
			 * looking for substrings in the error message.
			 */
			boolean lostConnection;
			if (cause != null) {
				lostConnection = cause instanceof SocketException || cause instanceof IOException;
			} else {
				String msg = sqlException.getMessage();
				lostConnection = msg.indexOf("SocketException") >= 0 || msg.indexOf("IOException") >= 0;
			}

			if (lostConnection) {
				DBDescr db = getDBDescr(null);
				synchronized (db) {
					// Reconnect database loop
					while (!db.verifyConnection()) {
						Log.w(subroutine, "Database is not connected.");
						try {
							if (!db.reconnect()) {
								Log.e(subroutine, "Database reconnect failed");
								if (db.getReturnOnReconnectFail()) {
									SQLException sqle = new SQLException("Database appears to be down");
									sqle.initCause(sqlException);
									throw sqle;
								} else {
									Log.w(subroutine, "Attempting to reconnect in " + DEFAULT_RECONNECT_WAIT_TIME + " ms");
									Thread.sleep(DEFAULT_RECONNECT_WAIT_TIME);
								}
							} else {
								Log.i(subroutine, "Reconnected lost database connection");
							}
						} catch (InterruptedException ie) {
						}
					}
				}
			} else {
				/* If we couldn't determine that the exception was due to loss
				 * of connectivity, we just log it and throw it back up.
				 */
				logStackTrace("SQLException thrown while processing statement: " + statement, sqlException);
				throw sqlException;
			}
		} else {
			// Unknown exceptions are wrapped in an SQLException and thrown
			logStackTrace("Unhandled exception thrown while running statement: " + statement, exception);
			SQLException newException = new SQLException("Got unexpected Exception during SQL query");
			newException.initCause(exception);
			throw newException;
		}
	}

	/**
	 * Quickly log a stacktrace to stderr, with associated message.
	 * @param message An optional message to log.
	 * @param t A throwable whose associated stacktrace will be logged.
	 */
	private static void logStackTrace(String message, Throwable t)
	{
	 	System.err.println(dateFormat.format(new GregorianCalendar().getTime()));
		if (message != null && message.length() > 0) {
			System.err.println(message);
		}
		t.printStackTrace(System.err);
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
			String s;
			if ((s=rs.getString(i)) != null)
				hm.put(md.getColumnName(i), s);
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
		if (s.startsWith("(")) s = "\\" + s;
		return addSlashesStrict(s);
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
