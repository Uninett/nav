package no.ntnu.nav.eventengine.handlerplugins.Info;

/**
 * Info plugin for eventengine; forwards all events as-is directly to alertengine. This plugin
 * is used for informal events which need no processing.
 */

import java.util.*;

import no.ntnu.nav.ConfigParser.*;

import no.ntnu.nav.eventengine.*;

public class Info implements EventHandler
{
	private static final boolean DEBUG_OUT = false;

	public String[] handleEventTypes()
	{
		return new String[] { "info" };
	}

	public void handle(DeviceDB ddb, Event e, ConfigParser cp)
	{
		outld("Info plugin handling event: " + e);

		Alert a = ddb.alertFactory(e);
		a.addEvent(e);

		try {
			ddb.postAlert(a);
		} catch (PostAlertException exp) {
			System.err.println("Info: Exception when trying to post alert " + a+ ", msg: " + exp);
		}
	}


	private static void outd(Object o) { if (DEBUG_OUT) System.out.print(o); }
	private static void outld(Object o) { if (DEBUG_OUT) System.out.println(o); }

	private static void err(Object o) { System.err.print(o); }
	private static void errl(Object o) { System.err.println(o); }

}
