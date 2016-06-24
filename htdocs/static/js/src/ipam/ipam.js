// TODO: we probably want to fetch usage data from
// http://localhost:8080/api/1/prefix/usage

define(function(require, exports, module) {
  var viz = require("src/ipam/viz");
  var util = require("src/ipam/util");
  var _ = require("libs/underscore");

  // TODO: Import URI.js to create URL in a sane way
  var BASE_URL = "/api/1/prefix/usage?starttime=2014-06-02T15:00:00";

  // Add fake prefix containing available addresses in scope
  function availablePrefix(data) {
    var used = _.reduce(data.parts, function(acc, n) {
      return acc + n.max_addresses;
    }, 0);
    var maximum = util.calculateAvailable(data.prefixlen, data.ip_version);
    var available = maximum - used;
    return {
      prefix: "available",
      usage: 0.00000000001,
      max_addresses: available
    };
  }

  function fetchPrefixStats(e) {
    var elem = $(this);
    var data = elem.data("json");
    var prefix = data.cidr;
    var mountElem = "#scope-graph-" + data.pk;
    var prefixlen = data.prefixlen;
    var ip_version = data.ip_version;

    console.log("Trying to fetch usage data for this scope");

    var targetUrl = `${BASE_URL}&scope=${prefix}`;

    // TODO: Handle pagination
    $.get(targetUrl, function(data) {
      console.log("Got data!");
      console.log(data);
      var properData = {
        prefix: prefix,
        prefixlen: prefixlen,
        ip_version: ip_version,
        // ensure correct order of CIDRs
        parts: data.results.reverse()
      };
      // add fake node with data about availability
      properData.parts.push(availablePrefix(properData));
      console.log(properData);

      viz({
        mountElem: mountElem,
        data: [properData],
        scaleFn: Math.log2
      });
    });
  }

  // Marker class for "real" prefixes, e.g. not RFC1918 fake nodes in tree
  $(".scope-tree-item-has-stats").on("click", fetchPrefixStats);

});


