package no.ntnu.nav.getDeviceData.dataplugins.Mem;

import java.util.*;
import java.sql.*;

import no.ntnu.nav.logger.*;
import no.ntnu.nav.Database.*;
import no.ntnu.nav.getDeviceData.Netbox;
import no.ntnu.nav.getDeviceData.dataplugins.*;

/**
 * DataHandler plugin for getDeviceData; provides an interface for storing
 * memory info.
 *
 * @see MemContainer
 */

public class MemHandler implements DataHandler {

	/**
	 * Fetch initial data from mem table.
	 */
	public synchronized void init(Map persistentStorage, Map changedDeviceids) {
		if (persistentStorage.containsKey("initDone")) return;
		persistentStorage.put("initDone", null);
	}

	/**
	 * Return a DataContainer object used to return data to this
	 * DataHandler.
	 */
	public DataContainer dataContainerFactory() {
		return new MemContainer(this);
	}
	
	/**
	 * Store the data in the DataContainer in the database.
	 */
	public void handleData(Netbox nb, DataContainer dc, Map changedDeviceids) {
		if (!(dc instanceof MemContainer)) return;
		MemContainer mc = (MemContainer)dc;
		if (!mc.isCommited()) return;

		Log.setDefaultSubsystem("MemHandler");
		int newcnt = 0, updcnt = 0;

		String netboxid = nb.getNetboxidS();
		try {
			Map m = new HashMap();
			ResultSet rs = Database.query("SELECT memid, memtype, device, size, used FROM mem WHERE netboxid='"+netboxid+"'");
			while (rs.next()) {
				String key = rs.getString("memtype") + ":" + rs.getString("device");
				long[] data = new long[] { rs.getLong("size"), rs.getLong("used"), rs.getLong("memid") };
				m.put(key, data);
			}

			for (Iterator it = mc.getMem(); it.hasNext();) {
				Object[] o = (Object[])it.next();
				String type = (String)o[0];
				String device = (String)o[1];
				long size = ((Long)o[2]).longValue();
				long used = ((Long)o[3]).longValue();
				String key = type+":"+device;

				long[] old = (long[])m.remove(key);
				if (old == null) {
					String[] ins = {
						"memid", "",
						"netboxid", netboxid,
						"memtype", type,
						"device", device,
						"size", ""+size,
						"used", ""+used,
					};
					Database.insert("mem", ins, null);
						
				} else {
					if (size != old[0] || used != old[1]) {
						String[] set = {
							"size", ""+size,
							"used", ""+used,
						};
						String[] where = {
							"memid", ""+old[2],
						};
						Database.update("mem", set, where);
					}
				}
			}

			StringBuffer sb = new StringBuffer();
			for (Iterator it = m.values().iterator(); it.hasNext();) {
				long[] old = (long[])it.next();
				sb.append(old[2]+",");
			}
			if (sb.length() > 0) {
				sb.deleteCharAt(sb.length()-1);
				Database.update("DELETE FROM mem WHERE memid IN ("+sb+")");
			}

		} catch (SQLException e) {
			Log.e("HANDLE", "SQLException: " + e.getMessage());
			e.printStackTrace(System.err);
		}

		if (newcnt > 0 || updcnt > 0) {
			Log.i("HANDLE", nb.getSysname() + ": New: " + newcnt + ", Updated: " + updcnt);
		}

	}

}
