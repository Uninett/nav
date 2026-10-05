// Starts the IPAM application

define(function(require, exports, module) {
  var viz = require("src/ipam/viz");
  var util = require("src/ipam/util");
  var App = require("src/ipam/app");

  // Mount prefix tree on DOM
  App.start();

});
