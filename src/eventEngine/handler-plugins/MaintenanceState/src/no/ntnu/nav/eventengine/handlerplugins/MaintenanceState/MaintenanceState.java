package no.ntnu.nav.eventengine.handlerplugins.MaintenanceState;

import java.util.*;

import no.ntnu.nav.ConfigParser.*;
import no.ntnu.nav.logger.*;

import no.ntnu.nav.eventengine.*;
import no.ntnu.nav.eventengine.deviceplugins.Box.*;

/**
 * MaintenanceState plugin for eventengine. Handles all events dealing with
 * netboxes and their modules going on/off maintenance.
 */

public class MaintenanceState implements EventHandler
{
	public String[] handleEventTypes()
	{
		return new String[] { "maintenanceState" };
	}

	public void handle(DeviceDB ddb, Event e, ConfigParser cp)
	{
		Log.setDefaultSubsystem("MAINTENANCE_HANDLER");
		Log.d("HANDLE", "Event: " + e);

		Device d = ddb.getDevice(e.getDeviceid());
		if (d == null) {
			Log.w("HANDLE", "Device with deviceid="+e.getDeviceid()+" not found!");
			e.defer("Device with deviceid="+e.getDeviceid()+" not found!");
			return;
		}

		Alert a;

		if (d instanceof Box) {
			Box b = (Box)d;
			if (e.getState() == Event.STATE_START) {
				b.onMaintenance(true);
				a = ddb.alertFactory(e, "onMaintenance");
			} else if (e.getState() == Event.STATE_END) {
				b.onMaintenance(false);
				a = ddb.alertFactory(e, "offMaintenance");
			} else {
				Log.w("HANDLE", "MaintenanceState events cannot be stateless, ignoring event");
				return;
			}
				
		} else {
			Log.w("HANDLE", "Device " + d + " not Box or sub-class of Box: " + d.getClassH());
			return;
		}
		
		a.addEvent(e);

		try {
			ddb.postAlert(a);
		} catch (PostAlertException exp) {
			Log.e("HANDLE", "Exception when trying to post alert " + a+ ", msg: " + exp);
		}
	}

}
