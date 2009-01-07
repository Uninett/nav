"""ipdevpoll daemon.

This is the daemon program that runs the IP device poller.

"""
__author__ = "Morten Brekkevold (morten.brekkevold@uninett.no)"
__copyright__ = "Copyright 2008 UNINETT AS"
__license__ = "GPLv2"

import sys
import logging, logging.config
from optparse import OptionParser

from twisted.internet import reactor

from ipdevpoll.models import loop_load_models, Netbox
from ipdevpoll.snmpoid import RunHandler
from ipdevpoll.plugins import import_plugins

from nav import buildconf

def schedule_polling(result=None):
    """Initiate polling schedule.

    First time around, all netboxes are polled immediately.
    """
    for netbox in Netbox.all.values():
        pollrun = RunHandler(netbox)
        pollrun.run()

def run_poller():
    """Load plugins, set up data caching and polling schedules."""
    import_plugins()
    loop_load_models().addCallback(schedule_polling)

def get_parser():
    """Setup and return a command line option parser."""
    parser = OptionParser(version="NAV " + buildconf.VERSION)
    parser.add_option("-c", "--config", dest="configfile",
                      help="read configuration from FILE", metavar="FILE")
    parser.add_option("-l", "--logconfig", dest="logconfigfile",
                      help="read logging configuration from FILE", 
                      metavar="FILE")
    return parser


def main():
    """Main exection function"""
    parser = get_parser()
    (options, args) = parser.parse_args()

    logging.config.fileConfig('logging.conf')
    logger = logging.getLogger('ipdevpoll')
    logger.info("--- Starting ipdevpolld ---")
    reactor.callWhenRunning(run_poller)
    reactor.run()

if __name__ == '__main__':
    main()
