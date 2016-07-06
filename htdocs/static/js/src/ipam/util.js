// Misc utility scripts

define(function (require, exports, module) {

  // Needed for Backbone.Wreqr
  var Backbone = require("backbone");
  var Marionette = require("marionette");

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


  // == SIMPLE NAMESPACED DEBUGGER (Backbone.Wreqr based)

  function mountDebugger() {
    if (typeof window.debugCh === "undefined") {
      console.log("[DEBUGGER] Mounting debugger");
      window.debugCh = Backbone.Wreqr.radio.channel("debug");
    }
  }

  // Usage: var debug = util.debug("my:name:space) => debug("my message", somedata)
  function debug(namespace) {
    mountDebugger();
    var _namespaces = namespace.split(":");
    // from models:foo:bar, generate [models:foo:bar, models:foo, models]
    var namespaces = _.reduce(_.range(1, _namespaces.length), function(acc, idx) {
      var tmp = _.take(_namespaces, idx);
      acc.push(tmp.join(":"));
      return acc;
    }, [namespace]);
    // console.log("Registering the following triggers for '" + namespace + "': ", namespaces);
    return function() {
      var args = [].slice.call(arguments, 0);
      // if any parent namespaces, generate triggers for them as well
      _.each(namespaces, function(ns) {
        var data = {
          ns: namespace,
          args: args
        };
        window.debugCh.vent.trigger(ns, data);
      });
    };
  }

  // Debug enabler
  var debugTmpl = _.template("[<%= namespace %>]");
  function debugListen(namespace) {
    mountDebugger();
    console.log("[DEBUGGER] Listening to '" + namespace + "'");
    window.debugCh.vent.on(namespace, function(data) {
      var s = debugTmpl({namespace: data.ns});
      var body = data.args;
      if (typeof body[0] === "string") {
        body = body[0];
      }
      var output = body;
      console.log(s, output);
    });
  }

  module.exports = {
    "calculateAvailable": calculateAvailable,
    "normalize": normalize,
    "translate": translate,
    "debug": debug,
    "debugListen": debugListen
  };

});
