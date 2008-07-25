"""Handle scheduling of poll runs according to the NAV snmpoid database."""
__author__ = "Morten Brekkevold (morten.brekkevold@uninett.no)"
__copyright__ = "Copyright 2008 UNINETT AS"
__license__ = "GPLv2"

import logging

from twisted.internet import defer

import ipdevpoll
from ipdevpoll.plugins import plugin_registry

logger = logging.getLogger('ipdevpoll.snmpoid')

class RunHandler(object):

    """Handles a single polling run against a single netbox.

    The responsibility of finding matching plugins and executing them
    in a proper sequence is the responsibility of this class.

    """

    def __init__(self, netbox):
        self.netbox = netbox
        self.logger = ipdevpoll.get_instance_logger(self, 
                                                  "[%s]" % netbox.sysname)

    def find_plugins(self):
        """Populate and sort the interal plugin list."""
        self.plugins = []
        for plugin_class in plugin_registry:
            if plugin_class.can_handle(self.netbox):
                plugin = plugin_class(self.netbox)
                self.plugins.append(plugin)

        if not self.plugins:
            self.logger.warning("No plugins for this run")
            return

        # Sort plugin instances according to their intrinsic
        # comparison methods
        self.plugins.sort()
        self.logger.debug("Plugins to call: %s", 
                          ",".join([p.name() for p in self.plugins]))

    def run(self):
        """Do a polling run against a netbox."""
        self.logger.info("Starting polling run")
        self.find_plugins()
        self.plugin_iterator = iter(self.plugins)
        self.deferred = defer.Deferred()
        
        # Hop on to the first plugin
        self._nextplugin()
        return self.deferred

    def _nextplugin(self, result=None):
        """Callback that advances to the next plugin in the sequence."""
        try:
            self.current_plugin = self.plugin_iterator.next()
        except StopIteration:
            return self._done()
        else:
            self.logger.debug("Now calling plugin: %s", self.current_plugin)
            df = self.current_plugin.handle()
            # Make sure we advance to next plugin when this one is done
            df.addCallback(self._nextplugin)
            df.addErrback(self._error)

    def _error(self, failure):
        """Error callback that handles plugin failures."""
        if failure.check(ipdevpoll.FatalPluginError):
            # Handle known exceptions from plugins
            self.logger.error("Aborting poll run due to error in plugin "
                              "%s: %s",
                              self.current_plugin, failure.getErrorMessage())
        else:
            # For unknown failures we dump a traceback.  The
            # RunHandler will eat all plugin errors to protect the
            # daemon process.
            self.logger.error("Aborting poll run due to unknown error in "
                              "plugin %s\n",
                              self.current_plugin, failure.getTraceback())
        # Release the proxy (i.e. release the listening UDP port so we
        # don't hold on to resources unnecessarily)
        self.netbox.release_proxy()
        #self.deferred.errback(err)
        #return self.deferred

    def _done(self):
        """Performs internal cleanup and callback firing.

        This is called after successful poll run.

        """
        # Release the proxy (i.e. release the listening UDP port so we
        # don't hold on to resources unnecessarily)
        self.netbox.release_proxy()
        self.logger.info("Polling run done")
        # Fire the callback chain
        self.deferred.callback(self)
        return self.deferred
