// Misc utility scripts

define(function (require, exports, module) {

  // Needed for Backbone.Wreqr
  var _ = require("libs/underscore");

  // Get the number of available addresses in a prefix (CIDR notation, e.g.
  // '10.0.0.0/8'), given all matching sub-prefixes
  function calculateAvailable(prefixlen, family) {
    var total_bits = family === 4 ? 32 : 128;
    return Math.pow(2, total_bits - prefixlen);
  }

  // Utility for translate statements, in lack of proper string templates for
  // ES5 (and any good reasons to transpile from ES6)
  function translate(x, y) {
    var fmt = _.template("translate(<%= xOffset %>, <%= yOffset %>)");
    return fmt({xOffset: x, yOffset: y});
  }

  // Remove zero elements and calculate relative steps (spanning [0, 1]) for
  // each data element, e.g. normalization. 'valueField' is the field which will
  // be scaled during this step to calculate the step delta.
  function normalize(arrayOfObj, valueField, scaleFn) {
    // initialize step
    var x0 = 0;
    var newData = arrayOfObj;
    // parse options
    var _scaleFn = scaleFn || function(n) { return n; };
    // remove zero rows
    newData = _.reject(newData, function (row) {
      return row[valueField] === 0;
    });
    // calculate steps
    newData = _.map(newData, function (row) {
      row.x0 = x0;
      x0 += _scaleFn(row[valueField]);
      row.x1 = x0;
      return row;
    });
    // normalize steps
    newData = _.map(newData, function (row) {
      row.x0 /= x0;
      row.x1 /= x0;
      return row;
    });
    return newData;
  }


  // == SIMPLE NAMESPACED DEBUGGER LOGGER (Backbone.Wreqr based)
  //
  // Supports colon-separated (':') namespaces. Example usage:
  //
  //   debug = require("src/ipam/util").Debugger("IPAM_DEBUG");
  //   var logger = debug.new("my:name:space")
  //   logger("Oh no, something went wrong")
  //   // listen to something
  //   debug.listen("my:name")
  //   // List all namespaces
  //   debug.listen()
  //   // Stop listening to namespace
  //   debug.unlisten("my:name")
  //
  // We also provide a magic object, window.IPAM_DEBUG for use in
  // the console provided by your browser.
  //
  //   > window.IPAM_DEBUG.new("my:name:space")
  //   > window.IPAM_DEBUG.listen("my:name")
  //   // mapping of each namespace handler to a logging function
  //   > window.IPAM_DEBUG.namespaces
  //   > window.IPAM_DEBUG.unlisten("my:name")
  //   // array of enabled namespaces
  //   > window.IPAM_DEBUG.enabledNamespaces

  function Debugger(name) {
    var debuggr = Object.assign({}, _Debugger);
    if (name !== null) {
      console.log("[DEBUGGER] Mounting debugger on", name);
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
      console.log("The following namespaces can be listened to:", namespaces);
    } else {
      console.log("No namespaces registered!");
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

  module.exports = {
    "calculateAvailable": calculateAvailable,
    "normalize": normalize,
    "translate": translate,
    "ipam_debug": Debugger("IPAM_DEBUG")
  };

});
