import java.io.*;
import java.util.*;
import java.util.regex.*;
import java.net.*;
import java.text.*;

import java.sql.*;

import no.ntnu.nav.logger.*;
import no.ntnu.nav.ConfigParser.*;
import no.ntnu.nav.Database.*;
import no.ntnu.nav.SimpleSnmp.*;
import no.ntnu.nav.event.*;
import no.ntnu.nav.netboxinfo.*;
import no.ntnu.nav.util.*;

/**
 * This class schedules the netboxes, assigns them to threads and runs
 * the plugins.
 */

public class DiscoveryThread extends Thread
{
	private static ConfigParser navCp;
	private static ConfigParser myCp;

	private static Timer timer;
	private static Timer updateFromARPTimer;
	private static CheckRunQTask checkRunQTask;

	private static SortedMap ipRunQ;
	private static Stack idleThreads;

	private static int maxThreadCnt;
	private static int threadCnt;
	private static Integer idleThreadLock = new Integer(0);
	private static Integer insertNetboxLock = new Integer(0);
	private static Integer updateMacLock = new Integer(0);
	private static Integer checkRouterLock = new Integer(0);
	private static Integer fileLock = new Integer(0);
	private static LinkedList threadIdList = new LinkedList();
	private static int curMaxTid = 0;

	private static int netboxCnt;
	private static int netboxHigh;
	private static long nbProcessedCnt;

	private static List csList = new ArrayList();
	private static int baseCheckInterval;
	private static int maxMacChecks;
	private static double checkMultiplier;

	private static boolean ipScanMode;
	private static LinkedList nextIpQueue = new LinkedList();

	private static Set seenMacs = Collections.synchronizedSet(new HashSet());
	private static Set macsInQueue = Collections.synchronizedSet(new HashSet());
	private static int numFound = 0;

	private static String allNetboxesBulkFile = "all-netboxes.bulk";
	private static String newNetboxesBulkFile = "new-netboxes.bulk";
	private static Set netboxesInAllFile = Collections.synchronizedSet(new HashSet());
	private static Set netboxesInNewFile = Collections.synchronizedSet(new HashSet());

	private static String DEFAULT_ROOMID = "dummy";
	private static String DEFAULT_ORGID = "dummy";
	private static String DEFAULT_LOCATIONID = "dummy";

	private static boolean autoInsertNetbox = false;


	// Object data
	String tid;
	IP ip;
	SimpleSnmp sSnmp;

	// Static init
	public static void init(int numThreads, ConfigParser _myCp, ConfigParser _navCp) {
		maxThreadCnt = numThreads;
		myCp = _myCp;
		navCp = _navCp;
		myCp.setObject("navCp", navCp);

		// Create the netbox map and the run queue
		ipRunQ = new TreeMap();

		// Read config
		String cs = myCp.get("communitys");
		String[] csA = cs.split(",");
		for (int i=0; i < csA.length; i++) {
			csList.add(csA[i].trim());
		}

		baseCheckInterval = Integer.parseInt(myCp.get("baseCheckInterval"));
		maxMacChecks = Integer.parseInt(myCp.get("maxMacChecks"));
		checkMultiplier = Double.parseDouble(myCp.get("checkMultiplier"));

		timer = new Timer();
		ipScanMode = true;

		if (myCp.get("allNetboxesBulkFile") != null) allNetboxesBulkFile = myCp.get("allNetboxesBulkFile");
		if (myCp.get("newNetboxesBulkFile") != null) newNetboxesBulkFile = myCp.get("newNetboxesBulkFile");
		if (myCp.get("autoInsertNetbox") != null) {
			try {
				autoInsertNetbox = myCp.get("autoInsertNetbox").startsWith("t");
			} catch (Exception e) {
			}
		}

		parseBulkFile(allNetboxesBulkFile, netboxesInAllFile);
		parseBulkFile(newNetboxesBulkFile, netboxesInNewFile);

		// For dupe checking
		loadSeenMacs();

		// Fill the runq from db
		fillRunQ();

		updateFromARPTimer = new Timer();
		long updateFromARPFrequency = 1800;
		try {
			updateFromARPFrequency = Integer.parseInt(myCp.get("updateFromARPFrequency"));
		} catch (Exception e) {
		}
		updateFromARPFrequency *= 1000;
		updateFromARPTimer.schedule(new UpdateFromARPTask(), updateFromARPFrequency, updateFromARPFrequency);

		Log.d("INIT", "Starting timer for IP query scheduling");
		scheduleCheckRunQ(0);

	}

	private static void loadSeenMacs() {
		try {
			ResultSet rs = Database.query("SELECT mac FROM autodisc_mac_scanned WHERE attempts IS NULL");
			while (rs.next()) {
				seenMacs.add(rs.getString("mac"));
			}
		} catch (SQLException e) {
			e.printStackTrace(System.err);
		}
	}

	private static void updateFromARP() {
		if (true) return;
		try {
			// All macs we haven't tried before
			ResultSet rs = Database.query("SELECT DISTINCT ip, mac FROM arp WHERE end_time='infinity' AND mac NOT IN (SELECT mac FROM autodisc_mac_scanned)");
			while (rs.next()) {
				IP ip = new IP(rs.getString("ip"), rs.getString("mac"));
				addToRunQ(ip);
			}
		} catch (SQLException e) {
			e.printStackTrace(System.err);
		}
	}

	private static void fillRunQ() {
		updateFromARP();

		try {
			// All macs we haven't given up on
			ResultSet rs = Database.query("SELECT ip, autodisc_mac_scanned.mac, time, attempts FROM autodisc_mac_scanned JOIN arp ON (autodisc_mac_scanned.mac = arp.mac AND arp.end_time='infinity') WHERE attempts < " + maxMacChecks);
			while (rs.next()) {
				IP ip = new IP(rs.getString("ip"), rs.getString("mac"), rs.getLong("time"), rs.getInt("attempts"));
				addToRunQ(ip);
			}
		} catch (SQLException e) {
			e.printStackTrace(System.err);
		}
	}

	private static void parseBulkFile(String fn, Set nbIpSet) {
		try {
			char sep = File.separatorChar;
			File f = new File(navCp.get("NAVROOT") + sep + "var" + sep + "log" + sep + fn);
			if (!f.exists()) return;

			BufferedReader in = new BufferedReader(new FileReader(f));
			String s;
			while ( (s=in.readLine()) != null) {
				String[] g = s.split(":");
				if (g.length >= 2) {
					nbIpSet.add(g[1]);
				}
			}
		} catch (Exception e) {
			e.printStackTrace(System.err);
		}
	}

	private void writeBulkFile(String fn, String ip, String catid, String ro, String dns, String sysname, String sysobjectid, String sysdescr) {
		synchronized (fileLock) {
			try {
				char sep = File.separatorChar;
				File f = new File(navCp.get("NAVROOT") + sep + "var" + sep + "log" + sep + fn);
				PrintStream out = new PrintStream(new FileOutputStream(f, true), true);
		
				// # dnsnavn, sysobjectid, system.sysdescr (avkappet om den er lang)
				String descr = "# " + dns + " ("+sysname+", " + ro + "), " + sysobjectid  + ", " + sysdescr.substring(0, Math.min(70, sysdescr.length()));
				out.println(descr);

				// #roomid:ip:orgid:catid:[ro:serial:rw:function:subcat1:subcat2..]
				String s = DEFAULT_ROOMID + ":" + ip + ":" + DEFAULT_ORGID + ":" + catid + ":" + ro;
				out.println(s);
				out.close();
			} catch (Exception e) {
				e.printStackTrace(System.err);
			}
		}
	}

	private static IP getNextIp() {
		synchronized (nextIpQueue) {
			if (nextIpQueue.isEmpty()) {
				// Init local IPs
				try {
					Enumeration e = NetworkInterface.getNetworkInterfaces();
					while(e.hasMoreElements()) {
						NetworkInterface netface = (NetworkInterface)e.nextElement();
						Enumeration e2 = netface.getInetAddresses();
						while (e2.hasMoreElements()){
							InetAddress ip = (InetAddress) e2.nextElement();
							if (ip instanceof Inet4Address && !ip.isLoopbackAddress()) {
								long ipnum = ipToNum(ip.getHostAddress());
								ipnum = ipToNum("129.241.190.1");
								nextIpQueue.add(new String[] { numToIp(ipnum), "u" } );
								nextIpQueue.add(new String[] { numToIp(ipnum-1), "d" } );
							}
						}
					}
				} catch (SocketException e) {
					e.printStackTrace(System.err);
				}
				if (nextIpQueue.isEmpty()) return null;
			}

			// Fetch next IP from queue
			String[] s = (String[])nextIpQueue.removeFirst();
			String ipaddr = s[0];
			long ipnum = ipToNum(ipaddr);
			if (s[1].equals("u")) ipnum++;
			else ipnum--;
			nextIpQueue.add(new String[] { numToIp(ipnum), s[1] } );

			return new IP(ipaddr, null);				
		}
	}

	private static void scheduleCheckRunQ(long l)
	{
		synchronized (timer) {
			if (checkRunQTask != null) checkRunQTask.cancel();
			checkRunQTask = new CheckRunQTask();

			// The delay can actually be negative due to inaccuracy in the Java timer
			l = Math.max(l, 0);
			Log.d("QUERY_NETBOX", "SCHEDULE_CHECK_RUN_Q", "Schedule check runq in " + l + " ms");
			try {
				timer.schedule(checkRunQTask, l);
			} catch (IllegalStateException e) {
				timer = new Timer();
				checkRunQTask = new CheckRunQTask();
				timer.schedule(checkRunQTask, l);
			}
		}
	}

	private static void checkRunQ()
	{
		Log.setDefaultSubsystem("QUERY_IP");

		// Try to get a free IP to check
		Object o;
		while ((o = removeRunQHead()) instanceof IP) {
			IP ip = (IP)o;

			Log.d("CHECK_RUN_Q", "Got ip: " + ip);

			// Try to get a free thread
			String tid = requestThread();
			if (tid == null) {
				Log.d("CHECK_RUN_Q", "IP is available, but no threads are idle");
				// Re-insert into queue
				addToRunQFront(ip);
				return;
			}

			// OK, start a new thread
			Log.d("CHECK_RUN_Q", "Starting new IP thread with id: " + tid + " to handle " + ip);
			new DiscoveryThread(tid, ip).start();
		} 

		// No more IPs, schedule re-run when the next is ready
		Long nextRun = (Long)o;
		Log.d("CHECK_RUN_Q", "No available IP, scheduling next check in " + nextRun + " ms (" + (nextRun.longValue()/1000) + " s)");
		scheduleCheckRunQ(nextRun.longValue());

	}

	private static void addToRunQ(IP ip) {
		addToRunQ(ip, false);
	}

	private static void addToRunQFront(IP ip) {
		addToRunQ(ip, true);
	}

	private static void addToRunQ(IP ip, boolean front) {
		Long nextRun = new Long(ip.getNextRun());
		synchronized (ipRunQ) {
			if (ip.getMac() != null) {
				// MAC should only be in queue once
				if (macsInQueue.contains(ip.getMac())) return;
			}
 			LinkedList l;
			if ( (l = (LinkedList)ipRunQ.get(nextRun)) == null) ipRunQ.put(nextRun, l = new LinkedList());
			if (front) {
				l.addFirst(ip);
			} else {
				l.add(ip);
			}
		}
		if (ip.getMac() != null) {
			seenMacs.add(ip.getMac());
		}
	}

	private static Object removeRunQHead() {
		Object o;
		if ((o = removeRunQHeadNoCheck()) instanceof IP) {
			IP ip = (IP)o;
			return ip;
		}
		return o;
	}

	private static int ipRunQSize() {
		synchronized (ipRunQ) {
			return ipRunQ.size();
		}
	}

	private static Object removeRunQHeadNoCheck() {
		synchronized (ipRunQ) {
			if (ipRunQ.isEmpty()) {
				if (ipScanMode) {
					return getNextIp();
				}
				return new Long(Long.MAX_VALUE / 2); // Infinity...
			}
			Long nextRun = (Long)ipRunQ.firstKey();
			if (nextRun.longValue() > System.currentTimeMillis()) {
				// Head of queue is not yet ready to be run
				return new Long(nextRun.longValue() - System.currentTimeMillis());
			}

			LinkedList l = (LinkedList)ipRunQ.get(nextRun);
			IP ip  = (IP)l.removeFirst();
			if (ip.getMac() != null) {
				macsInQueue.remove(ip.getMac());
			}
			if (l.isEmpty()) ipRunQ.remove(nextRun);
			return ip;
		}
	}

	private static long ipToNum(String ip) {
		if (ip.length() == 0) return 0;
		String[] s = ip.split("\\.");
		long l = 0;
		long mul = 1;
		for (int i=0; i < s.length-1; i++) mul *= 255;
		for (int i=0; i < s.length; i++) {
			l += Integer.parseInt(s[i]) * mul;
			mul /= 255;
		}
		return l;
	}
	private static String numToIp(long num) {
		if (num == 0) return "";
		String s = "";
		long mul = 1;
		int dig=0;
		while (mul < num) mul *= 255;
		while (num > 0) {
			long l = num / mul;
			if (num == l*mul && dig < 3) l--; // IPs must be 4 digits
			if (l > 0) {
				s += l + ".";
				dig++;
			}
			num -= l * mul;
			mul /= 255;
		}
		return s.substring(0, s.length()-1);
	}

	private static String requestThread() {
		synchronized (idleThreadLock) {
			if (threadCnt < maxThreadCnt) {
				int tid = getFreeTid();
				threadCnt++;
				//System.err.println("New thread, cnt="+(threadCnt+1)+" max="+max);
				return format(tid, String.valueOf(maxThreadCnt-1).length());
			}
			return null;
		}
	}

	private static void incNumFound() {
		synchronized (idleThreadLock) {
			numFound++;
		}
	}

	private static void threadIdle(String tid) {
		synchronized (idleThreadLock) {
			returnTid(Integer.parseInt(tid));
			//System.err.println("Del thread, cnt="+(threadCnt-1));
			threadCnt--;
		}
		scheduleCheckRunQ(0);
	}

	private static int getFreeTid() {
		if (threadIdList.isEmpty()) {
			threadIdList.add(new Integer(curMaxTid++));
		}
		return ((Integer)threadIdList.removeFirst()).intValue();
	}

	private static void returnTid(int tid) {
		threadIdList.add(new Integer(tid));
	}

	// Constructor
	public DiscoveryThread(String tid, IP ip)
	{
		this.tid = tid;
		this.ip = ip;
	}

	public boolean runningSNMP(String host) {
		try {
			//Log.d("RUNNING_SNMP", "Checking " + host + " for open SNMP port");
			InetAddress inet = InetAddress.getByName(host);
			DatagramSocket s = new DatagramSocket();
			s.setSoTimeout(100);
			try {
				s.connect(inet, 161);
				DatagramPacket p = new DatagramPacket(new byte[0], 0);
				s.send(p);
				s.receive(p);
			} catch (SocketTimeoutException e) {
				return true;
			} finally {
				s.close();
			}
		} catch (Exception e) {
			// We get java.net.PortUnreachableException: ICMP Port Unreachable if no SNMP is running
		}
		return false;
	}

	public String accessSNMP() {
		sSnmp.setSocketTimeout(100);
		for (Iterator it = csList.iterator(); it.hasNext();) {
			String cs = (String) it.next();
			sSnmp.setCs_ro(cs);
			//Log.d("ACCESS_SNMP", "Trying SNMP with cs " + cs);
			try {
				sSnmp.setTimeoutLimit(1);
				sSnmp.getNext("1", 1, false, true);

				// Ok!
				return cs;
			} catch (Exception e) {
			}
		}
		return null;
	}

	public void run()
	{
		Log.setDefaultSubsystem("QUERY_NETBOX_T"+tid);
		Log.setThreadId(tid);

		Log.d("RUN", "Thread " + tid + " starting work on ("+ip+")");

		long beginTime = System.currentTimeMillis();

		try {
			while (true) {
				String host = ip.getIp();
				Log.setNetbox(ip.getIp());

				sSnmp = SimpleSnmp.simpleSnmpFactory();
				sSnmp.setHost(ip.getIp());
				Log.d("RUN", "Testing ("+ip.getIp()+"): " + ip.getMac() + " (IPs in queue: " + ipRunQSize() + " Num found: " + numFound + ")");

				long boksBeginTime = System.currentTimeMillis();

				boolean accessible = false;
				if (runningSNMP(ip.getIp())) {
					//Log.d("RUN", "Host " + host + " has an open SNMP port");
					String cs = accessSNMP();
					if (cs != null) {
						accessible = true;
						boolean foundArp = collectARP(cs);
						boolean isGw = false;
						if (foundArp) {
							String[] newHost = new String[1];
							isGw = checkRouter(host, newHost);
							if (isGw) host = newHost[0];
						}
						Log.d("RUN", "Found new netbox: " + host + " (cs " + cs + "), gw: " + isGw);
						insertNetbox(host, cs, isGw);
						if (isGw && ipScanMode) {
							Log.d("RUN", "Disabled IP scanning mode");
							ipScanMode = false;
						}
					}
				} else {
					//Log.d("RUN", "Host " + host + " does not have an open SNMP port");
				}

				if (ip.getMac() != null) {
					if (ip.getAttempts() >= DiscoveryThread.maxMacChecks) {
						accessible = true; // Give up
						Log.d("RUN", "Giving up on host: " + ip);
					}
					updateMacDb(ip, accessible);

					if (!accessible) {
						// Insert into queue
						long nextr = ip.getNextRun() - System.currentTimeMillis();
						Log.d("RUN", "Schedule host " + ip + " to be retested in: " + nextr + " ms (" + (nextr/1000) + " s)");
						if (nextr < 0) {
							Log.d("RUN", "Neg " + nextr + ", " + ip + ", " + System.currentTimeMillis() + ", " + ip.getTime() + ", " + ip.getAttempts());
							System.err.println("Neg " + nextr + ", " + ip + ", " + System.currentTimeMillis() + ", " + ip.getTime() + ", " + ip.getAttempts());
						}
						addToRunQ(ip);
					}
				}


				Log.setNetbox(null);

				// Try to get a new IP to process
				Object o = removeRunQHead();
				if (o instanceof IP) {
					ip = (IP)o;
					//Log.d("RUN", "Got new IP: " + ip);
				} else {
					// We didn't get a netbox; exit the thread
					//Log.d("RUN", "No new IP available: " + o);
					break;
				}
			}

		} catch (Throwable e) {
			Log.e("RUN", "Caught exception, should not happen: " + e.getMessage());
			e.printStackTrace(System.err);
		} finally {
			Log.d("RUN", "Thread idle, exiting...");
			if (sSnmp != null) sSnmp.destroy();
			sSnmp = null;
			System.gc();
			Log.freeThread();
			threadIdle(tid);
		}
	}

	private String[] getNetboxInfo() {
		sSnmp.setSocketTimeout(500);

		List l;
		String sysname = "(null)";
		try {
			l = sSnmp.getAll("1.3.6.1.2.1.1.5.0", true, false);
			if (l != null && !l.isEmpty()) sysname = ((String[])l.get(0))[1];
		} catch (TimeoutException te) { }

		String sysobjectid = "(null)";
		try {
			l = sSnmp.getAll("1.3.6.1.2.1.1.2.0", false, false);
			if (l != null && !l.isEmpty()) sysobjectid = ((String[])l.get(0))[1];
		} catch (TimeoutException te) { }

		String sysdescr = "(null)";
		try {
			l = sSnmp.getAll("1.3.6.1.2.1.1.1.0", true, false);
			if (l != null && !l.isEmpty()) sysdescr = ((String[])l.get(0))[1];
			sysdescr = sysdescr.replace('\r', ' ');
			sysdescr = sysdescr.replace('\n', ',');
		} catch (TimeoutException te) { }

		return new String[] { sysname, sysobjectid, sysdescr };
	}

	private void insertNetbox(String host, String cs, boolean isGw) {
		String[] sysinfo = null;
		if (!netboxesInAllFile.contains(host) || !netboxesInNewFile.contains(host)) {
			sysinfo = getNetboxInfo();
		}

		sSnmp.setHost(host);

		synchronized (insertNetboxLock) {
			if (!netboxesInAllFile.contains(host)) {
				String dns = reverseDNS(host);
				writeBulkFile(allNetboxesBulkFile, host, isGw ? "GW" : "SW", cs, dns, sysinfo[0], sysinfo[1], sysinfo[2]);
				netboxesInAllFile.add(host);
			}

			try {
				// Check duplicate
				ResultSet rs = Database.query("SELECT netboxid FROM netbox WHERE ip='"+host+"'");
				if (rs.next()) {
					Log.d("INSERT_NETBOX", "Netbox already exists: " + host);
					return;
				}

				if (!netboxesInNewFile.contains(host)) {
					String dns = reverseDNS(host);
					writeBulkFile(newNetboxesBulkFile, host, isGw ? "GW" : "SW", cs, dns, sysinfo[0], sysinfo[1], sysinfo[2]);
					netboxesInNewFile.add(host);
				}
				incNumFound();

				if (!autoInsertNetbox) return;

				// Fetch sysLocation
				sSnmp.setSocketTimeout(500);
				String oid = getOid("sysLocation");
				List l = sSnmp.getAll(oid, true, true);
				if (l != null && !l.isEmpty()) {
					String[] s = (String[]) l.get(0);
					String location = s[1];
					String org = location;

					location = DEFAULT_LOCATIONID;
					org = DEFAULT_ORGID;
					// Look for syntax: snmp-server location <roomid> : <descr> : <utm>

					{
						rs = Database.query("SELECT roomid FROM room WHERE roomid='"+location+"'");
						if (!rs.next()) {
							Database.update("INSERT INTO room (roomid) VALUES ('"+location+"')");
						}
					}

					{
						rs = Database.query("SELECT orgid FROM org WHERE orgid='"+org+"'");
						if (!rs.next()) {
							Database.update("INSERT INTO org (orgid) VALUES ('"+org+"')");
						}
					}

					// Insert device
					String deviceid = "";
					{
						String[] ins = new String[] {
							"deviceid", ""
						};
						deviceid = Database.insert("device", ins, null);
					}
					String[] ins = new String[] {
						"ip", host,
						"roomid", location,
						"deviceid", deviceid,
						"catid", isGw ? "GW" : "SW",
						"orgid", org,
						"ro", cs,
					};
					Database.insert("netbox", ins);
					Log.d("INSERT_NETBOX", "Inserted new netbox: " + host);
				}
			} catch (Exception e) {
				e.printStackTrace(System.err);
			}
		}
	}

	private void updateMacDb(IP ip, boolean accessible) {
		synchronized (updateMacLock) {
			try {
				String mac = ip.getMac();
				ResultSet rs = Database.query("SELECT attempts FROM autodisc_mac_scanned WHERE mac='"+mac+"'");
				if (rs.next()) {
					String val = "null";
					if (!accessible) {
						ip.setAttempts(rs.getInt("attempts"));
						ip.incAttempts();
						val = "" + ip.getAttempts();
					}
					Database.update("UPDATE autodisc_mac_scanned SET attempts="+val+" WHERE mac='"+mac+"'");
				} else {
					String[] ins = new String[] {
						"mac", mac,
						"time", ""+ip.getTime(),
						"attempts", accessible ? "null" : "1",
						"found_snmp", accessible ? "true" : "false",
					};
					Database.insert("autodisc_mac_scanned", ins);
					ip.setAttempts(1);
				}
			} catch (SQLException e) {
				e.printStackTrace(System.err);
			}
		}
	}

	private boolean collectARP(String cs) {
		// Check if we really should collect arp
		try {
			/*
			ResultSet rs = Database.query("SELECT arpid FROM arp JOIN netbox USING(netboxid) WHERE arp.end_time='infinity' AND netbox.ip='"+ip.getIp()+"' LIMIT 1");
			if (rs.next()) {
				return true;
			}
			*/

			// Ok, try to collect ARP
			sSnmp.setSocketTimeout(500);
			String oid = getOid("ipNetToMediaPhysAddress");
			List l = sSnmp.getAll(oid, false, true);
			int newIps = 0;
			if (l != null && !l.isEmpty()) {
				for (Iterator it = l.iterator(); it.hasNext();) {
					String[] s = (String[])it.next();
					String host = s[0].substring(s[0].indexOf(".")+1, s[0].length());
					if (isLoopback(host)) continue;
					String mac = util.remove(s[1], ":").toLowerCase();
					if (seenMacs.contains(mac)) continue; // No need to check macs more than once
					IP newip = new IP(host, mac);
					addToRunQ(newip);
					newIps++;
				}
				Log.d("COLLECT_ARP", "Found " + newIps + " new IPs from ARP (" + l.size() + " fetched)");
				return true;
			}

		} catch (TimeoutException te) {
			// Do nothing, this is normal
		} catch (Exception e) {
			e.printStackTrace(System.err);
		}
		return false;
	}

	private boolean checkRouter(String host, String[] newHost) {
		try {
			List gwipList = sSnmp.getAll(getOid("ipAdEntIfIndex"), false, true);
			Map ifdescrMap = sSnmp.getAllMap(getOid("ifDescr"), true);

			if (gwipList != null && ifdescrMap != null) {
				String loopback = null;
				long lowgwip = Long.MAX_VALUE;
				for (Iterator it = gwipList.iterator(); it.hasNext();) {
					String[] s = (String[])it.next();
					String gwip = s[0];
					String ifindex = s[1];
					String ifdescr = (String) ifdescrMap.get(ifindex);

					gwip = validateIp(gwip);
					if (gwip == null) continue;

					if (ifdescr == null) continue;
					if (isLoopback(gwip)) continue;

					if (runningSNMP(gwip)) {
						try {
							sSnmp.setHost(gwip);
							sSnmp.setSocketTimeout(200);
							List newGwipList = sSnmp.getAll(getOid("ipAdEntIfIndex"), false, true);
							if (!isListEqual(gwipList, newGwipList)) continue;
						} catch (TimeoutException te) {
							continue;
						} finally {
							sSnmp.setHost(host);
							sSnmp.setSocketTimeout(500);
						}
					}

					if (ifdescr.toLowerCase().indexOf("loopback") >= 0) {
						// This is the IP we want
						loopback = gwip;
						break;
					}
					if (host.equals(gwip)) continue;

					long num = ipToNum(gwip);
					if (num < lowgwip) {
						loopback = gwip;
					}
				}
				if (loopback != null) {
					newHost[0] = loopback;
					return true;
				}

			}
		} catch (TimeoutException te) {
		} catch (Exception e) {
			e.printStackTrace(System.err);
		}
		return false;
	}

	private static String validateIp(String ip) {
		String[] s = ip.split("\\.");
		if (s.length < 4) return null;
		ip = "";
		for (int i=0; i < 4; i++) {
			try {
				int n = Integer.parseInt(s[i]);
				if (n < 0 || n > 255) return null;
				ip += n + ".";
			} catch (NumberFormatException e) {
			}
		}
		return ip.substring(0, ip.length()-1);
	}

	private static boolean isListEqual(List l1, List l2) {
		if (l1 == null || l2 == null) return false;
		if (l1.size() != l2.size()) return false;
		for (Iterator it = l1.iterator(), it2 = l2.iterator(); it.hasNext();) {
			String[] s1 = (String[]) it.next();
			String[] s2 = (String[]) it2.next();
			if (!s1[0].equals(s2[0]) || !s1[1].equals(s2[1])) return false;
		}
		return true;
	}

	private static boolean isLoopback(String ip) {
		if (ip.equals("0.0.0.0") || ip.startsWith("127")) return true;
		return false;
	}

	private String getOid(String oidkey) {
		try {
			ResultSet rs = Database.query("SELECT snmpoid FROM snmpoid WHERE oidkey='" + oidkey + "'");
			if (rs.next()) {
				return rs.getString("snmpoid");
			}
		} catch (SQLException e) {
			e.printStackTrace(System.err);
		}
		return null;
	}


	private static class CheckRunQTask extends TimerTask {
		public void run() {
			Log.setDefaultSubsystem("CHECK_RUN_Q");
			checkRunQ();
		}
	}

	private static class UpdateFromARPTask extends TimerTask {
		public void run() {
			updateFromARP();
		}
	}

	private static class IP {
		public String ip;
		public String mac;
		public long baseTime;
		public int attempts;

		public IP(String _ip, String _mac) {
			this(_ip, _mac, System.currentTimeMillis(), 0);
		}

		public IP(String _ip, String _mac, long _baseTime, int _attempts) {
			ip = _ip;
			mac = _mac;
			baseTime = _baseTime;
			attempts = _attempts;
		}

		public String getIp() {
			return ip;
		}

		public String getMac() {
			return mac;
		}

		public long getTime() {
			return baseTime;
		}

		public void setAttempts(int _attempts) {
			attempts = _attempts;
		}

		public void incAttempts() {
			attempts++;
		}

		public int getAttempts() {
			return attempts;
		}

		public long getNextRun() {
			long next = baseTime;
			if (attempts-1 >= 0) {
				next += (long) (Math.pow(DiscoveryThread.baseCheckInterval, Math.pow(DiscoveryThread.checkMultiplier, attempts-1)) * 1000);
			}
			return next;
		}

		public String toString() {
			return ip;
		}
	}

	private static String format(long i, int n)
	{
		DecimalFormat nf = new DecimalFormat("#");
		nf.setMinimumIntegerDigits(n);
		return nf.format(i);
	}

	// DNS Check code
	private static String[] hostBinCandidates = {
		"/bin/host",
		"/sbin/host",
		"/usr/bin/host",
		"/usr/sbin/host",
		"/usr/local/bin/host",
		"/usr/local/sbin/host",
	};
	private static File hostBin;
	private static Map dnsMap = Collections.synchronizedMap(new HashMap());

	private String reverseDNS(String ip) {
		if (dnsMap.containsKey(ip)) {
			return (String) dnsMap.get(ip);
		}

		// Do DNS lookup
		InetAddress ia = null;
		try {
			ia = InetAddress.getByName(ip);
		} catch (UnknownHostException e) {
			// Cannot happen as we always supply an IP address
		}
		String dnsName = ia.getCanonicalHostName();
		if (dnsName.equals(ip)) {
			dnsName = doHostReverseDNS(ip);
			if (dnsName.equals(ip)) {
				// DNS lookup failed
			}
		}
		dnsMap.put(ip, dnsName);
		return dnsName;
	}

	private String doHostReverseDNS(String ip) {
		try {
			if (hostBin == null) {
				for (int i=0; i < hostBinCandidates.length; i++) {
					File f = new File(hostBinCandidates[i]);
					if (f.exists() && f.isFile()) {
						hostBin = f;
						break;
					}
				}
			}

			String[] hostCmd = {
				hostBin.getAbsolutePath(),
				ip
			};

			Runtime rt = Runtime.getRuntime();
			Process p = rt.exec(hostCmd);
			BufferedInputStream in = new BufferedInputStream(p.getInputStream());
			try {
				p.waitFor();
			} catch (InterruptedException e) {
				System.err.println("InterruptedException: " + e);
				e.printStackTrace(System.err);
				return ip;
			}

			byte[] b = new byte[1024];
			in.read(b, 0, 1024);
			String s = new String(b).trim();

			// Check if found
			if (s.indexOf("not found") >= 0) return ip;

			// Extract DNS name
			String pat = ".*domain name pointer +(\\S{3,})";

			if (s.matches(pat)) {
				Matcher m = Pattern.compile(pat).matcher(s);
				m.matches();
				String host = m.group(1);
				if (host.endsWith(".")) host = host.substring(0, host.length()-1);
				return host;
			}

		} catch (IOException e) {
			System.err.println("IOException: " + e);
			e.printStackTrace(System.err);
		}
		return ip;
	}


}
