// Vizualization plugin for displaying simple graphs about subnets (stacked,
// normalized barcharts with annotations)

// Using CommonJS wrapper in RequireJS for niceness. Should be easy to convert
// if it turns out to not work that well
define(function (require, exports, module) {
  var d3 = require("d3");
  var _ = require("libs/underscore");

  var exampleData = [
    { prefix: "10.5.0.1/16", parts: [
      // same data, format, only nested
    ]}
  ];

  // Normalize data, remove zero elements and calculate steps
  function normalize(data) {
    // initialize step
    var x0 = 0;

    var newData = data;

    // remove zero rows
    newData.parts = _.filter(data.parts, function (row) { return row.usage !== 0; });

    // calculate steps
    newData.parts = _.map(newData.parts, function (row) {
      var newRow = row;
      newRow.x0 = x0;
      x0 += row.usage;
      newRow.x1 = x0;
      return newRow;
    });
    // normalize steps
    newData.parts = _.map(newData.parts, function (row) {
      var newRow = row;
      newRow.x0 /= x0;
      newRow.x1 /= x0;
      return newRow;
    });
    return newData;
  }


  // Draw a subnet chart
  function subnetChart(mountElem, inData) {
    // get bounds of mountElem to responsively set width
    var bounds = d3.select(mountElem).node().getBoundingClientRect();

    // normalize data
    var data = inData.map(normalize);
    console.log(data);

    var width = 400;
    var height = 50;
    var margin = { top: 10, bottom: 10, left: 10, right: 10 };

    // [width, 0] makes the normalization step easier/prettier
    var xScale = d3.scale.linear()
          .range([width, 0]);

    var yScale = d3.scale.ordinal()
          .rangeRoundBands([0, height], .1);

    // Adapt yScale to data dimensions to ensure consistent spacing
    yScale.domain(data.map(function(d) { return d.prefix; }));

    var colors = d3.scale.category10();

    // Mount main SVG element
    var svg = d3.select(mountElem)
          .append("svg")
          .attr("preserveAspectRatio", "xMaxYMin meet")
          .attr("viewBox", `0 0 ${width} ${height}`)
          .append("g");

    // Start drawing each prefix
    var prefix = svg.selectAll(".prefix")
          .data(data)
          .enter()
          .append("g")
          .attr("class", "scope")
          .attr("transform", function(d) { return `translate(0, ${yScale(d.prefix)})`; });

    // draw each bar for each scope. tag parent in children as well
    prefix.selectAll("rect")
      .data(function (d) { return d.parts; })
      .enter()
      .append("rect")
      .attr("height", yScale.rangeBand())
      .attr("x", function(d) { return xScale(d.x1); })
      .attr("width", function(d) { return xScale(d.x0) - xScale(d.x1); })
      .style("fill", function(d) { return colors(d.prefix); });


  }

  module.exports = subnetChart;
});
