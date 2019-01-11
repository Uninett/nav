//
// Copyright (C) 2016 Uninett AS
//
// This file is part of Network Administration Visualized (NAV).
//
// NAV is free software: you can redistribute it and/or modify it under
// the terms of the GNU General Public License version 3 as published by
// the Free Software Foundation.
//
// This program is distributed in the hope that it will be useful, but WITHOUT
// ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
// FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
// more details.  You should have received a copy of the GNU General Public
// License along with NAV. If not, see <http://www.gnu.org/licenses/>.
//
// == SIMPLE NAMESPACED DEBUGGER LOGGER
//
// Supports colon-separated (':') namespaces. Example usage:
//
//   debug = require("ipadebug");
//   var logger = debug.new("my:name:space")
//   logger("Oh no, something went wrong")
//   // listen to something
//   debug.listen("my:name")
//   // Empty argument lists all registered namespaces
//   debug.listen()
//   debug.unlisten()
//   // Stop listening to namespace
//   debug.unlisten("my:name")
//
// If you want to bind to a field in 'window', supply it as an argument to the
// constructor:
//
//   debug = require("libs/ipadebug")("IPAM_DEBUG")
//   // in your JS console etc.
//   IPAM_DEBUG.listen("nodes")
//
// Future versions might offer more sophisticated functionality, but for now,
// this'll do.


define(function (require, exports, module) {

  var _ = require("libs/underscore");

  function Debugger(name) {
    var debuggr = {};
    _.extend(debuggr, _Debugger);
    if (name !== null) {
      helpString(name);
      window[name] = debuggr;
    }
    return debuggr;
  }

  // Scaffold object for Debugger constructor
  var _Debugger = {
    registered: [],
    ignored: [],
    namespaces: {}
  };

  // Router for incoming data
  _Debugger.trigger = function(data) {
    if (this.namespaces.hasOwnProperty(data.ns)) {
      if (_.contains(this.ignored, data.origin)) {
        return;
      }
      var fn =  this.namespaces[data.ns];
      fn(data);
    };
  };

  // Log function factory
  _Debugger.new = function(namespace) {
    var self = this;
    var namespaces = explodeNamespace(namespace);
    // register namespace, remove duplicates
    self.registered = registerNamespaces(self.registered, namespaces);
    return function() {
      var args = [].slice.call(arguments);
      // if any parent namespaces, generate triggers for them as well
      _.each(namespaces, function(ns) {
        var data = {
          ns: ns,
          origin: namespace,
          args: args
        };
        // Avoid triggering for non-enabled namespaces, to save some resources
        self.trigger(data);
      });
    };
  };

  // Create a handler which listens to events from 'namespace'
  _Debugger.listen = function(namespace) {
    var self = this;
    // No arguments => List available namespaces
    if (typeof namespace === "undefined") {
      listNamespaces(this.registered);
      return;
    }
    if (!_.contains(self.registered, namespace)) {
      console.log("[DEBUGGER] WARNING: There are no registered handlers for", namespace);
    }
    console.log("[DEBUGGER] Listening to", namespace);
    self.namespaces[namespace] = debugLog;
    // remove from ignored list
    self.ignored = _.reject(self.ignored, function(elem) {
      return elem == namespace;
    });
  };

  // Remove handler for events from 'namespace'
  _Debugger.unlisten = function(namespace) {
    var self = this;
    // Iterate over each namespace, deleting matching handlers (e.g. if we
    // ignore the parent namespace, we want to ignore every child as well)
    _.each(Object.keys(self.namespaces), function(_namespace) {
      var exploded = explodeNamespace(_namespace);
      if (_.contains(exploded, namespace)) {
        console.log("[DEBUGGER] Stopped listening to", _namespace);
        delete self.namespaces[_namespace];
      }
    });
    this.ignored.push(namespace);
  };

  // Add namespaces to the list of listenable namespaces
  function registerNamespaces(registered, namespaces) {
    var delta = _.difference(namespaces, registered);
    console.log("[DEBUGGER] Registering namespace(s)", delta);
    registered = _.union(registered, delta);
    registered.sort();
    return registered;
  };

  // List all available namespaces
  function listNamespaces(namespaces) {
    if (namespaces.length) {
      console.log("[DEBUGGER] The following namespaces can be listened to:", namespaces);
    } else {
      console.log("[DEBUGGER] No namespaces registered!");
    }
  };

  var debugTmpl = _.template("[<%= namespace %>]");
  function debugLog(data) {
    var s = debugTmpl({namespace: data.origin});
    var body = [].slice.call(data.args);
    var output = [s].concat(body);
    // Chrome/Safari only, handle in Firefox later on
    console.log.apply(console, output);
  };

  // From 'models:foo:bar', generate [models:foo:bar, models:foo, models]
  function explodeNamespace(namespace) {
    var _namespaces = namespace.split(":");
    var acc = _.reduce(_.range(1, _namespaces.length), function(acc, idx) {
      var tmp = _.take(_namespaces, idx);
      acc.push(tmp.join(":"));
      return acc;
    }, [namespace]);
    acc.sort();
    return acc;
  }

  var helpTmpl = _.template([
    " .----------------.  .----------------.  .----------------. ",
    "| .--------------. || .--------------. || .--------------. |",
    "| |     _____    | || |   ______     | || |      __      | |",
    "| |    |_   _|   | || |  |_   __ \\   | || |     /  \\     | |",
    "| |      | |     | || |    | |__) |  | || |    / /\\ \\    | |",
    "| |      | |     | || |    |  ___/   | || |   / ____ \\   | |",
    "| |     _| |_    | || |   _| |_      | || | _/ /    \\ \\_ | |",
    "| |    |_____|   | || |  |_____|     | || ||____|  |____|| |",
    "| |              | || |              | || |              | |",
    "| '--------------' || '--------------' || '--------------' |",
    " '----------------'  '----------------'  '----------------' ",
    "                                                            ",
    "   YOUR DEBUGGER IS STARTING. PLEASE GO GRAB A COLD BEER.   ",
    "   RUN 'window.<%= mountPoint %>.listen()' FOR LIST OF LOGGERS",
    "                                                            "
  ].join("\n"));

  function helpString(mountElem) {
    var s = helpTmpl({mountPoint: mountElem});
    console.log(s);
  }

  module.exports = Debugger;

});
