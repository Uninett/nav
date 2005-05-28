package no.ntnu.nav.eventengine.handlerplugins.BoxState;

import java.util.*;
import java.sql.*;

import no.ntnu.nav.Database.*;
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
	private Set sentAlertSet = new HashSet();
	private int lastDownCount;

	public static final int SHADOW_SEVERITY_DEDUCTION = 20;

	public String[] handleEventTypes()
	{
		return new String[] { "boxState", "moduleState", "linkState", "boxRestart" };
	}

	public void handle(DeviceDB ddb, Event e, ConfigParser cp)
	{
		Log.setDefaultSubsystem("BOX_STATE_EVENTHANDLER");
		Log.d("HANDLE", "Event: " + e);

		String eventtype = e.getEventtypeid();
		boolean callback = false;

		if (eventtype.equals("boxState")) {
			Device d = ddb.getDevice(e.getDeviceid());
			if (d == null) {
				Log.w("HANDLE", "Box with deviceid="+e.getDeviceid()+" not found! (boxState)");
				return;
			}

			if (d instanceof Box) {
				Box b = (Box)d;

				if (e.getState() == Event.STATE_START) {
					if (!b.isUp() && startEventMap.containsKey(e.getDeviceidI())) {
						Log.d("HANDLE", "Ignoring duplicate down event for Box");
						e.dispose();
						return;
					}
					Log.d("HANDLE", "Box going down: " + b);
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
							// Check if there is any open 'down' event for the same netboxid
							try {
								ResultSet rs = Database.query("SELECT alerthistid,deviceid FROM alerthist WHERE netboxid='"+e.getNetboxid()+"' AND end_time='infinity' AND eventtypeid='boxState'");
								if (rs.next()) {
									// Close it and mark box up
									Database.update("UPDATE alerthist SET end_time=NOW() WHERE alerthistid='"+rs.getString("alerthistid")+"'");
									Log.d("HANDLE", "Closed old down alert with different deviceid="+rs.getString("deviceid") + " for netboxid: " + e.getNetboxid());
								} else {
									Log.d("HANDLE", "Ignoring box up event as no down event was found!");
								}
							} catch (SQLException exp) {
								Log.w("BOX_STATE_EVENTHANDLER", "SQLException when checking for open down event in alerthist, netboxid " + e.getNetboxid());
							}
							e.dispose();
						} else {
							// For now ignore transient events
							startEventMap.remove(e.getDeviceidI());
							se.dispose();
							e.dispose();
							Log.d("HANDLE", "Ignoring transient boxState");
						}
					} else {
						Log.d("HANDLE", "Box going up");

						// Post alert
						a = ddb.alertFactory(e, "boxUp");
						if (b.getStatus() == Box.STATUS_SHADOW) {
							a.setAlerttype("boxSunny");
							a.setSeverity(Math.max(e.getSeverity()-SHADOW_SEVERITY_DEDUCTION,0));
						}
						a.addEvent(e);

						if (b.onMaintenance()) {
							// Do not post to alertq if box is on maintenace
							Log.d("HANDLE", "Not posting alert to alertq as the box is on maintenance");
							a.setPostAlertq(false);
						}

						try {
							ddb.postAlert(a);
							sentAlertSet.remove(e.getDeviceidI());
						} catch (PostAlertException exp) {
							Log.w("HANDLE", "PostAlertException: " + exp.getMessage());
						}
						
						// Clean up
						startEventMap.remove(e.getDeviceidI());
					}
					b.up();
				}
			}
		} else if (eventtype.equals("moduleState") || eventtype.equals("linkState")) {
			// Get parent netbox
			int parentDeviceid = Box.boxidToDeviceid(e.getNetboxid());
			Device d = ddb.getDevice(parentDeviceid);
			if (d instanceof Netel) {
				if (!d.isUp()) {
					// Ignore event since box itself is down
					Log.d("HANDLE", "Box " + d + " is down, ignoring " + eventtype + " ("+e.getDeviceid()+")");
					e.dispose();
					return;
				}

				Netel parent = (Netel)d;
				Module m = parent.getModule(e.getDeviceid());
				if (m == null) {
					Log.d("HANDLE", "Module " + e.getDeviceid() + " not found on box " + d);
					ddb.updateFromDB();
					m = parent.getModule(e.getDeviceid());
					if (m == null) {
						Log.d("HANDLE", "Module " + e.getDeviceid() + " not found on box after updateFromDB " + d);
						System.err.println("Module " + e.getDeviceid() + " not found on box after updateFromDB" + d);
						e.dispose();
						return;
					}
				}
				if (eventtype.equals("linkState")) {
					Port p = m.getPort(Integer.parseInt(e.getSubid()));
					if (p == null) {
						Log.d("HANDLE", "Port ifindex="+e.getSubid()+" in module="+m.getModule()+" not found!");
						return;
					}
					if (e.getState() == Event.STATE_START) p.down();
					else if (e.getState() == Event.STATE_END) p.up();
					e.dispose();

					Log.d("HANDLE", "Port: " + p);
				} else {
					if (e.getState() == Event.STATE_START) {
						if (!m.isUp() && startEventMap.containsKey("m"+e.getDeviceidI())) {
							Log.d("HANDLE", "Ignoring duplicate down event for Module");
							e.dispose();
							return;
						}
						Log.d("HANDLE", "Module going down (" + m.getDeviceid()+")");
						m.down();
						startEventMap.put("m"+e.getDeviceidI(), e);
						callback = true;
					} else if (e.getState() == Event.STATE_END) {
						// Get the down alert
						Alert a = ddb.getDownAlert(e);
						if (a == null) {
							// The down event could be in the startEventMap queue
							Event se = (Event)startEventMap.get("m"+e.getDeviceidI());
							if (se == null) {
								Log.d("HANDLE", "Ignoring module up event as no down event was found!");
								e.dispose();
								return;
							}
							// For now ignore transient events
							startEventMap.remove("m"+e.getDeviceidI());
							se.dispose();
							e.dispose();
							Log.d("HANDLE", "Ignoring transient moduleState");
						} else {
							Log.d("HANDLE", "Module going up");

							// Post alert
							a = ddb.alertFactory(e, "moduleUp");
							a.addEvent(e);

							if (parent != null && parent.onMaintenance()) {
								// Do not post to alertq if box is on maintenace
								a.setPostAlertq(false);
							}

							try {
								ddb.postAlert(a);
								sentAlertSet.remove("m"+e.getDeviceidI());
							} catch (PostAlertException exp) {
								Log.w("HANDLE", "PostAlertException: " + exp.getMessage());
							}

							// Clean up
							startEventMap.remove("m"+e.getDeviceidI());
						}
						m.up();
					}
					//outld("BoxState  Module: " + m);
				}
			}
		} else if (eventtype.equals("boxRestart")) {
			// Simply post on alertq
			Device d = ddb.getDevice(e.getDeviceid());
			if (d == null) {
				Log.w("HANDLE", "Box with deviceid="+e.getDeviceid()+" not found (boxRestart)!");
				e.dispose();
				return;
			}

			String alerttype = e.getVar("alerttype");
			Alert a = ddb.alertFactory(e, alerttype);
			a.addEvent(e);

			if (d instanceof Box) {
				Box b = (Box)d;
				if (b.onMaintenance()) {
					// Do not post to alertq if box is on maintenace
					a.setPostAlertq(false);
				}
			}

			Log.d("HANDLE", "Posting boxRestart ("+alerttype+") alert");
			try {
				ddb.postAlert(a);
			} catch (PostAlertException exp) {
				Log.w("HANDLE", "PostAlertException: " + exp.getMessage());
			}
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
			warningTicks = 1;

			try {
				alertTickLength = Integer.parseInt(cp.get("alertTickLength"));
			} catch (Exception exp) { }

			try {
				warningTicks = Integer.parseInt(cp.get("alertWarningTicks"));
			} catch (Exception exp) { }

			try {
				alertTicks = Integer.parseInt(cp.get("alertTicks"));
			} catch (Exception exp) { }

			Log.d("HANDLE", "Scheduling  callback, alertTickLength="+alertTickLength+" warningTicks="+warningTicks+" alertTicks="+alertTicks);
			if (warningTicks <= 0 || alertTicks <= 0) {
				callback(ddb, alertTicks);
			}
			ddb.scheduleCallback(this, alertTickLength * 1000, alertTicks);
		}

		Log.d("HANDLE", "Finished handling event, startEventMap size="+startEventMap.size() + " callback: " + ddb.isScheduledCallback(this));

	}


	private boolean sentWarning = false;
	private int warningTicks;

	public void callback(DeviceDB ddb, int invocationsRemaining)
	{
		Log.setDefaultSubsystem("BOX_STATE_EVENTHANDLER");

		int downCount = Netel.boxDownCount();
		Log.d("CALLBACK", "lastDownCount="+lastDownCount+", downCount="+downCount+", invocationsRemaining="+invocationsRemaining+ " sentWarning="+sentWarning);

		//if ( (downCount == lastDownCount && !sentWarning && warningTicks-- <= 0) || invocationsRemaining <= 0) {
		if ( (!sentWarning && --warningTicks <= 0) || invocationsRemaining <= 0) {
			
			// Just in case alertTicks = 1; in this case we don't send out warnings
			if (invocationsRemaining <= 0 && !sentWarning) sentWarning = true;

			// We are now ready to post alerts
			for (Iterator i=Netel.findBoxesDown(); i.hasNext();) {
				Box b = (Box)i.next();
				if (sentAlertSet.contains(b.getDeviceidI())) continue;

				if (!b.isUp()) {
					Log.d("CALLBACK", "Box down: " + b.getSysname());

					// The box iself is down, this means we don't report modules down if any
					// Find the down event
					Event e = (Event)startEventMap.get(b.getDeviceidI());
					if (e == null) {
						Log.w("CALLBACK", "Box " + b.getSysname() + " is down, but no start event found!");
						continue;
					}
					//if (sentWarning) startEventMap.remove(b.getDeviceidI());

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
						a.setSeverity(Math.max(e.getSeverity()-SHADOW_SEVERITY_DEDUCTION,0));
					} else if (b.getStatus() == Box.STATUS_DOWN) {
						alerttype = "boxDown";
					}

					// Update varMap from database
					try {
						ResultSet rs = Database.query("SELECT * FROM module WHERE deviceid = " + e.getDeviceid());
						ResultSetMetaData rsmd = rs.getMetaData();
						if (rs.next()) {
							HashMap hm = Database.getHashFromResultSet(rs, rsmd);
							a.addVars(hm);
						}
					} catch (SQLException exp) {
						Log.w("BOX_STATE_EVENTHANDLER", "SQLException when fetching data from module("+e.getDeviceid()+"): " + exp.getMessage());
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

					if (b.onMaintenance()) {
						// Do not post to alertq if box is on maintenace
						Log.d("HANDLE", "Not posting " + alerttype + " alert to alertq as the box is on maintenance");
						a.setPostAlertq(false);
					}

					// Post the alert
					try {
						ddb.postAlert(a);
						if (sentWarning) sentAlertSet.add(e.getDeviceidI());
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
							if (sentAlertSet.contains("m"+m.getDeviceidI())) continue;

							Log.d("CALLBACK", "Module down on: " + b.getSysname() + ", " + m.getModule());
							
							// Find the down event
							Event e = (Event)startEventMap.get("m"+m.getDeviceidI());
							if (e == null) {
								Log.w("BOX_STATE_EVENTHANDLER", "CALLBACK", m + " ("+m.getDeviceid()+") is down, but no start event found! " + startEventMap.keySet());
								continue;
							}
							//if (sentWarning) startEventMap.remove(m.getDeviceidI());
							
							// Create alert
							Alert a = ddb.alertFactory(e);

							// First send a warning
							String alerttype = "moduleDown";
							if (!sentWarning) {
								a.setState(Event.STATE_NONE);
								alerttype += "Warning";
							} else {
								// Delete 'down' event when alert is posted
								a.addEvent(e);
							}
							a.setAlerttype(alerttype);

							Log.d("BOX_STATE_EVENTHANDLER", "CALLBACK", "Added moduleDown alert: " + a);

							if (b.onMaintenance()) {
								// Do not post to alertq if box is on maintenace
								Log.d("HANDLE", "Not posting moduleDown alert to alertq as the box is on maintenance");
								a.setPostAlertq(false);
							}
							
							// Post the alert
							try {
								ddb.postAlert(a);
								if (sentWarning) sentAlertSet.add("m"+m.getDeviceidI());
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
