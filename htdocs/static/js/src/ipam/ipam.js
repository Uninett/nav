// TODO: we probably want to fetch usage data from
// http://localhost:8080/api/1/prefix/usage

define(["src/ipam/viz"], function (viz) {

  // TODO: Import URI.js to create URL in a sane way

  var baseUrl = "/api/1/prefix/usage?starttime=2014-06-02T15:00:00";

  $(".scope-show-usage").on("click", function(e) {
    var elem = $(this);
    var mountElem = elem.data("mount-elem");
    var prefix = elem.data("prefix");

    console.log("Trying to fetch usage data for this scope");

    var targetUrl = `${baseUrl}&scope=${prefix}`;

    // TODO: Handle pagination
    $.get(targetUrl, function(data) {
      console.log(data);
      var properData = [{
        prefix: prefix,
        parts: data.results
      }];
      viz(mountElem, properData);
    });

  });

});


