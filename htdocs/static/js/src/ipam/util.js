// Everything that doesn't belong anywhere else

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
  // each data element, e.g. normalization. 'valueFieldOrFunction' is a function
  // that takes a data row and returns a numeric or value, or the field which
  // will be scaled during this step to calculate the step delta. row.delta0
  // denotes the start of the step, and delta1 denotes the end
  function normalize(arrayOfObj, valueFieldOrFunction, scaleFn) {
    var lookup = valueFieldOrFunction;
    if (!_.isFunction(valueFieldOrFunction)) {
      lookup = function(row) {
        return row[valueFieldOrFunction];
      };
    }
    // initialize step
    var step = 0;
    var newData = arrayOfObj;
    // parse options
    var _scaleFn = scaleFn || function(n) { return n; };
    // remove zero rows
    newData = _.reject(newData, function (row) {
      return lookup(row) === 0;
    });
    // calculate steps
    newData = _.map(newData, function (row) {
      row.delta0 = step;
      step += _scaleFn(lookup(row));
      row.delta1 = step;
      return row;
    });
    // normalize steps
    newData = _.map(newData, function (row) {
      row.delta0 /= step;
      row.delta1 /= step;
      return row;
    });
    return newData;
  }

  // Export debugger util lib
  var Debugger = require("libs/ipadebug");
  // Export state machine util lib
  var FSM = require("libs/statist");

  module.exports = {
    "calculateAvailable": calculateAvailable,
    "normalize": normalize,
    "translate": translate,
    "ipam_debug": Debugger("IPAM_DEBUG"),
    "FSM": FSM
  };

});
