package no.ntnu.nav.eventengine.handlerplugins.BoxState;

/**
 * BoxState plugin for eventengine. Handles all events dealing with
 * netboxes and their modules going up/down.
 */

import java.util.*;

import no.ntnu.nav.ConfigParser.*;

import no.ntnu.nav.eventengine.*;
import no.ntnu.nav.eventengine.deviceplugins.Box.*;
import no.ntnu.nav.eventengine.deviceplugins.Netel.*;

public class BoxState implements EventHandler, EventCallback
{
	private static final boolean DEBUG_OUT = true;

	private Map startEventMap = new HashMap();
	private int lastDownCount;

	public String[] handleEventTypes()
	{
		return new String[] { "boxState", "moduleState", "linkState", "coldStart", "warmStart" };
	}

	public void handle(DeviceDB ddb, Event e, ConfigParser cp)
	{
		outld("BoxState handling event: " + e);

		Device d = ddb.getDevice(e.getDeviceid());
		if (d == null) {
			errl("BoxState.handle: Error, device with deviceid="+e.getDeviceid()+" not found!");
			return;
		}

		String eventtype = e.getEventtypeid();
		boolean callback = false;

		if (eventtype.equals("boxState")) {
			if (d instanceof Box) {
				Box b = (Box)d;
				if (e.getState() == Event.STATE_START) {
					if (!b.isUp() && startEventMap.containsKey(e.getDeviceidI())) {
						outld("BoxState  Ignoring duplicate down event for Box");
						e.dispose();
						return;
					}
					outld("BoxState  Box going down");
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
							outld("BoxState  Ignoring box up event as no down event was found!");
							e.dispose();
							return;
						}
						// For now ignore transient events
						startEventMap.remove(e.getDeviceidI());
						se.dispose();
						e.dispose();
						outld("BoxState  Ignoring transient boxState");
					} else {
						outld("BoxState  Box going up");

						// Post alert
						a = ddb.alertFactory(e, "boxUp");
						a.addEvent(e);

						try {
							ddb.postAlert(a);
						} catch (PostAlertException exp) {
							errl("BoxState  Error, PostAlertException: " + exp.getMessage());
						}
						
						// Clean up
						startEventMap.remove(e.getDeviceidI());
					}
					b.up();
				}

				//outld("BoxState  Box: " + b);

			} else {
				errl("BoxState    Device " + d + " not Box or sub-class of Box: " + getClassH(d.getClass()) );
				return;
			}
		} else if (eventtype.equals("moduleState") || eventtype.equals("linkState")) {
			if (d instanceof Module) {
				Module m = (Module)d;
				if (eventtype.equals("linkState")) {
					Port p = m.getPort(e.getSubid());
					if (p == null) {
						errl("BoxState  Error, port="+e.getSubid()+" in module="+m.getModule()+" not found!");
						return;
					}
					if (e.getState() == Event.STATE_START) p.down();
					else if (e.getState() == Event.STATE_END) p.up();
					e.dispose();

					outld("BoxState  Port: " + p);
				} else {
					if (e.getState() == Event.STATE_START) {
						if (!m.isUp() && startEventMap.containsKey(e.getDeviceidI())) {
							outld("BoxState  Ignoring duplicate down event for Module");
							e.dispose();
							return;
						}
						outld("BoxState  Module going down");
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
								outld("BoxState  Ignoring module up event as no down event was found!");
								e.dispose();
								return;
							}
							// For now ignore transient events
							startEventMap.remove(e.getDeviceidI());
							se.dispose();
							e.dispose();
							outld("BoxState  Ignoring transient moduleState");
						} else {
							outld("BoxState  Module going up");

							// Post alert
							a = ddb.alertFactory(e, "moduleUp");
							a.addEvent(e);
							try {
								ddb.postAlert(a);
							} catch (PostAlertException exp) {
								errl("BoxState  Error, PostAlertException: " + exp.getMessage());
							}

							// Clean up
							startEventMap.remove(e.getDeviceidI());
						}
						m.up();
					}

					//outld("BoxState  Module: " + m);
				}

			} else {
				errl("BoxState    Device not Module or sub-class of Module");
				return;
			}
		} else if (eventtype.equals("coldStart") || eventtype.equals("warmStart")) {
			// Do nothing (yet)
			outld("BoxState  Ignoring event " + eventtype);
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

			outld("BoxState  Scheduling  callback, alertTickLength="+alertTickLength+" alertTicks="+alertTicks);
			ddb.scheduleCallback(this, alertTickLength * 1000, alertTicks);
		}

	}

	/**
   * Return the class hierarchy for c as a String.
   */
	private String getClassH(Class c) {
		if (c.getSuperclass() == null) return "";
		return getClassH(c.getSuperclass()) + " <- " + c.getName();
	}



	private boolean sentWarning = false;

	public void callback(DeviceDB ddb, int invocationsRemaining)
	{
		int downCount = Netel.boxDownCount();

		outld("BoxState callback, lastDownCount="+lastDownCount+", downCount="+downCount+", invocationsRemaining="+invocationsRemaining+ " sentWarning="+sentWarning);

		if ( (downCount == lastDownCount && !sentWarning) || invocationsRemaining == 0) {
			
			// Just in case alertTicks = 1; in this case we don't send out warnings
			if (invocationsRemaining == 0 && !sentWarning) sentWarning = true;

			// We are now ready to post alerts
			for (Iterator i=Netel.findBoxesDown(); i.hasNext();) {
				Box b = (Box)i.next();
				outld("BoxState: Box down: " + b);

				if (b instanceof Netel) {
					Netel n = (Netel)b;

					if (!n.isUp()) {
						// The box iself is down, this means we don't report modules down if any
						// Find the down event
						Event e = (Event)startEventMap.get(n.getDeviceidI());
						if (e == null) {
							errl("BoxState.callback: Error, Netel " + n + " is down, but no start event found!");
							continue;
						}
						if (sentWarning) startEventMap.remove(n.getDeviceidI());

						// Ask the Box to update its status
						n.updateStatus();

						// Create alert
						Alert a = ddb.alertFactory(e);

						// Set status (down or shadow)
						a.addVar("status", n.getStatusS());

						// Update alerttype
						String alerttype = "";
						if (n.getStatus() == Box.STATUS_SHADOW) {
							alerttype = "boxShadow";
						} else if (n.getStatus() == Box.STATUS_DOWN) {
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

						outld("  added alert: " + a);

						// Post the alert
						try {
							ddb.postAlert(a);
						} catch (PostAlertException exp) {
							errl("BoxState.callback: While posting netel down alert, PostAlertException: " + exp.getMessage());
						}


					} else {
						// The box is up, one of more modules must be down
						for (Iterator md = n.getModulesDown(); md.hasNext();) {
							Module m = (Module)md.next();
							if (m.isUp()) continue;

							// Find the down event
							Event e = (Event)startEventMap.remove(m.getDeviceidI());
							if (e == null) {
								errl("BoxState.callback: Error, Module " + m + " is down, but no start event found!");
								continue;
							}

							// Create alert
							Alert a = ddb.alertFactory(e, "moduleDown");
							a.addEvent(e);

							// Post the alert
							try {
								ddb.postAlert(a);
							} catch (PostAlertException exp) {
								errl("BoxState.classback: While posting module down alert, PostAlertException: " + exp.getMessage());
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
			outld("BoxState.callback: Alert processing done, events remaining: " + startEventMap.size());

		}

		lastDownCount = downCount;



	}


	private static void outd(Object o) { if (DEBUG_OUT) System.out.print(o); }
	private static void outld(Object o) { if (DEBUG_OUT) System.out.println(o); }

	private static void err(Object o) { System.err.print(o); }
	private static void errl(Object o) { System.err.println(o); }

}
