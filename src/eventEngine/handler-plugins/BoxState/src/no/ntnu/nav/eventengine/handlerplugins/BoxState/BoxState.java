package no.ntnu.nav.eventengine.handlerplugins.BoxState;

import java.util.*;

import no.ntnu.nav.ConfigParser.*;
import no.ntnu.nav.logger.*;

import no.ntnu.nav.eventengine.*;
import no.ntnu.nav.eventengine.deviceplugins.Box.*;
import no.ntnu.nav.eventengine.deviceplugins.Netel.*;

/**
 * BoxState plugin for eventengine. Handles all events dealing with
 * netboxes and their modules going up/down.
 */

public class BoxState implements EventHandler, EventCallback
{
	private Map startEventMap = new HashMap();
	private int lastDownCount;

	public String[] handleEventTypes()
	{
		return new String[] { "boxState", "moduleState", "linkState", "coldStart", "warmStart" };
	}

	public void handle(DeviceDB ddb, Event e, ConfigParser cp)
	{
		Log.setDefaultSubsystem("BOX_STATE_EVENTHANDLER");
		Log.d("HANDLE", "Event: " + e);

		Device d = ddb.getDevice(e.getDeviceid());
		if (d == null) {
			Log.w("HANDLE", "Device with deviceid="+e.getDeviceid()+" not found!");
			return;
		}

		String eventtype = e.getEventtypeid();
		boolean callback = false;

		if (eventtype.equals("boxState")) {
			if (d instanceof Box) {
				Box b = (Box)d;

				if (b.onMaintenance()) {
					// We simply ignore any events from boxes on maintenance
					Log.d("HANDLE", "Ignoring event as the box is on maintenance");
					e.dispose();
					return;
				}

				if (e.getState() == Event.STATE_START) {
					if (!b.isUp() && startEventMap.containsKey(e.getDeviceidI())) {
						Log.d("HANDLE", "Ignoring duplicate down event for Box");
						e.dispose();
						return;
					}
					Log.d("HANDLE", "Box going down");
					b.down();
					startEventMap.put(e.getDeviceidI(), e);
					callback = true;
				} else if (e.getState() == Event.STATE_END) {
					// Get the down alert
					Alert a = ddb.getDownAlert(e);
					if (a == null) {
						// The down event could be in the startEventMap queue
						Event se = (Event)startEventMap.get(e.getDeviceidI());
						if (se == null) {
							Log.d("HANDLE", "Ignoring box up event as no down event was found!");
							e.dispose();
							return;
						}
						// For now ignore transient events
						startEventMap.remove(e.getDeviceidI());
						se.dispose();
						e.dispose();
						Log.d("HANDLE", "Ignoring transient boxState");
					} else {
						Log.d("HANDLE", "Box going up");

						// Post alert
						a = ddb.alertFactory(e, "boxUp");
						a.addEvent(e);

						try {
							ddb.postAlert(a);
						} catch (PostAlertException exp) {
							Log.w("HANDLE", "PostAlertException: " + exp.getMessage());
						}
						
						// Clean up
						startEventMap.remove(e.getDeviceidI());
					}
					b.up();
				}

			} else {
				Log.w("HANDLE", "Device " + d + " not Box or sub-class of Box: " + d.getClassH());
				return;
			}
		} else if (eventtype.equals("moduleState") || eventtype.equals("linkState")) {
			if (d instanceof Module) {
				Module m = (Module)d;
				if (eventtype.equals("linkState")) {
					Port p = m.getPort(e.getSubid());
					if (p == null) {
						Log.d("HANDLE", "Port="+e.getSubid()+" in module="+m.getModule()+" not found!");
						return;
					}
					if (e.getState() == Event.STATE_START) p.down();
					else if (e.getState() == Event.STATE_END) p.up();
					e.dispose();

					Log.d("HANDLE", "Port: " + p);
				} else {
					if (e.getState() == Event.STATE_START) {
						if (!m.isUp() && startEventMap.containsKey(e.getDeviceidI())) {
							Log.d("HANDLE", "Ignoring duplicate down event for Module");
							e.dispose();
							return;
						}
						Log.d("HANDLE", "Module going down");
						m.down();
						startEventMap.put(e.getDeviceidI(), e);
						callback = true;
					} else if (e.getState() == Event.STATE_END) {
						// Get the down alert
						Alert a = ddb.getDownAlert(e);
						if (a == null) {
							// The down event could be in the startEventMap queue
							Event se = (Event)startEventMap.get(e.getDeviceidI());
							if (se == null) {
								Log.d("HANDLE", "Ignoring module up event as no down event was found!");
								e.dispose();
								return;
							}
							// For now ignore transient events
							startEventMap.remove(e.getDeviceidI());
							se.dispose();
							e.dispose();
							Log.d("HANDLE", "Ignoring transient moduleState");
						} else {
							Log.d("HANDLE", "Module going up");

							// Post alert
							a = ddb.alertFactory(e, "moduleUp");
							a.addEvent(e);
							try {
								ddb.postAlert(a);
							} catch (PostAlertException exp) {
								Log.w("HANDLE", "PostAlertException: " + exp.getMessage());
							}

							// Clean up
							startEventMap.remove(e.getDeviceidI());
						}
						m.up();
					}

					//outld("BoxState  Module: " + m);
				}

			} else {
				Log.w("HANDLE", "Device not Module or sub-class of Module");
				return;
			}
		} else if (eventtype.equals("coldStart") || eventtype.equals("warmStart")) {
			// Do nothing (yet)
			Log.d("HANDLE", "Ignoring event " + eventtype);
			e.dispose();
			return;
		}

		int downCount = Netel.boxDownCount();
		boolean scheduledCB = ddb.isScheduledCallback(this);
		if (downCount == 0 && scheduledCB) {
			ddb.cancelCallback(this);
		} else
		if (callback && !scheduledCB) {
			lastDownCount = downCount;

			int alertTickLength = 60;
			int alertTicks = 4;

			try {
				alertTickLength = Integer.parseInt(cp.get("alertTickLength"));
			} catch (Exception exp) { }

			try {
				alertTicks = Integer.parseInt(cp.get("alertTicks"));
			} catch (Exception exp) { }

			Log.d("HANDLE", "Scheduling  callback, alertTickLength="+alertTickLength+" alertTicks="+alertTicks);
			ddb.scheduleCallback(this, alertTickLength * 1000, alertTicks);
		}

		Log.d("HANDLE", "Finished handling event, startEventMap size="+startEventMap.size() + " callback: " + ddb.isScheduledCallback(this));

	}


	private boolean sentWarning = false;

	public void callback(DeviceDB ddb, int invocationsRemaining)
	{
		Log.setDefaultSubsystem("BOX_STATE_EVENTHANDLER");

		int downCount = Netel.boxDownCount();
		Log.d("CALLBACK", "lastDownCount="+lastDownCount+", downCount="+downCount+", invocationsRemaining="+invocationsRemaining+ " sentWarning="+sentWarning);

		if ( (downCount == lastDownCount && !sentWarning) || invocationsRemaining == 0) {
			
			// Just in case alertTicks = 1; in this case we don't send out warnings
			if (invocationsRemaining == 0 && !sentWarning) sentWarning = true;

			// We are now ready to post alerts
			for (Iterator i=Netel.findBoxesDown(); i.hasNext();) {
				Box b = (Box)i.next();
				Log.d("CALLBACK", "Box down: " + b.getSysname());

				if (!b.isUp()) {
					// The box iself is down, this means we don't report modules down if any
					// Find the down event
					Event e = (Event)startEventMap.get(b.getDeviceidI());
					if (e == null) {
						Log.w("CALLBACK", "Box " + b.getSysname() + " is down, but no start event found!");
						continue;
					}
					if (sentWarning) startEventMap.remove(b.getDeviceidI());

					// Ask the Box to update its status
					b.updateStatus();

					// Create alert
					Alert a = ddb.alertFactory(e);

					// Set status (down or shadow)
					a.addVar("status", b.getStatusS());

					// Update alerttype
					String alerttype = "";
					if (b.getStatus() == Box.STATUS_SHADOW) {
						alerttype = "boxShadow";
					} else if (b.getStatus() == Box.STATUS_DOWN) {
						alerttype = "boxDown";
					}

					// First send a warning
					if (!sentWarning) {
						a.setState(Event.STATE_NONE);
						alerttype += "Warning";
					} else {
						// Delete 'down' event when alert is posted
						a.addEvent(e);
					}

					a.setAlerttype(alerttype);

					Log.d("BOX_STATE_EVENTHANDLER", "CALLBACK", "Added alert: " + a);

					// Post the alert
					try {
						ddb.postAlert(a);
					} catch (PostAlertException exp) {
						Log.w("BOX_STATE_EVENTHANDLER", "CALLBACK", "While posting netel down alert, PostAlertException: " + exp.getMessage());
					}
				} else {
					// Box is up, this means it is a Netbox with modules down
					if (b instanceof Netel) {
						Netel n = (Netel)b;

						// The box is up, one or more modules must be down
						for (Iterator md = n.getModulesDown(); md.hasNext();) {
							Module m = (Module)md.next();
							if (m.isUp()) continue;
							
							// Find the down event
							Event e = (Event)startEventMap.remove(m.getDeviceidI());
							if (e == null) {
								Log.w("BOX_STATE_EVENTHANDLER", "CALLBACK", "Module " + m + " is down, but no start event found!");
								continue;
							}
							
							// Create alert
							Alert a = ddb.alertFactory(e, "moduleDown");
							a.addEvent(e);
							
							// Post the alert
							try {
								ddb.postAlert(a);
							} catch (PostAlertException exp) {
								Log.w("BOX_STATE_EVENTHANDLER", "CALLBACK", "While posting module down alert, PostAlertException: " + exp.getMessage());
							}
						}
						
					}
					
				}

			}

			sentWarning = !sentWarning;

			/*
			if (!eventMap.isEmpty()) {
				errl("BoxState: Error, eventMap is not empty after alert processing!");
			}
			*/
			Log.d("BOX_STATE_EVENTHANDLER", "CALLBACK", "Alert processing done, startEventMap size=" + startEventMap.size() + " sentWarning="+sentWarning);

		}

		lastDownCount = downCount;



	}

}
