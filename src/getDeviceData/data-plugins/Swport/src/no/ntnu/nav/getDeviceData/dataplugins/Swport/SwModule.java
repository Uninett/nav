/*
 * $Id: SwModule.java 3555 2006-07-17 14:28:20Z mortenv $
 *
 * Copyright 2003-2004 Norwegian University of Science and Technology
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
 *
 *
 * Authors: Kristian Eide <kreide@gmail.com>
 * 
 */
package no.ntnu.nav.getDeviceData.dataplugins.Swport;

import java.util.Map;
import java.util.HashMap;
import java.util.Iterator;

import no.ntnu.nav.getDeviceData.dataplugins.Module.Module;

/**
 * Describes a single switch module.
 */

public class SwModule extends Module implements Comparable
{
	private Map swports = new HashMap();
	private SwportContainer sc;

	SwModule(int module, SwportContainer sc) {
		super(module);
		this.sc = sc;
	}

	SwModule(String serial, String hwVer, String fwVer, String swVer, int module, SwportContainer sc) {
		super(serial, hwVer, fwVer, swVer, module);
		this.sc = sc;
	}
	
	public void setSerial(String s) {
		super.setSerial(s);
	}

	protected void setDeviceid(int i) { super.setDeviceid(i); }

	protected int getModuleid() { return super.getModuleid(); }
	protected String getModuleidS() { return super.getModuleidS(); }
	protected void setModuleid(int i) { super.setModuleid(i); }

	// Doc in parent
	protected String getKey() { return super.getKey(); }

	void addSwport(Swport sd) { swports.put(sd.getIfindex(), sd); }
	Iterator getSwports() { return swports.values().iterator(); }
	int getSwportCount() { return swports.size(); }
	Swport getSwport(String ifindex) { return (Swport)swports.get(ifindex); }
	void ignore() { ignore = true; }

	/**
	 * Return an Swport-object which is used to describe a single switch port.
	 */
	public Swport swportFactory(String ifindex) {
		Swport sw = sc.createOrGetSwport(ifindex);
		sw.assignedToModule();
		swports.put(ifindex, sw);
		return sw;
	}

}
