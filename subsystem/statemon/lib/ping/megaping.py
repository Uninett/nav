"""
$Id: megaping.py,v 1.2 2003/06/01 12:17:25 magnun Exp $                                                                                                                              
This file is part of the NAV project.                                                                                             
                                                                                                                                 
Copyright (c) 2002 by NTNU, ITEA nettgruppen                                                                                      
Author: Magnus Nordseth <magnun@stud.ntnu.no>
	Stian Soiland   <stain@stud.ntnu.no>
"""
import threading,sys,time,socket,select,os,profile,md5,random,struct,circbuf,debug,config
# From our friend:
import ip,icmp,rrd

ROTATION=r"/-\|"
PINGSTRING="Stian og Magnus ruler verden"

hasher = md5.md5()

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

class Host:
  def __init__(self, ip):
    self.rnd = random.randint(0,2**16)
    self.certain = 0
    self.ip = ip
    self.pkt = icmp.Packet()
    self.pkt.type = icmp.ICMP_ECHO
    self.pkt.id = os.getpid()
    self.pkt.seq = 0
    self.replies = circbuf.CircBuf()

  def makePacket(self, pingstring=PINGSTRING):
    self.pkt.data = pingstring
    return self.pkt.assemble()

  def nextseq(self):
    self.pkt.seq = (self.pkt.seq + 1) % 2**16
    if self.pkt.seq > 2 and not self.certain:
      self.certain = 1

  def __hash__(self):
    return self.ip.__hash__()

  def __eq__(self, obj):
    if type(obj) == type(""):
      return self.ip == obj
    else:
      return self.ip == obj.ip

  def logPingTime(self, pingtime):
    if pingtime:
      rrd.update(self.ip,'N','UP',pingtime)
    else:
      # Dette er litt grisete og bør endres
      rrd.update(self.ip,'N','DOWN',self.timeout)

  def getState(self, nrping=3):
    if self.certain:
      status = self.replies[:nrping] != [None]*nrping
      return status
    else:
      return 1

class MegaPing(RotaterPlugin):
  def __init__(self, socket=None, conf=None):
    RotaterPlugin.__init__(self)
    self.debug = debug.debug()
    if conf is None:
      self.conf=config.pingconf()
    else:
      self.conf=conf
    self.delay=float(self.conf.get('delay',2))/1000   # convert from ms
    self.timeout = int(self.conf.get('timeout', 5))
    self.hosts = []
    self.sent = 0
    packetsize = int(self.conf.get('packetsize', 64))
    if packetsize < 44:
      raise """Packetsize (%s) too small to create a proper cookie.
               Must be at least 44."""%packetsize
    self.packetsize=packetsize
    self.totaltWait=0
    self.pid = os.getpid()
    self.elapsedtime=0
    
    # Create our common socket
    if socket is None:
      self.socket = makeSocket()
    else:
      self.socket = socket

  def setHosts(self,hosts):
    """
    Specify a list of hosts to ping. If we alredy have the host
    in our list, we reuse that  host object
    """
    newhosts = filter(lambda x: x not in self.hosts, hosts)
    for ip in newhosts:
      self.hosts.append(Host(ip))

  def reset(self):
    self.requests = {}
    self.responses = {}
    self.senderFinished = 0
    self.totalWait=0

  def start(self):
    # Start working
    self.reset()
    #kwargs = {'mySocket': makeSocket()}
    self.sender = threading.Thread(target=self.sendRequests, name="sender")
    self.getter = threading.Thread(target=self.getResponses, name="getter")
    self.sender.setDaemon(1)
    self.getter.setDaemon(1)
    self.sender.start()
    self.getter.start()
    self.getter.join()
    #while(self.getter.isAlive()):
    #  self.rotate()    
    return self.elapsedtime
  
  #def icmpPrototype(self):
  #  self.pkt = icmp.Packet()
  #  self.pkt.type = icmp.ICMP_ECHO
  #  self.pkt.id = self.pid
  #  self.pkt.seq = 0 # Always sequence number 0..
  
  #def makeIcmpPacket(self, pingstring=PINGSTRING):
  #  self.pkt.data = pingstring
  #  return self.pkt.assemble()

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
          (pkt, (sender, blapp)) = self.socket.recvfrom(4096)
        except socket.error:
          self.debug.log("RealityError -2", 1)
          continue
        # could also use the ip module to get the payload

        repip = ip.Packet(pkt)
        try:
          reply = icmp.Packet(repip.data)
        except ValueError:
          self.debug.log("Recived illegeal packet from %s: %s" % (sender,repr(repip.data)), 7)
          continue
        if reply.id <> self.pid:
          self.debug.log("The id field of the packet does not match for %s"% sender,7)
          continue

        cookie = reply.data[0:14]
        try:
          host = self.requests[cookie]
        except KeyError:
          self.debug.log("The packet recieved from %s does not match any of the packets we sent." % repr(sender),7)
          self.debug.log("Length of recieved packet: %i Cookie: [%s]" % (len(reply.data), cookie),7)
          continue

        # Puuh.. OK, it IS our package <--- Stain, you're a moron
        pingtime = arrival - host.time
        ### sett inn i RotatingList
        host.replies.push(pingtime)
        host.logPingTime(pingtime)
        
        self.debug.log("Response from %-16s in %03.3f ms" % (sender, pingtime*1000),7)
        del self.requests[cookie]  
      elif self.senderFinished:
          break

    # Everything else timed out
    for host in self.requests.values():
      host.replies.push(None)
      host.logPingTime(None)
    end = time.time()
    self.elapsedtime=end-start


  def sendRequests(self, mySocket=None, hosts=None):
    if(mySocket is None):
      mySocket = self.socket
    if(hosts is None):
      hosts = self.hosts
    for host in hosts:
      if self.requests.has_key(host):
        self.debug.log("Duplicate host %s ignored" % host,6)
        continue

      now = time.time()
      host.time = now
      chrip = "".join(map(lambda x:chr(int(x)), host.ip.split('.')))
      packedtime = struct.pack('d', now)
      packedrnd = struct.pack('H', host.rnd)
      identifier = ''.join([chrip, packedtime, packedrnd])
      cookie = identifier.ljust(self.packetsize-icmp.ICMP_MINLEN)
      # typical cookie: "\x81\xf18F\x06\xf13\xc9\x87\xa8\xceA\xe5m"
      # the cookie is 14 bytes long
      self.requests[identifier] = host
      packet = host.makePacket(cookie)
      host.nextseq()
      mySocket.sendto(packet, (host.ip, 0))
      time.sleep(self.delay)
    self.senderFinished = time.time()
      
  def noAnswers(self):
    reply=[]
    for host in self.hosts:
      if not host.getState():
        reply.append(host.ip)

    return reply

  def answers(self):
    reply=[]
    for host in self.hosts:
      if host.getState():
        reply.append(host.ip)

    return reply
