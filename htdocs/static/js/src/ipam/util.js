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
  //   var util = require("util")
  //   var debug = util.debug("my:name:space")
  //   debug("Oh no, something went wrong")
  //   // listen to something
  //   util.debugListen("my:name")
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

  function mountDebugger() {
    if (typeof window.IPAM_DEBUG === "undefined") {
      window.IPAM_DEBUG = {};
      console.log("[DEBUGGER] Mounting debugger");
      // log factory
      window.IPAM_DEBUG.new = debug;
      // listen to some namespace (and unignore it)
      window.IPAM_DEBUG.listen = debugListen;
      // unlisten to some namespace (and ignore it)
      window.IPAM_DEBUG.unlisten = debugUnlisten;
      // maps namespaces to logging functions
      window.IPAM_DEBUG.namespaces = {};
      // list of ignored namespaces
      window.IPAM_DEBUG.ignored = [];
      window.IPAM_DEBUG.trigger = function(data) {
        if (window.IPAM_DEBUG.namespaces.hasOwnProperty(data.ns)) {
          if (_.contains(window.IPAM_DEBUG.ignored, data.origin)) {
            return;
          }
          var fn =  window.IPAM_DEBUG.namespaces[data.ns];
          fn(data);
        };
      };
    }
  }

  function debug(namespace) {
    mountDebugger();
    var _namespaces = namespace.split(":");
    // from models:foo:bar, generate [models:foo:bar, models:foo, models]
    var namespaces = _.reduce(_.range(1, _namespaces.length), function(acc, idx) {
      var tmp = _.take(_namespaces, idx);
      acc.push(tmp.join(":"));
      return acc;
    }, [namespace]);
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
        window.IPAM_DEBUG.trigger(data);
      });
    };
  }

  var debugTmpl = _.template("[<%= namespace %>]");
  function debugLog(data) {
    var s = debugTmpl({namespace: data.origin});
    var body = [].slice.call(data.args);
    var output = [s].concat(body);
    // Chrome/Safari only, handle in Firefox later on
    console.log.apply(console, output);
  }

  // Debug enabler. Should probably be settable in window.DEBUG or something
  function debugListen(namespace) {
    mountDebugger();
    window.IPAM_DEBUG.namespaces[namespace] = debugLog;
    // remove from ignored list
    window.IPAM_DEBUG.ignored = _.reject(window.IPAM_DEBUG.ignored, function(elem) {
      return elem == namespace;
    });
  }

  function debugUnlisten(namespace) {
    mountDebugger();
    delete window.IPAM_DEBUG.namespaces[namespace];
    window.IPAM_DEBUG.ignored.push(namespace);
  }

  module.exports = {
    "calculateAvailable": calculateAvailable,
    "normalize": normalize,
    "translate": translate,
    "debug": debug,
    "debugListen": debugListen,
    "debugUnlisten": debugUnlisten
  };

});
