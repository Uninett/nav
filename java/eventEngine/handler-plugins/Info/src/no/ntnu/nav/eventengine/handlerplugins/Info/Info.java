package no.ntnu.nav.eventengine.handlerplugins.Info;

import java.util.*;

import no.ntnu.nav.ConfigParser.*;
import no.ntnu.nav.logger.*;
import no.ntnu.nav.eventengine.*;

/**
 * Info plugin for eventengine; forwards all events as-is directly to
 * alertengine. This plugin is used for informal events which need no
 * processing.
 */

public class Info implements EventHandler
{
	public String[] handleEventTypes()
	{
		return new String[] { "info" };
	}

	public void handle(DeviceDB ddb, Event e, ConfigParser cp)
	{
		Log.d("INFO_HANDLER", "HANDLE", "Info plugin handling event: " + e);

		Alert a = ddb.alertFactory(e);
		a.addEvent(e);
		if (e.getVar("alerttype") != null) a.setAlerttype(e.getVar("alerttype"));

		try {
			ddb.postAlert(a);
		} catch (PostAlertException exp) {
			Log.e("INFO_HANDLER", "HANDLE", "Exception when trying to post alert " + a+ ", msg: " + exp);
		}
	}

}
