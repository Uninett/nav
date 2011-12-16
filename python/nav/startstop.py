#
# Copyright (C) 2003, 2004 Norwegian University of Science and Technology
# Copyright (C) 2006, 2010 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""NAV Service start/stop library."""
from __future__ import with_statement

import os
import os.path
import sys
import time
import re
import nav.config
from nav.errors import GeneralException
from UserDict import UserDict

try:
    import nav.buildconf
except ImportError:
    CRONDIR = 'cron.d'
    INITDIR = 'init.d'
else:
    CRONDIR = nav.buildconf.crondir
    INITDIR = nav.buildconf.initdir

INFOHEAD = '## info:'
def getInfoFromContent(content):
    """Extracts and returns service information from an iterable"""
    for line in content:
        if not line.startswith('#'):
            break
        elif line.startswith(INFOHEAD):
            return line[len(INFOHEAD):].strip()

class Service(object):
    """ Represents a NAV service in general, and should never be
    instantiated."""
    def __init__(self, filename):
        self.name = os.path.split(filename)[1]
        self.info = 'N/A'
        self.source = filename
        self.loadFromFile(filename)

    def __repr__(self):
        return "<%s '%s'>" % (self.__class__.__name__, self.name)

    def loadFromFile(self, filename):
        """Loads the service from a file"""
        raise NotImplementedError

    def start(self, silent=False):
        """Starts the service"""
        raise NotImplementedError

    def stop(self, silent=False):
        """Stops the service"""
        raise NotImplementedError

    def restart(self, silent=False):
        """Restarts the service"""
        raise NotImplementedError

    def isUp(self, silent=False):
        """Verifies that the service is up and running"""
        raise NotImplementedError

    def command(self, command, silent=False):
        """Runs command against this service handler"""
        raise NotImplementedError

    @classmethod
    def loadServices(cls):
        """Loads all services of this kind"""
        raise NotImplementedError


class DaemonService(Service):
    """ Represents daemon based services."""
    def loadFromFile(self, filename):
        with file(filename, 'r') as initfile:
            self.info = getInfoFromContent(initfile)

    def loadServices(cls):
        def _isBlacklisted(fname):
            return (fname.startswith('.') or fname.endswith('~')
                    or fname == 'functions'
                    or '.dpkg-' in fname)
        fileList = [os.path.join(INITDIR, f)
                    for f in os.listdir(INITDIR)
                    if not _isBlacklisted(f)]
        serviceList = [cls(f) for f in fileList]
        return serviceList
    loadServices = classmethod(loadServices)

    def start(self, silent=False):
        if not self.command('start', silent=silent):
            if self.status >> 8 == 1:
                return False
            else:
                raise CommandFailedError, self.status
        else:
            return True

    def stop(self, silent=False):
        if not self.command('stop', silent=silent):
            if self.status >> 8 == 1:
                return False
            else:
                raise CommandFailedError, self.status
        else:
            return True

    def restart(self, silent=False):
        if not self.command('restart', silent=silent):
            if self.status >> 8 == 1:
                return False
            else:
                raise CommandFailedError, self.status
        else:
            return True

    def isUp(self, silent=False):
        if not self.command('status', silent=silent):
            if self.status >> 8 == 1:
                return False
            else:
                raise CommandFailedError, self.status
        else:
            return True

    def command(self, command, silent=False):
        silence = silent and ' > /dev/null 2> /dev/null' or ''
        self.status = os.system(self.source + ' ' + command + silence)
        return (self.status == 0)


class CronService(Service):
    """ Represents cron based services."""
    crontab = None
    cronUser = 'navcron'

    def __init__(self, filename):
        self.content = None
        if CronService.crontab is None:
            CronService.crontab = Crontab(CronService.cronUser)
        super(CronService, self).__init__(filename)

    def loadFromFile(self, filename):
        with file(filename, 'r') as cronfile:
            self.content = [line.strip() for line in cronfile]
            self.info = getInfoFromContent(self.content)

    def loadServices(cls):
        def _isBlacklisted(fname):
            return (fname.startswith('.') or fname.endswith('~')
                    or '.dpkg-' in fname)
        fileList = [os.path.join(CRONDIR, f)
                    for f in os.listdir(CRONDIR)
                    if not _isBlacklisted(f)]
        serviceList = [cls(f) for f in fileList]
        return serviceList
    loadServices = classmethod(loadServices)

    def start(self, silent=False):
        if not silent:
            print "Starting %s:" % self.name,
        try:
            CronService.crontab[self.name] = self.content
            CronService.crontab.save()
        except CrontabError, error:
            print "Failed"
            raise error
        else:
            if not silent:
                print "Ok"
            return True

    def stop(self, silent=False):
        if not silent:
            print "Stopping %s:" % self.name,
        try:
            del CronService.crontab[self.name]
            CronService.crontab.save()
        except CrontabError, error:
            if not silent:
                print "Failed"
            raise error
        except KeyError, error:
            if not silent:
                print "Not running"
        else:
            if not silent:
                print "Ok"
            return True

    def restart(self, silent=False):
        self.stop(silent=silent)
        self.start(silent=silent)

    def isUp(self, silent=False):
        if not silent:
            print "%s:" % self.name,
        if CronService.crontab.has_key(self.name):
            runningContent = '\n'.join(CronService.crontab[self.name])
            myContent = '\n'.join(self.content)
            if not silent:
                print "Up"
                if runningContent != myContent:
                    print >> sys.stderr, ("NOTICE: Current crontab does not "
                                          "match the content of %s" % self.name)
            return True
        else:
            if not silent:
                print "Down"
            return False

    def command(self, command, silent=False):
        raise CommandNotSupportedError(command)


class Crontab(object):
    """ Represents the crontab of a user.  Recognizes tags to define a
    block structure, which can be set/retrieved using a Crontab object
    as a dictionary."""
    def __init__(self, user):
        self.user = user
        self.content = ''
        self._blocks = {}
        self.load()

    def load(self):
        """Loads the currently active crontab"""
        pipe = os.popen('crontab -u %s -l' % self.user)
        self.content = [line.strip() for line in pipe.readlines()]
        pipe.close()
        # cron often inserts three comment lines in the spooled
        # crontab; the following is an attempt to remove those three
        # lines.
        for _dummy in range(3):
            if not self.content:
                break
            if self.content[0][:2] == '# ':
                del self.content[0]
        self._parseBlocks()

        if not self.has_key('__init__'):
            self.updateInit()

    def save(self):
        """Saves the current state to the crontab"""
        self.updateInit()
        pipe = os.popen('crontab -u %s -' % self.user, 'w')
        pipe.write(str(self))
        exit_code = pipe.close()
        if exit_code:
            raise CrontabError, exit_code

    def updateInit(self):
        """ Update the __init__ block with current environment
        variables and such."""
        timeString = time.strftime("%Y-%m-%d %H:%M:%S",
                                   time.localtime(time.time()))
        envVars = ('PERL5LIB', 'PYTHONPATH', 'CLASSPATH', 'PATH')
        initBlock = ['# NAV updated this crontab at: ' + timeString]
        for var in envVars:
            if os.environ.has_key(var):
                val = os.environ[var]
                initBlock.append('%s="%s"' % (var, val))

        # Set up a default MAILTO directive
        mailto = 'root@localhost'
        try:
            navConf = nav.config.readConfig('nav.conf')
            if navConf.has_key('ADMIN_MAIL'):
                mailto = navConf['ADMIN_MAIL']
        except IOError:
            pass

        initBlock.append('MAILTO=' + mailto)
        if not self.has_key('__init__'):
            # If we don't have an init block, make sure we put it at
            # the very top of the crontab
            self.content[0:0] = ['##block __init__##', '##end##']
            self._parseBlocks()
        self['__init__'] = initBlock

    def _parseBlocks(self):
        blockStart = re.compile('^##block\s+([^#]+)##')
        blockEnd = '##end##'
        blockList = {}
        inBlock = None
        startLine = 0
        pos = 0

        for line in self.content:
            if inBlock is None:
                m = blockStart.match(line)
                if m:
                    inBlock = m.groups()[0]
                    startLine = pos
            elif line.startswith(blockEnd):
                blockList[inBlock] = (startLine, pos)
                inBlock = None
                startLine = 0
            pos += 1

        if inBlock is not None:
            raise CrontabBlockError, (self.user, inBlock)
        self._blocks = blockList

    def has_key(self, key):
        return self._blocks.has_key(key)

    def keys(self):
        return self._blocks.keys()

    def __getitem__(self, key):
        pos = self._blocks[key]
        return self.content[pos[0]+1:pos[1]]

    def __setitem__(self, key, content):

        block = ['##block %s##' % key, '##end##']
        if type(content) is str:
            block[1:1] = content.split('\n')
        else:
            block[1:1] = content

        if self._blocks.has_key(key):
            insLine = self._blocks[key][0]
            del self[key]
        else:
            insLine = len(self.content)

        self.content[insLine:insLine] = block
        self._parseBlocks()

    def __delitem__(self, key):
        pos = self._blocks[key]
        del self.content[pos[0]:pos[1]+1]
        self._parseBlocks()

    def __str__(self):
        return '\n'.join(self.content)

class ServiceRegistry(UserDict):
    """ Registry of known NAV services."""
    def __init__(self):
        UserDict.__init__(self)

        serviceList = []
        for serviceType in (DaemonService, CronService):
            serviceList.extend(serviceType.loadServices())

        for service in serviceList:
            self[service.name] = service

#
# Exception/Error classes
#
class ServiceError(GeneralException):
    "General service error"

class CommandNotSupportedError(ServiceError):
    "Command not supported"

class CommandFailedError(ServiceError):
    "Command failed"

class CrontabError(ServiceError):
    "General Crontab error"

class CrontabBlockError(CrontabError):
    "There is an error in the block format of the crontab"

