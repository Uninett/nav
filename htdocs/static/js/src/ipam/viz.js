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

  // === Tooltip (+ template)
  var tip = d3tip()
        .attr('class', 'd3-tip')
        .offset([-10, 0])
        .html(function(d) {
          return `<strong>${d.prefix}:</strong> ${d.max_addresses}`;
        });



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
            .attr("viewBox", `0 0 ${width} ${height}`)
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
          .attr("transform", function(d) { return `translate(0, ${yScale(d.prefix)})`; });

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
          .attr("x", function(d) { return xScale(d.x1); })
          .attr("width", function(d) { return xScale(d.x0) - xScale(d.x1) - padding; })
          .style("fill", function(d) {
            if (d.prefix == "available") {
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
        return `translate(0, ${yScale.rangeBand() - getMaskHeight(d)})`;
      })
      .attr("x", function(d) { return xScale(d.x1); })
      .attr("width", function(d) { return xScale(d.x0) - xScale(d.x1) - padding; })
      .style("fill", "steelblue")
      .on("mouseover", function(d) { console.log(d); });
  }

  module.exports = subnetChart;
});
