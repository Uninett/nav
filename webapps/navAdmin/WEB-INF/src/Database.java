/*
 * NTNU ITEA "nav" prosjekt
 *
 * Database interface class
 *
 * Skrvet av: Kristian Eide <kreide@online.no>
 *
 */

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.Date;

public class Database
{
    private static final String dbDriverOracle = "oracle.jdbc.driver.OracleDriver";
    private static final String dbDriverPostgre = "org.postgresql.Driver";
    private static final String dbDriverMysql = "org.gjt.mm.mysql.Driver";

    private static final String dbName = "postgresql";
    //private static final String dbName = "mysql";

    private static final String dbDriver = dbDriverPostgre;

    private static Connection connection;
    private static Statement[] stQuery = new Statement[40];
    private static Statement stUpdate;
    private static int queryCount;
    private static int queryPos;
    private static boolean queryQFull = false;

    private static int connectionCount = 0;

    public static synchronized boolean openConnection(String serverName, String dbName, String user, String pw) {
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

			connection = DriverManager.getConnection("jdbc:postgresql://" + serverName + "/" + dbName, user, pw);
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

    public static synchronized ResultSet query(String statement) throws SQLException
    {
		//try {
			//System.out.println(String.valueOf(new StringBuffer("Query(#").append(queryTeller).append("): ").append(statement)));
			if (queryPos==stQuery.length) {
				if (!queryQFull) queryQFull = true;
				queryPos = 0;
			}
			if (queryQFull) stQuery[queryPos].close();

			Statement st = connection.createStatement();
			stQuery[queryPos] = st;
			queryCount++;
			queryPos++;
			ResultSet resultset = st.executeQuery(statement);
			return resultset;
		//} catch (SQLException e) {
		//	System.err.println("Query error: ".concat(e.getMessage()));
		//	return null;
		//}
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

    public static boolean insert(String table, String[] feltVerdi) {
		if ((feltVerdi.length & 0x1) == 1)
			return false;
		String query = String.valueOf(new StringBuffer("INSERT INTO ").append(table).append(" ("));
		for (int i = 0; i < feltVerdi.length; i += 2) {
			if (i != 0)
			query = query.concat(",");
			query = query.concat(feltVerdi[i]);
		}
		query = query.concat(") VALUES (");
		for (int i = 1; i < feltVerdi.length; i += 2) {
			if (i != 1)
			query = query.concat(",");
			String fnutt = "'";
			if (feltVerdi[i].equals("NOW()")) fnutt = "";
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

    public static boolean update(String table, String[] feltVerdi, String[] keyNavnVerdi) {
		if ((feltVerdi.length & 0x1) == 1 || (keyNavnVerdi.length & 0x1) == 1)
			return false;
		String query = String.valueOf(new StringBuffer("UPDATE ").append(table).append(" SET "));
		for (int i = 0; i < feltVerdi.length; i += 2) {
			if (i != 0) query += ",";

			String fnutt = "'";
			if (feltVerdi[i].equals("NOW()")) fnutt = "";

			query += feltVerdi[i] + "=" + fnutt + addSlashes(feltVerdi[i+1]) + fnutt;
		}
		query = query.concat(" WHERE ");
		for (int i = 0; i < keyNavnVerdi.length; i += 2) {
			if (i != 0)
			query = query.concat(" AND ");
			query = query.concat(String.valueOf(new StringBuffer(keyNavnVerdi[i]).append("='").append(addSlashes(keyNavnVerdi[i + 1])).append("'")));
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

    public static synchronized boolean update(String query)
    {
		try {
			//System.out.println("Update query: ".concat(query));
			stUpdate.close();
			stUpdate = connection.createStatement();
			stUpdate.executeUpdate(query);
			return true;
		} catch (SQLException e) {
			System.err.println("Update query error: ".concat(e.getMessage()));
			System.err.println("Query with error: ".concat(query));
			return false;
		}
	}

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
