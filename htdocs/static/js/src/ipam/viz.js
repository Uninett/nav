// Vizualization plugin for displaying simple graphs about subnets (stacked,
// normalized barcharts with annotations). Accepts raw data from NAV's APIs
// (/api/).

// Using CommonJS wrapper in RequireJS for niceness. Should be easy to convert
// if it turns out to not work that well

define(function (require, exports, module) {
  var d3 = require("d3");
  var _ = require("libs/underscore");
  var util = require("src/ipam/util");
  var d3tip = require("d3tip");
  var d3v4 = require("d3v4");

  // === Tooltip (+ template)
  var tip = d3tip()
        .attr('class', 'd3-tip')
        .offset([-10, 0])
        .html(function(d) {
          var fmt = _.template("<strong><%= prefix %></strong>: <%= addr %>");
          return fmt({prefix: d.prefix, addr: d.max_addresses});
        });


  // Simple viewbox template
  var viewbox = _.template("0 0 <%= width %> <%= height %>");

  // TODO: Consider dropping rows to not draw too much at once (for usability
  // reasons)

  var DEFAULT_OPTS = {
    // layout settings
    width: 400,
    height: 50,
    margin: { top: 10, bottom: 10, left: 10, right: 10 },
    padding: 1,
    // the id of the element to mount the graph on
    mountElem: null,
    // data to display
    data: [{
      prefix: "10.0.0.0/8",
      parts: [ /* same datastructure*/ ]
    }],
    // function to scale the values (in the x dimension)
    scaleFn: function(n) { return n; }
  };

  function normalizeData(data, opts) {
    return _.map(opts.data, function (row) {
      row.parts = _.map(row.parts, function(d) {
        if (d.prefix !== "available") {
          d.usage = Math.random();
        }
        return d;
      });
      row.parts = util.normalize(row.parts, "max_addresses", opts.scaleFn);
      return row;
    });
  }

  // Draw a subnet chart.
  function subnetChart(inOpts) {
    // parse options
    var opts = _.extend(DEFAULT_OPTS, inOpts);
    var mountElem = opts.mountElem;
    var inData = opts.data;
    // size options
    var width = opts.width;
    var height = opts.height;
    var margin = opts.margin;
    var padding = opts.padding;

    if (!(inData.length && inData[0].parts.length)) {
      console.log("No data to display");
      return;
    }
    // get bounds of mountElem to responsively set width
    // var bounds = d3.select(mountElem).node().getBoundingClientRect();

    // normalize data
    var data = normalizeData(inData, opts);

    // === Drawing settings
    // [width, 0] makes the normalization step easier/prettier
    var xScale = d3.scale.linear()
          .range([width, 0]);

    var yScale = d3.scale.ordinal()
          .rangeRoundBands([0, height], .1);

    // Adapt yScale to data dimensions to ensure consistent spacing
    yScale.domain(_.map(data, function(d) { return d.prefix; }));

    var colors = d3.scale.category20();

    var svg;
    if (d3.select(mountElem).select("svg").empty()) {
      // Mount main SVG element
      svg = d3.select(mountElem)
        .append("svg")
        .attr("preserveAspectRatio", "xMaxYMin meet")
        .attr("viewBox", viewbox({width: width, height: height}))
        .append("g");
    } else {
      console.log("Already drawn. Trying to redraw?");
      svg = d3.select(mountElem).select("svg").select("g");
      // remove existing elements. this is stupid, should probably use lifetimes
      // (.update) etc instead
      d3.selectAll(".prefix").remove();
    }

    svg.call(tip);

    // Start drawing each prefix
    var prefixes = svg.selectAll(".graph-prefixes")
          .data(data)
          .enter()
          .append("g")
          .attr("class", "graph-prefixes")
          .attr("transform", function(d) {
            return util.translate(0, yScale(d.prefix));
          });

    // draw each bar for each prefix this prefix spans
    var prefix = prefixes.selectAll(".graph-prefix")
          .data(function (d) { return d.parts; })
          .enter()
          .append("g")
          .attr("class", "graph-prefix");

    // Attach tooltip to prefix
    prefix
      .on("mouseover", tip.show)
      .on("mouseout", tip.hide);

    // Draw available addresses (main graph)
    var bar = prefix.append("rect")
          .attr("height", yScale.rangeBand())
          .style("stroke", function(d) {
            return "#ccc";
          })
          .style("stroke-width", 0.25)
          .attr("x", function(d) { return xScale(d.delta1); })
          .attr("width", function(d) { return xScale(d.delta0) - xScale(d.delta1) - padding; })
          .style("fill", function(d) {
            if (d.prefix === "available") {
              // TODO: Use some kind of green highlight color?
              return "#000";
            }
            return "lightsteelblue";
          });

    function getMaskHeight(d) {
      return d.usage * yScale.rangeBand();
    }

    // Add usage mask. TODO: BTW, there has got to be a better way of doing
    // this. Maybe we should be able to set the rect to grow from the bottom of
    // the <g> instead of the top? Investigate...
    prefix.append("rect")
      .attr("height", getMaskHeight)
      .attr("transform", function(d) {
        return util.translate(0, yScale.rangeBand() - getMaskHeight(d));
      })
      .attr("x", function(d) { return xScale(d.delta1); })
      .attr("width", function(d) { return xScale(d.delta0) - xScale(d.delta1) - padding; })
      .style("fill", "steelblue")
      .on("mouseover", function(d) { console.log(d); });
  }

  // Simple percent vertical bar chart.
  function usageChart(inOpts) {
    // parse options
    var opts = _.extend(DEFAULT_OPTS, inOpts);
    var mountElem = opts.mountElem;
    var inData = opts.data;
    // size options
    var width = opts.width;
    var height = opts.height;
    var margin = opts.margin;
    var padding = opts.padding;

    // Normalize data based on value field
    var data = util.normalize(inData, "value", opts.scaleFn);

    // === Drawing settings
    var xScale = d3.scale.linear().range([width, 0]);
    var yScale = d3.scale.ordinal().rangeRoundBands([0, height], .1);
    var colors = d3.scale.category20();

    // === Drawing phase
    var svg = d3.select(mountElem)
          .append("svg")
          .attr("preserveAspectRatio", "xMinYMax slice")
          .attr("viewBox", viewbox({width: width, height: height}))
          .append("g");

    var bars = svg.selectAll(".usage-graph-bar")
          .data(data)
          .enter()
          .append("g")
          .attr("class", "usage-graph-bar");

    bars.append("rect")
      .attr("x", function(d) { return xScale(d.delta1); })
      .style("fill", function(d) {
        if (typeof d.fill === "undefined") {
          return colors(d.name);
        }
        return d.fill;
      })
      .attr("height", yScale.rangeBand())
      .attr("width", function(d) { return xScale(d.delta0) - xScale(d.delta1); });

    // TODO: add tooltip
  }




  // SUBnet matrix impl

  var IP_BITS = 32;
  var MATRIX_BITS = 8;
  function rowSpan(row) {
    return Math.pow(2, IP_BITS - MATRIX_BITS - row.prefixlen);
  }


  function subnetMatrix(inOpts) {
    var opts = _.extend(DEFAULT_OPTS, inOpts);
    var mountElem = opts.mountElem;
    var inData = opts.data;
    // size options
    var width = opts.width;
    var height = opts.height;
    var margin = opts.margin;
    var padding = opts.padding;
    var bitsInMatrix = 8;

    // todo: calculate height of each element (rowspan), use this to create offset.
    // width will be proportional to prefixlen (row width = 32 bits for IPv4)

    // Normalize data and calculate steps for height
    var data = util.normalize(inData, function(row) {
        return 32 - row.prefixlen;
    }, opts.scaleFn);
    console.log(data);

    // Width is based on host octet (assumed  to be last octet)
    var xScale = d3.scale.linear().range([width, 0]).domain([1, 32]);
    var xOffset = d3.scale.linear().range([width, 0]).domain([255, 0]);

    // Height is based on number of potential subnets (see rowHeight)
    var yScale = d3.scale.linear().range([0, height]).domain([0, 1]);

    var colors = d3.scale.category20();
    colors.domain(_.map(data, function(d){ return d.prefix; }));


    // === Drawing phase
    var svg = d3.select(mountElem)
          .append("svg")
          //.attr("preserveAspectRatio", "xMinYMax slice")
          .attr("viewBox", viewbox({width: width, height: height}))
          .append("g");

    var subnets = svg.selectAll(".subnets")
          .data(data)
          .enter()
          .append("g")
          .attr("class", "subnets");

    subnets.append("rect")
      .attr("x", function (d) {
        return xOffset(d.last_octet);
      }).attr("y", function (d) {
        return yScale(d.delta0);
      })
      .style("fill", function(d) {
        return colors(d.prefix);
      })
      .attr("height", function (d) { return yScale(d.delta1 - d.delta0); } )
      .attr("width", function(d) { return xScale(d.prefixlen); });

    subnets.append("text")
      .attr("x", function (d) {
        return xOffset(d.last_octet);
      }).attr("y", function (d) {
        var middle = Math.abs((d.delta1 - d.delta0) / 2.0);
        return yScale(d.delta0 + middle);
      })
      .text(function(d) {
        return d.prefix + ": " + d.description;
      });
  }

  module.exports = {
    "subnetChart": subnetChart,
    "usageChart": usageChart,
    "subnetMatrix": subnetMatrix
  };
});
