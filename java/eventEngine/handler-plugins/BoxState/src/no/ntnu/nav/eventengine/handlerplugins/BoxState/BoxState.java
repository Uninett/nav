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
	public static final int SHADOW_SEVERITY_DEDUCTION = 20;

	public String[] handleEventTypes()
	{
		// FIXME: Temporarily disabled handling of linkState events, as it is broken
		// The INFO plugin will dispatch the alerts, but no update of the swport table is done.
		return new String[] { "boxState", "moduleState", "boxRestart" };
	}

	public void handle(DeviceDB ddb, Event e, ConfigParser cp)
	{
		Log.setDefaultSubsystem("BOX_STATE_EVENTHANDLER");
		Log.d("HANDLE", "Event: " + e);

		setWaitTimes(cp);
		
		String eventtype = e.getEventtypeid();

		if (eventtype.equals("boxState")) {
			if (!handleBoxState(ddb, e, eventtype)) return;
		} else if (eventtype.equals("moduleState") || eventtype.equals("linkState")) {
			if (!handleModuleState(ddb, e, eventtype)) return;
		} else if (eventtype.equals("boxRestart")) {
			handleBoxRestart(ddb, e);
			return;
		}

		checkScheduleCallback(ddb);

		Log.d("HANDLE", "Finished handling event, queue size="+deviceQ.size() + " callback: " + ddb.isScheduledCallback(this));

	}

	private void setWaitTimes(ConfigParser cp) {
		warningWaitTime = 60;
		alertWaitTime = 240;		
		try {
			warningWaitTime = Integer.parseInt(cp.get("warningWaitTime"));
		} catch (Exception exp) { }
		try {
			alertWaitTime = Integer.parseInt(cp.get("alertWaitTime"));
		} catch (Exception exp) { }

		moduleWarningWaitTime = 60;
		moduleAlertWaitTime = 240;		
		try {
			moduleWarningWaitTime = Integer.parseInt(cp.get("moduleWarningWaitTime"));
		} catch (Exception exp) { }
		try {
			moduleAlertWaitTime = Integer.parseInt(cp.get("moduleAlertWaitTime"));
		} catch (Exception exp) { }
	}

	private void handleBoxRestart(DeviceDB ddb, Event e) {
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

	private boolean handleModuleState(DeviceDB ddb, Event e, String eventtype) {
		// Get parent netbox
		int parentDeviceid = Box.boxidToDeviceid(e.getNetboxid());
		Device d = ddb.getDevice(parentDeviceid);
		if (d instanceof Netel) {
			if (!d.isUp()) {
				// Ignore event since box itself is down
				Log.d("HANDLE", "Box " + d + " is down, ignoring " + eventtype + " ("+e.getDeviceid()+")");
				e.dispose();
				return false;
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
					return false;
				}
			}
			if (eventtype.equals("linkState")) {
				Port p = m.getPort(Integer.parseInt(e.getSubid()));
				if (p == null) {
					Log.d("HANDLE", "Port ifindex="+e.getSubid()+" in module="+m.getModule()+" not found!");
					return false;
				}
				if (e.getState() == Event.STATE_START) p.down();
				else if (e.getState() == Event.STATE_END) p.up();
				e.dispose();

				Log.d("HANDLE", "Port: " + p);
			} else {
				if (e.getState() == Event.STATE_START) {
					if (!m.isUp() && isInQ(m, eventtype)) {
						Log.d("HANDLE", "Ignoring duplicate down event for Module");
						e.dispose();
						return false;
					}
					Log.d("HANDLE", "Module going down (" + m.getDeviceid()+")");
					m.down();
					addToQ(m, eventtype, moduleWarningWaitTime, moduleAlertWaitTime - moduleWarningWaitTime, e);
				} else if (e.getState() == Event.STATE_END) {
					// Get the down alert
					Alert a = ddb.getDownAlert(e);
					if (a == null) {
						// The down event could be in the queue
						SendAlertDescr sad = removeFromQ(m, eventtype);
						if (sad == null) {
							Log.d("HANDLE", "Ignoring module up event as no down event was found!");
							e.dispose();
							return false;
						}
						// For now ignore transient events
						sad.event.dispose();
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
						} catch (PostAlertException exp) {
							Log.w("HANDLE", "PostAlertException: " + exp.getMessage());
						}

						// Clean up
						removeFromQ(m, eventtype);
					}
					m.up();
				}
			}
		}
		return true;
	}

	private boolean handleBoxState(DeviceDB ddb, Event e, String eventtype) {
		Device d = ddb.getDevice(e.getDeviceid());
		if (d == null) {
			Log.w("HANDLE", "Box with deviceid="+e.getDeviceid()+" not found! (boxState)");
			return false;
		}

		if (d instanceof Box) {
			Box b = (Box)d;

			if (e.getState() == Event.STATE_START) {
				if (!b.isUp() && isInQ(b, eventtype)) {
					Log.d("HANDLE", "Ignoring duplicate down event for Box");
					e.dispose();
					return false;
				}
				Log.d("HANDLE", "Box going down: " + b);
				b.down();
				addToQ(b, eventtype, warningWaitTime, alertWaitTime - warningWaitTime, e);

			} else if (e.getState() == Event.STATE_END) {
				// Get the down alert
				Alert a = ddb.getDownAlert(e);

				// Check if the deviceid has changed
				if (a == null && !isInQ(b, eventtype)) {
					try {
						ResultSet rs = Database.query("SELECT alerthistid,deviceid FROM alerthist WHERE netboxid='"+e.getNetboxid()+"' AND end_time='infinity' AND eventtypeid='boxState'");
						if (rs.next()) {
							Alert oldevent = (Alert)e;
							oldevent.setDeviceid(rs.getInt("deviceid"));
							a = ddb.getDownAlert(e);

							// Close it and mark box up
							//Database.update("UPDATE alerthist SET end_time=NOW() WHERE alerthistid='"+rs.getString("alerthistid")+"'");
							Log.d("HANDLE", "Deviceid changed for end event, deviceid="+rs.getString("deviceid") + " for netboxid: " + e.getNetboxid());
						} else {
							Log.d("HANDLE", "Ignoring box up event as no down event was found!");
						}
					} catch (SQLException exp) {
						Log.w("BOX_STATE_EVENTHANDLER", "SQLException when checking for open down event in alerthist, netboxid " + e.getNetboxid());
					}
				}

				if (a == null) {
					// The down event could be in the queue
					SendAlertDescr sad = removeFromQ(b, eventtype);
					if (sad == null) {
						// No down alert, but we mark the box up just in case
						e.dispose();
						Log.d("HANDLE", "No down event found, disposing up event");
					} else {
						// For now ignore transient events
						sad.event.dispose();
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
					} catch (PostAlertException exp) {
						Log.w("HANDLE", "PostAlertException: " + exp.getMessage());
					}

					// Clean up
					removeFromQ(b, eventtype);
				}
				b.up();
			}
		}
		return true;
	}

	private void checkScheduleCallback(DeviceDB ddb) {
 		if (!isEmptyQ()) {
			long wait = waitTimeQ();
			if (wait <= 0) wait = 1;
			Log.d("HANDLE", "Scheduling callback in " + wait + " ms ("+ (wait/1000)+" s)");
			ddb.scheduleCallback(this, wait, 1);
		} else {
			ddb.cancelCallback(this);
		}
	}


	public void callback(DeviceDB ddb, int invocationsRemaining) {
		Log.setDefaultSubsystem("BOX_STATE_EVENTHANDLER");

		if (isEmptyQ()) return;

		SendAlertDescr sad;
		int processCnt = 0;
		while ((sad = removeHeadQ()) != null) {
			Box b = null;
			if (sad.device instanceof Box) {
				b = (Box) sad.device;						
			}

			if (b != null && !b.isUp()) {
				Log.d("CALLBACK", "Box down: " + b.getSysname());

				// The box iself is down, this means we don't report modules down if any
				// Find the down event
				Event e = sad.event;
				if (e == null) {
					Log.w("CALLBACK", "Box " + b.getSysname() + " is down, but no start event found!");
					continue;
				}

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
				if (!sad.sentWarning) {
					a.setState(Event.STATE_NONE);
					alerttype += "Warning";

					// Schedule the real down event
					sad.sentWarning = true;
					addToQ(sad, sad.alertWait);
				
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
				} catch (PostAlertException exp) {
					Log.w("BOX_STATE_EVENTHANDLER", "CALLBACK", "While posting netel down alert, PostAlertException: " + exp.getMessage());
				}
			} else {
				if (sad.device instanceof Module) {
					Module m = (Module)sad.device;
					b = (Box) m.getParent();
					if (!b.isUp()) {
						// Ignore moduleDown when box is down
						Log.d("CALLBACK", "Ignoring module down (" + m.getModule() + "), as the box is down (" + b.getSysname() +")");
						continue;
					} else {
						Log.d("CALLBACK", "Module down on: " + b.getSysname() + ", " + m.getModule());
					}
					
					// Find the down event
					Event e = sad.event;
					if (e == null) {
						Log.w("BOX_STATE_EVENTHANDLER", "CALLBACK", m + " ("+m.getDeviceid()+") is down, but no start event found!");
						continue;
					}
						
					// Create alert
					Alert a = ddb.alertFactory(e);

					// First send a warning
					String alerttype = "moduleDown";
					if (!sad.sentWarning) {
						a.setState(Event.STATE_NONE);
						alerttype += "Warning";

						// Schedule the real down event
						sad.sentWarning = true;
						addToQ(sad, sad.alertWait);
					} else {
						// Delete 'down' event when alert is posted
						a.addEvent(e);
					}
					a.setAlerttype(alerttype);

					Log.d("BOX_STATE_EVENTHANDLER", "CALLBACK", "Added moduleDown alert: " + a);

					if (b.onMaintenance()) {
						// Do not post to alertq if box is on maintenace, only register in alerthist
						Log.d("HANDLE", "Not posting moduleDown alert to alertq as the box is on maintenance");
						a.setPostAlertq(false);
					}
						
					// Post the alert
					try {
						ddb.postAlert(a);
					} catch (PostAlertException exp) {
						Log.w("BOX_STATE_EVENTHANDLER", "CALLBACK", "While posting module down alert, PostAlertException: " + exp.getMessage());
					}
				}
			}
			processCnt++;
		}
		checkScheduleCallback(ddb);
		Log.d("BOX_STATE_EVENTHANDLER", "CALLBACK", "Alert processing done, processed " + processCnt + ", queue size " + deviceQ.size());
	}

	// Queue handling code
	private SortedMap deviceQ = new TreeMap();
	private Map qMap = new HashMap();
	private int warningWaitTime;
	private int alertWaitTime;
	private int moduleWarningWaitTime;
	private int moduleAlertWaitTime;

	private class SendAlertDescr {
		public Device device;
		public String eventtype;
		public boolean sentWarning;
		public long alertWait;
		public Event event;

		public SendAlertDescr(Device d, String type) {
			this(d, type, 0, null);
		}

		public SendAlertDescr(Device d, String type, long wait, Event e) {
			device = d;
			eventtype = type;
			sentWarning = false;
			alertWait = wait;
			event = e;
		}

		public boolean equals(Object o) {
			if (o instanceof SendAlertDescr) {
				SendAlertDescr sad = (SendAlertDescr)o;
				return device.getDeviceid() == sad.device.getDeviceid() && eventtype.equals(sad.eventtype);
			}
			return false;
		}

		public String toString() {
			return "Dev: " + device.getDeviceid() + " type: " + eventtype + " w: " + sentWarning + " alertWait: " + alertWait;
		}
	}

	private boolean isEmptyQ() {
		return deviceQ.isEmpty();
	}
	private long waitTimeQ() {
		if (deviceQ.isEmpty()) return Long.MAX_VALUE;

		Long t = (Long) deviceQ.firstKey();
		return t.longValue() - System.currentTimeMillis();
	}
	private void addToQ(SendAlertDescr sad, long time) {
		List l;
		Long t = new Long(System.currentTimeMillis() + time * 1000);
		if ( (l=(List)deviceQ.get(t)) == null) deviceQ.put(t, l = new ArrayList());
		l.add(sad);
		qMap.put(sad.device.getDeviceidI()+":"+sad.eventtype, t);
	}
	private SendAlertDescr removeFromQ(Device d, String eventtype) {
		Long t = (Long) qMap.remove(d.getDeviceidI()+":"+eventtype);
		if (t == null) return null;
		List l = (List) deviceQ.get(t);
		int idx = l.indexOf(new SendAlertDescr(d, eventtype));
		SendAlertDescr sad = (SendAlertDescr) l.get(idx);
		l.remove(idx);
		if (l.isEmpty()) deviceQ.remove(t);
		return sad;
	}

	private SendAlertDescr removeHeadQ() {
		if (deviceQ.isEmpty()) return null;

		Long t = (Long) deviceQ.firstKey();
		if (t.longValue() > System.currentTimeMillis()) return null;
		List l = (List) deviceQ.get(t);		
		SendAlertDescr sad = (SendAlertDescr) l.remove(l.size()-1);
		if (l.isEmpty()) deviceQ.remove(t);
		qMap.remove(sad.device.getDeviceidI()+":"+sad.eventtype);
		return sad;
	}
	private void addToQ(Device d, String eventtype, long warningTime, long alertTime, Event e) {
		addToQ(new SendAlertDescr(d, eventtype, alertTime, e), warningTime);
	}
		
	private boolean isInQ(Device device, String eventtype) {
		return qMap.containsKey(device.getDeviceidI() + ":" + eventtype);
	}

}
