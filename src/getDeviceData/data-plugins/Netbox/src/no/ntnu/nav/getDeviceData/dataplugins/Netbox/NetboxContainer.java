package no.ntnu.nav.getDeviceData.dataplugins.Netbox;

import java.util.*;
import java.sql.ResultSet;
import java.sql.SQLException;

import no.ntnu.nav.Database.*;
import no.ntnu.nav.logger.*;
import no.ntnu.nav.getDeviceData.Netbox;
import no.ntnu.nav.getDeviceData.dataplugins.*;
import no.ntnu.nav.getDeviceData.dataplugins.Device.DeviceContainer;

/**
 * <p>
 * The interface to device plugins for storing collected data.
 * </p>
 *
 * <p> This plugin provides an interface for storing logical netbox
 * data and data about the physical device which the netbox
 * represent.</p>
 * 
 * <p> For storing data the device plugin should request a {@link
 * NetboxData NetboxData} from the {@link #netboxDataFactory
 * netboxDataFactory} method, giving the type, sysname, serial number,
 * and, if available, the hardware and software version. </p>
 *
 * @see NetboxHandler
 */

public class NetboxContainer extends DeviceContainer implements DataContainer {

	private NetboxHandler nh;
	private NetboxData nd;
	private boolean commit = false;

	protected NetboxContainer(NetboxHandler nh) {
		super(null);
		this.nh = nh;
	}

	/**
	 * Get the name of the container; returns the string NetboxContainer
	 */
	public String getName() {
		return "NetboxContainer";
	}

	/**
	 * Get a data-handler for this container; this is a reference to the
	 * NetboxHandler object which created the container.
	 */
	public DataHandler getDataHandler() {
		return nh;
	}

	/**
	 * <p> Return a NetboxData object which is used to describe a single
	 * netbox. Since deviceplugins only works with a single netbox at a
	 * time, it should only be neccessary to call this method once;
	 * further calls will return identical references. </p>
	 *
	 * <p> The nb argument should simply be the same reference as given
	 * in the DeviceHandler interface; the reason this is neccessary is
	 * so the correct type and typegroup can be set when commit() is
	 * called. This information is required by other device
	 * plugins. </p>
	 */
	public NetboxData netboxDataFactory(String serial, String hw_ver, String sw_ver, Netbox nb, String type, String sysname) {
		if (nd == null) {
			nd = new NetboxData(serial, hw_ver, sw_ver, nb, type, sysname);
		}
		return nd;
	}

	public void commit() {
		// Here we need to do some magic because other plugins need to know the correct type
		NetboxUpdatable nb = (NetboxUpdatable)nd.getNetbox();
		nb.setType(nd.getType());
		nb.setSysname(nd.getSysname());

		commit = true;		
	}

	// Doc in parent
	protected boolean isCommited() {
		return commit;
	}
	
	NetboxData getNetbox() {
		return nd;
	}


}
