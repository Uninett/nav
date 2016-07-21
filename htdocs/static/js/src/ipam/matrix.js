// TODO: we probably want to fetch usage data from
// http://localhost:8080/api/1/prefix/usage

define(function(require, exports, module) {
  var viz = require("src/ipam/viz");
  var util = require("src/ipam/util");

  // TODO: Do AJAX call and draw matrix

  var TARGET = "/ipam/api/?type=ipv4&net_type=scope&net_type=reserved&within=129.241.0.0/16";
  var AVAILABLE = "/ipam/api/find?prefix=129.241.0.0/16";

  $.get(TARGET).done(function (data) {
    console.log("Got data", data);
    $.get(AVAILABLE).done(function (available) {
      console.log(available);
    });
    viz.subnetMatrix({
      height: 600,
      width: 800,
      data: data,
      mountElem: "#ipam-matrix"
    });
  });

});


