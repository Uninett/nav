"""ipdevpoll daemon.

This is the daemon program that runs the IP device poller.

"""
__author__ = "Morten Brekkevold (morten.brekkevold@uninett.no)"
__copyright__ = "Copyright 2008 UNINETT AS"
__license__ = "GPLv2"

import sys
import logging, logging.config
from twisted.internet import reactor
from ipdevpoll.models import load_models, Netbox
from ipdevpoll.snmpoid import RunHandler
from ipdevpoll.plugins import import_plugins

def run_poller():
    """Main execution hook, run after reactor start."""
    import_plugins()
    load_models()
    for netbox in Netbox.all.values():
        pollrun = RunHandler(netbox)
        pollrun.run()

def main():
    logging.config.fileConfig('logging.conf')
    logger = logging.getLogger('ipdevpoll')
    logger.info("--- Starting ipdevpolld ---")
    reactor.callWhenRunning(run_poller)
    reactor.run()

if __name__ == '__main__':
    main()
