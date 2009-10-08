#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2008,2009 University of Tromsø
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 2 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#

import os
import re
import sys
import email
import ConfigParser
import logging
import types
import traceback
from optparse import OptionParser
import nav
import nav.mailin

def add_mailin_subsystem():
    """Ensure that the 'mailin' subsystem exists in the db"""
    
    conn = nav.db.getConnection('default', 'manage')
    cursor = conn.cursor()

    cursor.execute("select * from subsystem where name='mailin'")
    if cursor.rowcount == 0:
        cursor.execute("INSERT INTO subsystem (name, descr) VALUES ('mailin', '')")
    conn.commit()

def indent_msg(msg):
    """Indent every line in msg."""
    return re.sub(r'(^|\n)', r'\1    ', msg)

def load_plugins(paths):
    plugins = []

    for path in paths:
        logger.info('Loading plugin %s ...' % path)
        parent = path.split('.')[:-1]

        try:
            mod = __import__(path, globals(), locals(), [parent])
        except ImportError:
            logger.error('Plugin not found: %s' % path)
        except Exception, arg:
            logger.error('Failed to load plugin %s\n%s' % (path,
                                                           indent_msg(traceback.format_exc())))
            continue

        plugin = mod.Plugin(path, conf, logger)
        plugins.append(plugin)

    return plugins

def authorize_match(plugin, msg):
    """Test message headers against a pattern in the configuration file"""
    
    # Try to get 'authorization' option from plugin section
    # or from main section.
    if conf.has_option(plugin.name, 'authorization'):
        p = conf.get(plugin.name, 'authorization')
    elif conf.has_option('main', 'authorization'):
        p = conf.get('main', 'authorization')
    else:
        # No authorization pattern, so just let it through
        return True

    # Return True if the patterm matches at least one
    # header line
    pattern = re.compile(p)
    for key in msg.keys():
        value = msg[key]
        line = key + ': ' + value
        if pattern.search(line):
            return True

    # Should this logged as error or warning?
    logger.error("Message doesn't match auth pattern %s" % repr(p))
    return False

def make_logger(filename):
    logger = logging.getLogger('nav.mailin')
    logger.setLevel(logging.DEBUG)

    if filename == '-':
        # Log to stdout
        #     logging.basicConfig(level=logging.DEBUG)
        handler = logging.StreamHandler()
    else:
        if conf.has_option('main', 'logfile'):
            filename = conf.get('main', 'logfile')        
            # logging.basicConfig(filename=logfile, level=logging.DEBUG)

        handler = logging.FileHandler(filename)

    handler.setFormatter(logging.Formatter("[%(asctime)s] - %(name)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)

    return logger

def main():
    global logger
    global conf

    parser = OptionParser()
    parser.add_option('-i',
                      '--init',
                      dest='init',
                      action='store_true',
                      default=False,
                      help='Only load plugins and create event/alert types')
    parser.add_option('-t',
                      '--test',
                      dest='test',
                      action='store_true',
                      default=False,
                      help='Write events to stdout instead of posting them.')
    (options, args) = parser.parse_args()

    configfile = nav.buildconf.sysconfdir + '/mailin.conf'
    logfile = nav.buildconf.localstatedir + '/log/mailin.log'

    # Todo: fail if config file is not found
    conf = ConfigParser.ConfigParser()
    conf.read(configfile)

    # Must do this after config, so logfile can be configurable
    if options.test:
        logger = make_logger('-')
    else:
        logger = make_logger(logfile)
    
    add_mailin_subsystem()

    plugins = conf.get('main', 'plugins').split()
    plugins = load_plugins(plugins)

    if options.init:
        logger.info('Initialization done. Exiting.')
        return

    msg = email.message_from_file(sys.stdin)
    logger.info('---')
    logger.info('Got message: From=%s Subject=%s' % (repr(msg['From']), repr(msg['Subject'])))

    for plugin in plugins:
        if plugin.accept(msg):
            logger.info('%s accepted the message' % plugin.name)

            if authorize_match(plugin, msg):
                if plugin.authorize(msg):
                    events = plugin.process(msg)
                    if isinstance(events, nav.event.Event):
                        # Only one event, put it in a list
                        events = [events]

                    if options.test:
                        print 'Would have posted these events:'
                        for event in events:
                            print event
                    else:
                        for event in events:
                            event.post()
                            logger.info('Posted %s' % repr(event))
                else:
                    logger.error('Message not authorized')

            break  # Only one message gets to play

    logger.info('Done')

if __name__ == '__main__':
    main()
