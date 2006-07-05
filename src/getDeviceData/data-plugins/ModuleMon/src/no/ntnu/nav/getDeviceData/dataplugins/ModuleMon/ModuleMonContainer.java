package no.ntnu.nav.getDeviceData.dataplugins.ModuleMon;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Set;

import no.ntnu.nav.Database.Database;
import no.ntnu.nav.getDeviceData.Netbox;
import no.ntnu.nav.getDeviceData.dataplugins.DataContainer;
import no.ntnu.nav.getDeviceData.dataplugins.DataHandler;
import no.ntnu.nav.logger.Log;

/**
 * <p>
 * The interface to device plugins for storing collected data.
 * </p>
 *
 * @see ModuleMonHandler
 */

public class ModuleMonContainer implements DataContainer {

	public static final int PRIORITY_MODULE_MON = PRIORITY_NORMAL;

	private ModuleMonHandler mmh;
	private boolean commit = false;

	//private MultiMap queryIfindices;
	//private Map moduleToIfindex;
	private Set moduleUpSet = new HashSet();

	protected ModuleMonContainer(ModuleMonHandler mmh) {
		this.mmh = mmh;
		//this.queryIfindices = queryIfindices;
		//this.moduleToIfindex = moduleToIfindex;
	}

	/**
	 * Get the name of the container; returns the string ModuleMonContainer
	 */
	public String getName() {
		return "ModuleMonContainer";
	}

	// Doc in interface
	public int getPriority() {
		return PRIORITY_MODULE_MON;
	}

	/**
	 * Get a data-handler for this container; this is a reference to the
	 * ModuleMonHandler object which created the container.
	 */
	public DataHandler getDataHandler() {
		return mmh;
	}

	public Set getModuleSet(String netboxid) {
		Set s = new HashSet();
		try {
			ResultSet rs = Database.query("SELECT module FROM module WHERE netboxid='"+netboxid+"'");
			while (rs.next()) {
				s.add(rs.getString("module"));
			}
		} catch (SQLException e) {
			Log.e("INIT", "SQLException: " + e.getMessage());
			e.printStackTrace(System.err);
		}
		return s;
	}

	/**
	 * <p> Give a list of ifindices to query.  </p>
	 */
	public Iterator getQueryIfindices(String netboxid) {
		Map m = new HashMap();
		try {
			ResultSet rs = Database.query("SELECT ifindex, module FROM module JOIN swport USING(moduleid) WHERE netboxid='"+netboxid+"' ORDER BY module, port IS NOT NULL DESC, RANDOM()");
			while (rs.next()) {
				List l;
				String module = rs.getString("module");
				if ( (l=(List)m.get(module)) == null) m.put(module, l = new ArrayList());
				l.add(rs.getString("ifindex"));
			}
		} catch (SQLException e) {
			Log.e("INIT", "SQLException: " + e.getMessage());
			e.printStackTrace(System.err);
		}
		return m.entrySet().iterator();
	}

	/**
	 * Reschedule the given netbox for the given module and OID. OID =
	 * null means all OIDs.
	 */
	public void rescheduleNetbox(Netbox nb, String module, String oid) {
		rescheduleNetbox(nb, module, Arrays.asList(new String[] { oid }));
	}

	/**
	 * Reschedule the given netbox for the given module and OID. OID =
	 * null means all OIDs.
	 */
	public void rescheduleNetbox(Netbox nb, String module, List oid) {
		int cnt = nb.get(module);
		if (cnt < 3) {
			if (cnt < 0) cnt = 0;
			nb.set(module, ++cnt);
			long delay;
			switch (cnt) {
			case 1: delay = 30; break;
			case 2: delay = 60; break;
			case 3: delay = 120; break;
			default:
				System.err.println("Error in rescheduleNetbox, cnt="+cnt+", should not happen");
				return;
			}
			for (Iterator it=oid.iterator(); it.hasNext();) nb.scheduleOid((String)it.next(), delay);
		}
	}

	/**
	 * <p> Returns the ifindices to ask for the given module.  </p>
	 */
	public Iterator ifindexForModule(String netboxid, String module) {
		List l = new ArrayList();
		try {
			ResultSet rs = Database.query("SELECT ifindex FROM module JOIN swport USING(moduleid) WHERE netboxid='"+netboxid+"' AND module='"+module+"' ORDER BY port IS NOT NULL DESC, RANDOM()");
			while (rs.next()) l.add(rs.getString("ifindex"));
		} catch (SQLException e) {
			Log.e("INIT", "SQLException: " + e.getMessage());
			e.printStackTrace(System.err);
		}
		return l.iterator();
	}

	/**
	 * <p> Register that the given module is up on the netbox.
	 * </p>
	 *
	 * @param module The up module
	 */
	public void moduleUp(Netbox nb, String module) {
		moduleUpSet.add(module);
		nb.set(module, 0);
	}

	public void commit() {
		commit = true;		
	}

	boolean isCommited() {
		return commit;
	}

	public Iterator getModulesUp() {
		return moduleUpSet.iterator();
	}

	Set getModulesUpSet() {
		return moduleUpSet;
	}

	public int modulesUpCount() {
		return moduleUpSet.size();
	}


}
