import threading,sys,time,socket,select,os,profile

# From our friend:
import ip,icmp

ROTATION=r"/-\|"
PINGSTRING="Stian og Magnus ruler verden"

class RotaterPlugin:
  def __init__(self, rotdelay=0.1):
    self.rotation = 0
    self.rotatedelay = rotdelay
  def rotate(self, noDelay=None):
    self.rotation = (self.rotation + 1) % len(ROTATION)
    sys.stdout.write("\010" + ROTATION[self.rotation])
    sys.stdout.flush()
    if(not noDelay):
      time.sleep(self.rotatedelay)
  
def makeSocket():
  sock = socket.socket(socket.AF_INET, socket.SOCK_RAW,
                              socket.IPPROTO_ICMP)
  sock.setblocking(1)
  return sock

class MegaPing(RotaterPlugin):
  def __init__(self, hosts, timeout=5, delay=0.002):
    RotaterPlugin.__init__(self)
    self.delay=delay
    self.hosts = hosts
    self.timeout = timeout
    self.sent = 0
    self.totaltWait=0
    self.pid = os.getpid()
    self.icmpPrototype()
    # Create our common socket
    self.socket = makeSocket()

  def reset(self):
    self.requests = {}
    self.responses = {}
    self.senderFinished = 0
    self.totalWait=0

  def start(self, hosts=[]):
    # Start working
    if hosts:
      self.hosts=hosts
    self.reset()
    #kwargs = {'mySocket': makeSocket()}
    self.sender = threading.Thread(target=self.sendRequests, name="sender")
    self.getter = threading.Thread(target=self.getResponses, name="getter")
    self.sender.setDaemon(1)
    self.getter.setDaemon(1)
    self.sender.start()
    self.getter.start()
    while(self.getter.isAlive()):
      self.rotate()    
    
  def icmpPrototype(self):
    self.pkt = icmp.Packet()
    self.pkt.type = icmp.ICMP_ECHO
    self.pkt.id = self.pid
    self.pkt.seq = 0 # Always sequence number 0..
  
  def makeIcmpPacket(self, pingstring=PINGSTRING):
    self.pkt.data = pingstring
    return self.pkt.assemble()

  def _getResponses(self):
    profiler = profile.Profile()
    profiler.runcall(self.getResponses)
    print "getResponse stats:"
    print profiler.print_stats()

  def getResponses(self):
    start = time.time()
    timeout=self.timeout

    while not self.senderFinished or self.requests:      
      if self.senderFinished:
        runtime=time.time()-self.senderFinished
        if runtime > self.timeout:
          break
        else:
          timeout=self.timeout-runtime
          
      startwait = time.time()
      rd, wt, er = select.select([self.socket], [], [], timeout)
      if rd:
        # okay to use time here, because select has told us
        # there is data and we don't care to measure the time
        # it takes the system to give us the packet.
        arrival = time.time()
        try:
          (pkt, (host, blapp)) = self.socket.recvfrom(4096)
        except socket.error:
          print "RealityError -2"
          continue
        # could also use the ip module to get the payload

        repip = ip.Packet(pkt)
        try:
          reply = icmp.Packet(repip.data)
        except ValueError:
          print "Ugyldig format"
          continue
        if reply.id <> self.pid:
          continue
        try:
          (host, sent, pingstring) = reply.data.split('|')

        except:
          print "Noen fucker med oss, vi lager ikke slike pakker"
          continue # It's not our packet
        if pingstring <> PINGSTRING:
          print "Ikke vår pakke: %s" % pingstring
          continue
          
        try:
          if str(self.requests[host]) <> sent:
            continue # Not sent at our time
        except KeyError:
          #print "Vi sendte ikke til denne hosten: %s" % repr(host)
          continue # unknown host

        # Puuh.. OK, it IS our package <--- Stain, you're a moron
        pingtime = time.time() - self.requests[host]
        self.responses[host] = pingtime
          # print "Response from %-16s in %03.3f secs" % (host, pingtime)
        del self.requests[host]  
      elif self.senderFinished:
          break

    # Everything else timed out
    for host in self.requests.keys():
      self.responses[host] = None
    end = time.time()
    print "It took %4f seconds." % (end-start)



  def _sendRequests(self, *args):
    profiler = profile.Profile()
    profiler.runcall(self.sendRequests, *args)
    print "sendRequests stats:"
    print profiler.print_stats()
  def multiSendRequests(self, threads=10):
    """Split the hosts between several threads, each with their own
    socket"""
    partitionSize = len(self.hosts) / threads
    for threadNr in range(threads):
      start = partitionSize*threadNr
      if(threadNr == threads - 1):
        stop = len(self.hosts) # The last thread
      else:  
        stop = partitionSize*(threadNr+1)
      args = (makeSocket(), self.hosts[start:stop])
      thread = threading.Thread(target=self.sendRequests, args=args)
      thread.start()

  def sendRequests(self, mySocket=None, hosts=None):
    if(mySocket is None):
      mySocket = self.socket
    if(hosts is None):
      hosts = self.hosts
    for host in hosts:
      if self.requests.has_key(host):
        print "Duplicate host %s ignored" % host
        continue

      now = time.time()
      self.requests[host] = now
      identifier = '|'.join([host, str(now), PINGSTRING])
      # 129.241.190.190|2554428.22|Stian og Magnus ruler verden
      packet=self.makeIcmpPacket(identifier)
      mySocket.sendto(packet, (host, 0))
      time.sleep(self.delay)
    self.senderFinished = time.time()
      
  def noAnswers(self):
    return [host for (host, ping) in self.responses.items() if not ping]

  def answers(self):
    return [host for (host, ping) in self.responses.items() if ping]
