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
		return new String[] { "boxState", "moduleState", "linkState", "boxRestart", "snmpAgentState" };
	}

	public void handle(DeviceDB ddb, Event e, ConfigParser cp)
	{
		Log.setDefaultSubsystem("BOX_STATE_EVENTHANDLER");
		Log.d("HANDLE", "Event: " + e);

		setWaitTimes(cp);

		String eventtype = e.getEventtypeid();

		if (eventtype.equals("boxState")) {
			if (!handleBoxState(ddb, e, eventtype)) return;
		} else if (eventtype.equals("snmpAgentState")) {
			if (!handleSnmpAgentState(ddb, e, eventtype)) return;
		} else if (eventtype.equals("moduleState")) {
			if (!handleModuleState(ddb, e, eventtype)) return;
		} else if (eventtype.equals("linkState")) {
			if (!handleLinkState(ddb, e, eventtype)) return;
		} else if (eventtype.equals("boxRestart")) {
			handleBoxRestart(ddb, e);
			return;
		}

		checkScheduleCallback(ddb);

		Log.d("HANDLE", "Finished handling event, queue size="+deviceQ.size() + " callback: " + ddb.isScheduledCallback(this));

	}

	private void setWaitTimes(ConfigParser cp) {
		warningWaitTime = getConfigInt(cp, "warningWaitTime", 60);
		alertWaitTime = getConfigInt(cp, "alertWaitTime", 240);
		moduleWarningWaitTime = getConfigInt(cp, "moduleWarningWaitTime", 60);
		moduleAlertWaitTime = getConfigInt(cp, "moduleAlertWaitTime", 240);
		linkAlertWaitTime = getConfigInt(cp, "linkAlertWaitTime", 60);
		snmpAlertWaitTime = getConfigInt(cp, "snmpAlertWaitTime", 240);
	}

	private int getConfigInt(ConfigParser cp, String key, int defaultValue) {
		try {
			return Integer.parseInt(cp.get(key));
		} catch (Exception exp) {
			return defaultValue;
		}
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
		return true;
	}

	private boolean handleLinkState(DeviceDB ddb, Event e, String eventtype) {
		int netboxDeviceId = Box.boxidToDeviceid(e.getNetboxid());
		Device device = ddb.getDevice(netboxDeviceId);
		if (device instanceof Netel) {
			Netel netbox = (Netel) device;
			if (!netbox.isUp()) {
				// Ignore event since box itself is down
				Log.d("HANDLE", "Box " + netbox.getSysname() + " is down, ignoring " + eventtype + " ("+e.getDeviceid()+")");
				e.dispose();
				return false;
			}

			int interfaceid = Integer.parseInt(e.getSubid());
			Port port = netbox.getPort(interfaceid);
			if (port == null) {
				Log.e("HANDLE", "interfaceid " + interfaceid + " referenced in linkState event not found on box " + device);
				e.dispose();
				return false;
			}

			if (e.getState() == Event.STATE_START) {
				if (!port.isUp() || isInQ(netbox, port, eventtype)) {
					Log.d("HANDLE", "Ignoring duplicate down event for link");
					e.dispose();
					return false;
				}
				Log.i("HANDLE", netbox.getSysname() + " port going down: " + port);
				port.down();
				addToQ(netbox, port, eventtype, linkAlertWaitTime, 0, e);

			}
			else if (e.getState() == Event.STATE_END) {
				Alert a = ddb.getDownAlert(e);
				if (a == null) {
					SendAlertDescr sad = removeFromQ(netbox, port, eventtype);
					if (sad != null) {
						Log.i("HANDLE", "Ignoring transient link state change");
						sad.event.dispose();
						e.dispose();
						return false;
					}
					Log.d("HANDLE", "Ignoring link up event as no down event was found!");
					e.dispose();
					return false;
				}
				Log.i("HANDLE", netbox.getSysname() + " port going up: " + port);
				port.up();
				Alert alert = ddb.alertFactory(e, "linkUp");
				alert.addEvent(e);
				alert.addVars(getPortVarMap(netbox, port));

				Log.d("HANDLE", "Posting linkState (linkUp) alert");
				try {
					ddb.postAlert(alert);
				} catch (PostAlertException exp) {
					Log.w("HANDLE", "PostAlertException: " + exp.getMessage());
				}
			}
		} else {
			Log.e("HANDLE", "no such device, ignoring event: " + netboxDeviceId);
			e.dispose();
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

	private boolean handleSnmpAgentState(DeviceDB ddb, Event e, String eventtype) {
		Device d = ddb.getDevice(e.getDeviceid());
		if (d == null) {
			Log.w("HANDLE", "Box with deviceid="+e.getDeviceid()+" not found! (snmpAgentState)");
			return false;
		}

		if (d instanceof Box) {
			Box b = (Box)d;

			if (e.getState() == Event.STATE_START) {
				if (isInQ(b, eventtype)) {
					Log.d("HANDLE", "Ignoring duplicate snmpAgentDown event for box " + b.getSysname());
					e.dispose();
					return false;
				} else if (!b.isUp()) {
					Log.d("HANDLE", "Ignoring snmpAgentDown event as box " + b.getSysname() + " is down");
					e.dispose();
					return false;
				}
				addToQ(b, eventtype, snmpAlertWaitTime, 0, e);

			} else if (e.getState() == Event.STATE_END) {
				// Get the down alert
				Alert a = ddb.getDownAlert(e);

				// Check if the deviceid has changed
				if (a == null && !isInQ(b, eventtype)) {
					try {
						ResultSet rs = Database.query("SELECT alerthistid,deviceid FROM alerthist WHERE netboxid='"+e.getNetboxid()+"' AND end_time='infinity' AND eventtypeid='snmpAgentState'");
						if (rs.next()) {
							Alert oldevent = (Alert)e;
							oldevent.setDeviceid(rs.getInt("deviceid"));
							a = ddb.getDownAlert(e);

							Log.d("HANDLE", "Deviceid changed for end event, deviceid="+rs.getString("deviceid") + " for netboxid: " + e.getNetboxid());
						} else {
							Log.d("HANDLE", "Ignoring snmpAgentUp event as no down event was found!");
						}
					} catch (SQLException exp) {
						Log.w("BOX_STATE_EVENTHANDLER", "SQLException when checking for open snmpAgentDown event in alerthist, netboxid " + e.getNetboxid());
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
						Log.d("HANDLE", "Ignoring transient snmpAgentState");
					}
				} else {
					Log.d("HANDLE", "SNMP Agent coming up");

					// Post alert
					a = ddb.alertFactory(e, "snmpAgentUp");
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
			if (b!= null && sad.port != null) {
				Log.d("CALLBACK", "Link down: " + b.getSysname() + " " + sad.port);
				Event e = sad.event;
				if (e == null) {
					Log.w("CALLBACK", "Port " + b.getSysname() + ":" + sad.port + " is down, but no start event found!");
					continue;
				}

				if (!b.isUp()) {
					// Ignore linkDown when box is down
					Log.d("CALLBACK", "Ignoring link down (" + sad.port + "), as the box is down (" + b.getSysname() +")");
					continue;
				}

				// Create alert
				Alert a = ddb.alertFactory(e);
				a.setState(Event.STATE_START);
				a.setAlerttype("linkDown");
				a.addVars(getPortVarMap(b, sad.port));

				a.addEvent(e);

				Log.d("BOX_STATE_EVENTHANDLER", "CALLBACK", "Added linkDown alert: " + a);

				if (b.onMaintenance()) {
					// Do not post to alertq if box is on maintenace, only register in alerthist
					Log.d("HANDLE", "Not posting linkDown alert to alertq as the box is on maintenance");
					a.setPostAlertq(false);
				}

				// Post the alert
				try {
					ddb.postAlert(a);
				} catch (PostAlertException exp) {
					Log.w("BOX_STATE_EVENTHANDLER", "CALLBACK", "While posting linkDown alert, PostAlertException: " + exp.getMessage());
				}

			} else if (b != null && sad.eventtype.equals("snmpAgentState")) {
				Log.d("CALLBACK", "SNMP Agent down: " + b.getSysname());
				Event e = sad.event;
				if (e == null) {
					Log.w("CALLBACK", "SNMP Agent on " + b.getSysname() + " is down, but no start event found!");
					continue;
				}

				if (b.getStatus() != Box.STATUS_UP) {
					Log.w("CALLBACK", "Box " + b.getSysname() + " isn't up, ignoring snmpAgentState event");
					e.dispose();
					continue;
				}

				// Create alert
				Alert a = ddb.alertFactory(e);
				a.addEvent(e);
				a.setAlerttype("snmpAgentDown");

				Log.d("BOX_STATE_EVENTHANDLER", "CALLBACK", "Added alert: " + a);

				if (b.onMaintenance()) {
					// Do not post to alertq if box is on maintenace
					Log.d("HANDLE", "Not posting snmpAgentDown alert to alertq as the box is on maintenance");
					a.setPostAlertq(false);
				}

				// Post the alert
				try {
					ddb.postAlert(a);
				} catch (PostAlertException exp) {
					Log.w("BOX_STATE_EVENTHANDLER", "CALLBACK", "While posting snmpAgentDown alert, PostAlertException: " + exp.getMessage());
				}
			} else if (b != null && !b.isUp()) {
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

	private HashMap getPortVarMap(Box box, Port port) {
		try {
			ResultSet rs = Database.query("SELECT * FROM interface WHERE netboxid = " + box.getBoxid() + " AND ifindex=" + port.getIfindex());
			ResultSetMetaData rsmd = rs.getMetaData();
			if (rs.next()) {
				return Database.getHashFromResultSet(rs, rsmd);
			}
		} catch (SQLException exp) {
			Log.w("BOX_STATE_EVENTHANDLER", "SQLException when fetching data from interface("+box.getBoxid() + ":" + port.getIfindex()+"): " + exp.getMessage());
		}
		return new HashMap();
	}

	// Queue handling code
	private SortedMap deviceQ = new TreeMap();
	private Map qMap = new HashMap();
	private int warningWaitTime;
	private int alertWaitTime;
	private int moduleWarningWaitTime;
	private int moduleAlertWaitTime;
	private int linkAlertWaitTime;
	private int snmpAlertWaitTime;

	private class SendAlertDescr {
		public Device device;
		public Port port;
		public String eventtype;
		public boolean sentWarning;
		public long alertWait;
		public Event event;

		public SendAlertDescr(Device d, String type) {
			this(d, type, 0, null);
		}

		public SendAlertDescr(Device d, Port p, String type) {
			this(d, p, type, 0, null);
		}

		public SendAlertDescr(Device d, String type, long wait, Event e) {
			this(d, null, type, wait, e);
		}

		public SendAlertDescr(Device d, Port p, String type, long wait, Event e) {
			device = d;
			port = p;
			eventtype = type;
			sentWarning = false;
			alertWait = wait;
			event = e;
		}

		public boolean equals(Object o) {
			if (o instanceof SendAlertDescr) {
				SendAlertDescr sad = (SendAlertDescr)o;
				boolean isSameDevice = device.getDeviceid() == sad.device.getDeviceid();
				boolean isSameEventType = eventtype.equals(sad.eventtype);
				boolean isSamePort = port == sad.port || (port != null && sad.port != null && port.getIfindex() == sad.port.getIfindex());
				return isSameDevice && isSameEventType && isSamePort;
			}
			return false;
		}

		public String toString() {
			return "Dev: " + device.getDeviceid() + " port: " + port + " type: " + eventtype + " w: " + sentWarning + " alertWait: " + alertWait;
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
		qMap.put(qKey(sad.device, sad.port, sad.eventtype), t);
	}
	private SendAlertDescr removeFromQ(Device d, String eventtype) {
		return removeFromQ(d, null, eventtype);
	}
	private SendAlertDescr removeFromQ(Device d, Port p, String eventtype) {
		Long t = (Long) qMap.remove(qKey(d, p, eventtype));
		if (t == null) return null;
		List l = (List) deviceQ.get(t);
		if (l == null) return null;
		int idx = l.indexOf(new SendAlertDescr(d, p, eventtype));
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
		qMap.remove(qKey(sad.device, sad.eventtype));
		return sad;
	}
	private void addToQ(Device d, String eventtype, long warningTime, long alertTime, Event e) {
		addToQ(d, null, eventtype, warningTime, alertTime, e);
	}
	private void addToQ(Device d, Port p, String eventtype, long warningTime, long alertTime, Event e) {
		addToQ(new SendAlertDescr(d, p, eventtype, alertTime, e), warningTime);
	}

	private boolean isInQ(Device device, String eventtype) {
		return qMap.containsKey(qKey(device, eventtype));
	}
	private boolean isInQ(Device device, Port p, String eventtype) {
		return qMap.containsKey(qKey(device, p, eventtype));
	}

	private String qKey(Device device, String eventType) {
		return qKey(device, null, eventType);
	}
	private String qKey(Device device, Port p, String eventType) {
		String portKey = p != null ? "" + p.getIfindexI() : "";
		return device.getDeviceidI() + ":" + portKey + ":" + eventType;
	}
}
