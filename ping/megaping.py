import threading,sys,time,socket,select,os,profile

# From our friend:
import ip,icmp

ROTATION=r"/-\|"
PINGSTRING="Stian og Magnus ruler verden"

class RotaterPlugin:
  def __init__(self, delay=0.1):
    self.rotation = 0
    self.delay = delay
  def rotate(self, noDelay=None):
    self.rotation = (self.rotation + 1) % len(ROTATION)
    sys.stdout.write("\010" + ROTATION[self.rotation])
    sys.stdout.flush()
    if(not noDelay):
      time.sleep(self.delay)
  
def makeSocket():
  sock = socket.socket(socket.AF_INET, socket.SOCK_RAW,
                              socket.IPPROTO_ICMP)
  sock.setblocking(1)
  return sock

class MegaPing(RotaterPlugin):
  def __init__(self, hosts, timeout=5):
    RotaterPlugin.__init__(self)
    self.hosts = hosts
    self.requests = {}
    self.responses = {}
    self.senderFinished = 0
    
    self.timeout = timeout
    self.sent = 0
    self.pid = os.getpid()
    # Create our common socket
    self.socket = makeSocket()
    self.makeIcmpPackage()

  def start(self):
    # Start working
    self.sender = threading.Thread(target=self._sendRequests, name="sender")
    self.getter = threading.Thread(target=self._getResponses, name="getter")
    self.rotater = threading.Thread(target=self.rotateThread, name="rotater")
    self.sender.start()
    self.getter.start()
    self.rotater.start()
  
  def rotateThread(self):
    # While we wait
    while(self.getter.isAlive()):
      self.rotate()
  
  def makeIcmpPackage(self):
    # We use the same icmp-package to them all!
    pkt = icmp.Packet()
    pkt.type = icmp.ICMP_ECHO
    pkt.id = self.pid
    pkt.seq = 0 # Always sequence number 0..
    pkt.data = PINGSTRING
    self.package = pkt.assemble()

  def _getResponses(self):
    profiler = profile.Profile()
    profiler.runcall(self.getResponses)
    print "getResponse stats:"
    print profiler.print_stats()

  def getResponses(self):
    start = time.time()
    while not self.senderFinished or self.requests:
      rd, wt, er = select.select([self.socket], [], [], self.timeout)
      if rd:
        # okay to use time here, because select has told us
        # there is data and we don't care to measure the time
        # it takes the system to give us the package.
        arrival = time.time()
        try:
          (pkt, (host, blapp)) = self.socket.recvfrom(4096)
        except socket.error:
          continue
        # could also use the ip module to get the payload
        repip = ip.Packet(pkt)
        try:
          reply = icmp.Packet(repip.data)
        except ValueError:
          continue
        if reply.id == self.pid and reply.data == PINGSTRING:
          try:
            pingtime = time.time() - self.requests[host]
            self.responses[host] = pingtime
            # print "Response from %-16s in %03.3f secs" % (host, pingtime)
          except KeyError:
            continue
          del self.requests[host]  
      elif self.senderFinished:
        break

    # Everything else timed out
    for host in self.requests.keys():
      self.responses[host] = None
    end = time.time()
    print "It took ", end-start, "seconds"


  def _sendRequests(self, *args):
    profiler = profile.Profile()
    profiler.runcall(self.sendRequests, *args)
    print "sendRequests stats:"
    print profiler.print_stats()
  def multiSendRequests(self, threads=2):
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
      thread = threading.Thread(target=self._sendRequests, args=args)
      thread.start()
      time.sleep(0.01)
    
  def sendRequests(self, mySocket=None, hosts=None):
    if(mySocket is None):
      mySocket = self.socket
    if(hosts is None):
      hosts = self.hosts
    for host in hosts:
      try:
        host = socket.gethostbyname(host) # The IP
      except socket.error:
        hosts.remove(host)
        continue # Fuck you!
      self.requests[host] = time.time()
      mySocket.sendto(self.package, (host, 0))
    self.senderFinished = 1  
