package no.ntnu.nav.eventengine.handlerplugins.ThresholdState;

import java.util.*;

import no.ntnu.nav.ConfigParser.*;
import no.ntnu.nav.logger.*;

import no.ntnu.nav.eventengine.*;

/**
 * ThresholdState plugin for eventengine. Handles all events dealing with
 * various thresholds being exceeded.
 */

public class ThresholdState implements EventHandler
{
	public String[] handleEventTypes()
	{
		return new String[] { "thresholdState" };
	}

	public void handle(DeviceDB ddb, Event e, ConfigParser cp)
	{
		Log.setDefaultSubsystem("THRESHOLD_HANDLER");
		Log.d("HANDLE", "Event: " + e);

		Alert a = ddb.alertFactory(e);
		a.addEvent(e);

		if (e.getState() == Event.STATE_START) {
			a.setAlerttype("exceededThreshold");
		} else if (e.getState() == Event.STATE_END) {
			a.setAlerttype("belowThreshold");
		}

		try {
			ddb.postAlert(a);
		} catch (PostAlertException exp) {
			Log.e("INFO_HANDLER", "HANDLE", "Exception when trying to post alert " + a+ ", msg: " + exp);
		}

	}

}
