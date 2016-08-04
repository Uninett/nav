// Starts the IPAM application

define(function(require, exports, module) {
  var viz = require("src/ipam/viz");
  var util = require("src/ipam/util");
  var App = require("src/ipam/app");
  var _ = require("libs/underscore");

  // Mount prefix tree on DOM
  App.start();

});
