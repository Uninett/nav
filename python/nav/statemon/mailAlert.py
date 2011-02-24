# $Id$
# $Source: /usr/local/cvs/navbak/navme/subsystem/statemon/lib/mailAlert.py,v $

import smtplib, threading, Queue, time
from debug import debug


def mailAlert(*args, **kwargs):
    if _mailAlert._instance is None:
        _mailAlert._instance = _mailAlert(*args, **kwargs)
    return _mailAlert._instance

class _mailAlert(threading.Thread):
    _instance = None
    def __init__(self):
        threading.Thread.__init__(self)
        self.setDaemon(1)
        self._recipent = "drift-nav@itea.ntnu.no"
        self._sender = "drift-nav@itea.ntnu.no"
        self._alertq = Queue.Queue()
        self._alertlist = []

    def run(self):
        while 1:
            # Block until there is a item in our queue
            debug("mailalert -> Waiting for event")
            self._alertlist.append(self._alertq.get())
            debug("mailalert -> Got event, waiting for corrlated events")
            # Wait and see if we get any other reports
            time.sleep(300)
            for i in range(self._alertq.qsize()):
                self._alertlist.append(self._alertq.get())
            # Send the alert...
            debug("mailalert -> Stripping duplicates...")
            try:
                self.stripAlert()
            except Exception, info:
                debug("mailalert -> failed in stripAlert(): %s" % info)

            if not self._alertlist:
                debug("mailalert -> All events marked as duplicates.")
            else:
                debug("mailalert -> Creating mail body")
                self.createMailText()
                debug("mailalert -> Sending mail...")
                try:
                    self.sendMail()
                except Exception, info:
                    debug("mailalert -> Failed while sending alert: %s" % info,
                          1)
                # Empty the list of alerts...
                self._alertlist = []
            
    def stripAlert(self):
        """
        Remove duplicates and services that har both down and
        up message
        """
        alerthash = {}
        removable = []
        for each in self._alertlist:
            #
            #key="%s:%s" % (each.sysname, each.type)
            key = each.serviceid
            if not alerthash.has_key(key) or alerthash[key] == None:
                alerthash[key] = each
            elif (alerthash[key] != None and
                  alerthash[key].status != each.status):
                alerthash[key] = None
                debug("mailalert -> Removed duplicated alert: %s" % key)
            else:
                debug("mailalert -> Key: %s made it to the else clause..."%key)

        self._alertlist = filter(lambda x:x != None, alerthash.values())

    
    def createMailText(self):
        txt = "\n"
        for each in self._alertlist:
            txt += "[%s] %-17s %-5s -> %s, %s\n" % (each.time, each.sysname, each.type, each.status, each.info)
        self.alertText = txt


    def sendMail(self):
        subject = "[NAV ServiceMonitor] New event(s) %s" % (time.strftime('%Y-%m-%d %H:%M:%S'))
        msg = "From: %s\r\nTo: %s\r\nSubject: %s\r\n" % (self._sender, self._recipent, subject)
        msg += self.alertText
        msg += "\n\n--\nAs friendly as possible"
        msg += "\nCurrent status at: http://isbre.itea.ntnu.no/services/"

        smtpobj = smtplib.SMTP("smtp.stud.ntnu.no")
        smtpobj.set_debuglevel(0)
        smtpobj.sendmail(self._sender, self._recipent, msg)
        smtpobj.quit()
        debug("mailalert -> Alert sent successfully.")

            

    def put(self, event):
        self._alertq.put(event)
        debug("mailalert -> Queued alert: %s:%s" % (event.sysname, event.type))
