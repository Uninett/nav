#
# Copyright (C) 2006, 2010, 2016 Uninett AS
# Copyright (C) 2022 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""NAV Service start/stop library."""

import errno
import os
import shlex
import signal
import subprocess
import sys
import time
import re

import yaml

from nav.config import open_configfile, find_config_file, NAV_CONFIG
from nav.errors import GeneralException
from nav import buildconf

INFOHEAD = '## info:'
DAEMON_CONFIG = 'daemons.yml'
CRON_DIR = find_config_file('cron.d')


def get_info_from_content(content):
    """Extracts and returns service information from an iterable"""
    for line in content:
        if not line.startswith('#'):
            break
        elif line.startswith(INFOHEAD):
            return line.removeprefix(INFOHEAD).strip()


class Service(object):
    """Represents a NAV service in general, and should never be
    instantiated."""

    def __init__(self, filename):
        self.name = os.path.split(filename)[1]
        self.info = 'N/A'
        self.source = filename
        self.load_from_file(filename)

    def __repr__(self):
        return "<%s '%s'>" % (self.__class__.__name__, self.name)

    def load_from_file(self, filename):
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

    def is_up(self, silent=False):
        """Verifies that the service is up and running"""
        raise NotImplementedError

    def command(self, command, silent=False):
        """Runs command against this service handler"""
        raise NotImplementedError

    @classmethod
    def load_services(cls):
        """Loads all services of this kind"""
        raise NotImplementedError


class DaemonService(Service):
    """Represents daemon based services."""

    status = None

    def __init__(self, name, service_dict, source=None):
        self.name = name
        self.info = service_dict.get('description')
        self.source = source
        self._command = service_dict['command']
        self.service_dict = service_dict

    @classmethod
    def load_services(cls):
        try:
            with open_configfile(DAEMON_CONFIG) as ymldata:
                cfg = yaml.safe_load(ymldata)
        except OSError:
            cfg = {'daemons': {}}

        daemons = cfg.get('daemons')

        services = [
            cls(name, service_dict=values, source=DAEMON_CONFIG)
            for name, values in daemons.items()
            if values.get('enabled', True)
        ]

        return services

    def start(self, silent=False):
        if self.is_up():
            return False

        if not self.service_dict.get("privileged", False):
            # run command as regular nav user
            user = NAV_CONFIG.get("NAV_USER", "navcron")
            command = 'su {user} -c "{command}"'.format(
                command=self._command, user=user
            )
        else:
            command = self._command

        return self.execute(command, silent=silent)

    def stop(self, silent=False):
        if not self.is_up():
            return False

        pid = self.get_pid()
        for attempt in range(3):
            try:
                os.kill(pid, signal.SIGTERM)
            except OSError as error:
                if error.errno == errno.ESRCH:  # it's gone
                    return True
                else:
                    raise
            if self.is_up(pid=pid):
                delay = (attempt + 1) * 2
                time.sleep(delay)
        else:
            return False

    def restart(self, silent=False):
        if self.stop(silent=silent):
            return self.start(silent=silent)
        else:
            return False

    def is_up(self, silent=False, pid=None):
        if not pid:
            pid = self.get_pid()
        if not pid:
            return False

        try:
            os.kill(pid, 0)
        except OSError as error:
            if error.errno == errno.ESRCH:  # no such process
                return False
            elif error.errno == errno.EPERM:  # no permission, but it's there
                return True
            else:
                raise
        else:
            return True

    def get_pid(self):
        """Returns the last known pid of this process, if found"""
        pidfile = self.get_pidfile()
        if pidfile:
            with open(pidfile, 'r') as handle:
                pid = handle.readline().strip()
                if not pid or not pid.isdigit():
                    return
                return int(pid)

    def get_pidfile(self):
        """Attempts to locate the pidfile of this command"""
        pidfile = self.service_dict.get('pidfile')
        if pidfile and os.path.exists(pidfile):
            return pidfile
        elif pidfile:
            nameguess = pidfile
        else:
            nameguess = self.name + '.pid'

        locations = [
            os.path.join(buildconf.datadir, 'var/run'),
            '/var/run/nav',
            '/run/nav',
            '/tmp',
        ]
        for pidfile in [os.path.join(loc, nameguess) for loc in locations]:
            if os.path.exists(pidfile):
                return pidfile

    def command(self, command, silent=False):
        raise CommandNotSupportedError(command)

    def execute(self, command, silent=False):
        with open(os.devnull, 'w') as DEVNULL:
            if silent:
                stdout = stderr = DEVNULL
            else:
                stdout = stderr = None

            self.status = subprocess.call(
                list(shlex.split(command)), stdout=stdout, stderr=stderr
            )
            return self.status == 0


class CronService(Service):
    """Represents cron based services."""

    crontab = None

    def __init__(self, filename):
        self.content = None
        if CronService.crontab is None:
            cron_user = NAV_CONFIG.get('NAV_USER', 'navcron')
            CronService.crontab = Crontab(cron_user)
        super(CronService, self).__init__(filename)

    def load_from_file(self, filename):
        with open(filename, mode='r') as cronfile:
            self.content = [line.strip() for line in cronfile]
            self.info = get_info_from_content(self.content)

    @classmethod
    def load_services(cls):
        def _is_blacklisted(fname):
            return fname.startswith('.') or fname.endswith('~') or '.dpkg-' in fname

        if CRON_DIR:
            filelist = [
                os.path.join(CRON_DIR, f)
                for f in os.listdir(CRON_DIR)
                if not _is_blacklisted(f)
            ]
        else:
            filelist = []
        servicelist = [cls(f) for f in filelist]
        return servicelist

    def start(self, silent=False):
        if not silent:
            print("Starting %s:" % self.name, end=' ')
        try:
            CronService.crontab[self.name] = self.content
            CronService.crontab.save()
        except CrontabError as error:
            print("Failed")
            raise error
        else:
            if not silent:
                print("Ok")
            return True

    def stop(self, silent=False):
        if not silent:
            print("Stopping %s:" % self.name, end=' ')
        try:
            del CronService.crontab[self.name]
            CronService.crontab.save()
        except CrontabError as error:
            if not silent:
                print("Failed")
            raise error
        except KeyError:
            if not silent:
                print("Not running")
        else:
            if not silent:
                print("Ok")
            return True

    def restart(self, silent=False):
        self.stop(silent=silent)
        self.start(silent=silent)

    def is_up(self, silent=False):
        if not silent:
            print("%s:" % self.name, end=' ')
        if self.name in CronService.crontab:
            running_content = '\n'.join(CronService.crontab[self.name])
            my_content = '\n'.join(self.content)
            if not silent:
                print("Up")
                if running_content != my_content:
                    print(
                        "NOTICE: Current crontab does not match the content"
                        " of %s" % self.name,
                        file=sys.stderr,
                    )
            return True
        else:
            if not silent:
                print("Down")
            return False

    def command(self, command, silent=False):
        raise CommandNotSupportedError(command)


class Crontab(object):
    """Represents the crontab of a user.  Recognizes tags to define a
    block structure, which can be set/retrieved using a Crontab object
    as a dictionary."""

    def __init__(self, user):
        self.user = user
        self.content = ''
        self._blocks = {}
        self.load()

    def load(self):
        """Loads the currently active crontab"""
        try:
            output = subprocess.check_output(["crontab", "-u", self.user, "-l"])
            self.content = output.decode('utf-8').splitlines()
        except subprocess.CalledProcessError:
            # crontab doesn't have very helpful exit codes. if we get here, it
            # may simply be because the user has no defined crontab yet
            self.content = []
            _error = True
        except OSError as error:
            if error.errno == errno.ENOENT:
                raise CrontabError("crontab command was not found")
            else:
                raise
        else:
            _error = False

        # cron often inserts three comment lines in the spooled
        # crontab; the following is an attempt to remove those three
        # lines.
        for _dummy in range(3):
            if not self.content:
                break
            if self.content[0].startswith('# '):
                del self.content[0]
        self._parse_blocks()

        if not _error and '__init__' not in self:
            self.update_init()

    def save(self):
        """Saves the current state to the crontab"""
        self.update_init()
        proc = subprocess.Popen(
            ["crontab", "-u", self.user, "-"], stdin=subprocess.PIPE
        )
        proc.stdin.write(str(self).encode('utf-8'))
        proc.stdin.close()

        exit_code = proc.wait()
        if exit_code:
            raise CrontabError(exit_code)

    def update_init(self):
        """Update the __init__ block with current environment
        variables and such."""
        time_string = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
        env_vars = ('PERL5LIB', 'PYTHONPATH', 'CLASSPATH', 'PATH')
        init_block = ['# NAV updated this crontab at: ' + time_string]
        for var in env_vars:
            if var in os.environ:
                val = os.environ[var]
                init_block.append('%s="%s"' % (var, val))

        # Set up a default MAILTO directive
        mailto = NAV_CONFIG.get('ADMIN_MAIL', 'root@localhost')

        init_block.append('MAILTO=' + mailto)
        if '__init__' not in self:
            # If we don't have an init block, make sure we put it at
            # the very top of the crontab
            self.content[0:0] = ['##block __init__##', '##end##']
            self._parse_blocks()
        self['__init__'] = init_block

    def _parse_blocks(self):
        block_start = re.compile(r'^##block\s+([^#]+)##')
        block_end = '##end##'
        block_list = {}
        in_block = None
        start_line = 0
        pos = 0

        for line in self.content:
            if in_block is None:
                match = block_start.match(line)
                if match:
                    in_block = match.groups()[0]
                    start_line = pos
            elif line.startswith(block_end):
                block_list[in_block] = (start_line, pos)
                in_block = None
                start_line = 0
            pos += 1

        if in_block is not None:
            raise CrontabBlockError(self.user, in_block)
        self._blocks = block_list

    def __contains__(self, item):
        return item in self._blocks

    def __getitem__(self, key):
        pos = self._blocks[key]
        return self.content[pos[0] + 1 : pos[1]]

    def __setitem__(self, key, content):
        block = ['##block %s##' % key, '##end##']
        if isinstance(content, str):
            block[1:1] = content.split('\n')
        else:
            block[1:1] = content

        if key in self._blocks:
            ins_line = self._blocks[key][0]
            del self[key]
        else:
            ins_line = len(self.content)

        self.content[ins_line:ins_line] = block
        self._parse_blocks()

    def __delitem__(self, key):
        pos = self._blocks[key]
        del self.content[pos[0] : pos[1] + 1]
        self._parse_blocks()

    def __str__(self):
        return '\n'.join(self.content)


class ServiceRegistry(dict):
    """Registry of known NAV services."""

    def __init__(self):
        super(ServiceRegistry, self).__init__()

        service_list = []
        for service_type in (DaemonService, CronService):
            service_list.extend(service_type.load_services())

        for service in service_list:
            self[service.name] = service


#
# Exception/Error classes
#


class ServiceError(GeneralException):
    """General service error"""


class CommandNotSupportedError(ServiceError):
    """ "Command not supported"""


class CommandFailedError(ServiceError):
    """Command failed"""


class CrontabError(ServiceError):
    """General Crontab error"""


class CrontabBlockError(CrontabError):
    """ "There is an error in the block format of the crontab"""
