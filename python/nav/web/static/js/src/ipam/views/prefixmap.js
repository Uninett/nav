// D3 component for displaying and exploring allocated prefixes. Expects an
// options object with the following fields defined:
//
// - `mountElem`, the selector for the element to mount the SVG elem upon.
//
// - `width`, `height` - self-explanatory, but do note that this element only
// enforces the relative aspect ratio of the width and height, and expands to
// fill the whole container width.
//
// - `selectNodeCallBack`, which is invoked with the selected node as its
// argument when the user clicks on a prefix.
//
// - `data`, which is the JSON serialization of a PrefixHeap (see NAV API docs).
// It is expected that the top level is a "virtual" prefix ("*") with the rest
// of tree as its child.


define(function(require, exports, module) {

  var _ = require("libs/underscore");
  var d3 = require("d3v4");

  var viewbox = _.template("0 0 <%= width %> <%= height %>");
  var tooltipTmpl = _.template("<%= prefix %> <% if (vlan_number) { %> (vlan <%= vlan_number %>)<% } %> - <%= description %>");

  var PrefixMap = function(opts) {
    var width = opts.width;
    var height = opts.height;
    var mountElem = opts.mountElem;
    var data = opts.data.children[0];
    var selectNodeCallback = opts.selectNodeCallBack;

    // Minor constants
    var BRUSH_BOX_HEIGHT = 20;
    var BRUSH_BOX_PADDING = 20;

    // Canonical xScale is needed to preserve original between different zoom
    // extents, e.g. recover original scale.
    var xScale = d3.scaleLinear().range([0, width]);
    var canonicalXScale = d3.scaleLinear().range([0, width]);
    var yScale = d3.scaleLinear().range([0, height]);

    // Split into hierarchical data (a tree), weighted by prefix length
    var partition = d3.partition();
    var root = d3.hierarchy(data);
    root.each(function (node) {
      if (_.isUndefined(node.data.prefixlen === "undefined")) return;
      node.value = Math.pow(2, 32 - node.data.prefixlen);
    });
    partition(root);

    // Main container. We use a viewbox as a simple responsive solution for the viz
    var svg = d3.select(mountElem).select(".viz")
          .append("svg")
          .attr("viewBox", viewbox({width: width, height: height + BRUSH_BOX_PADDING + BRUSH_BOX_HEIGHT}))
          .attr("class", "matrix")
          .append("g");

    var rootTmpl = _.template("<%= prefix %> <% if (description) {%>- <%= description %><% } %>");

    // Container for tooltip on nodes
    var div = d3.select("body").append("div")
          .attr("class", "prefix-tooltip")
          .style("opacity", 0);

    // Draw static top node, e.g. not enhanced by zoom
    var rootElem = _.first(root.descendants());
    var rootNode = svg.selectAll("g")
          .data([rootElem])
          .enter()
          .append("g")
          .attr("transform", "translate(" + xScale(rootElem.x0) + "," + yScale(rootElem.y0) + ")")
          .attr("class", "matrix-subnet-root");
    rootNode.append("rect")
      .attr("class", "matrix-subnet-root-rect")
      .attr("fill", colors)
      .attr("stroke", colors(rootElem).darker(1))
      .attr("width", xScale(rootElem.x1) - xScale(rootElem.x0))
      .attr("height", yScale(rootElem.y1) - yScale(rootElem.y0))
      .on("mouseover", function(d) {
        div.transition()
          .duration(200)
          .style("opacity", .9);
        div.html(tooltipTmpl(rootElem.data))
          .style("left", (d3.event.pageX) + "px")
          .style("top", (d3.event.pageY - 28) + "px");
      })
      .on("mouseout", function(d) {
        div.transition()
          .duration(500)
          .style("opacity", 0);
      });
    rootNode
      .append("text")
      .attr("visibility", "visible")
      .attr("x", 0.5 * (xScale(rootElem.x1) - xScale(rootElem.x0)))
      .attr("y", 0.5 * (yScale(rootElem.y1) - yScale(rootElem.y0)))
      .attr("class", "matrix-subnet-root-prefix")
      .append("tspan")
      .text(rootTmpl(rootElem.data))
      .attr("x", 0.5 * (xScale(rootElem.x1) - xScale(rootElem.x0)))
      .attr("y", 0.5 * (yScale(rootElem.y1) - yScale(rootElem.y0)));

    // Add containers/rects for each node in the prefix tree
    var subnet = svg.selectAll("g")
          .data(root.descendants())
          .enter()
          .append("g")
          .attr("transform", function(d) { return "translate(" + xScale(d.x0) + "," + yScale(d.y0) + ")"; })
          .attr("class", "matrix-subnet");
    var subnetRect = subnet.append("rect")
          .attr("class", "matrix-subnet-rect")
          .attr("fill", colors)
          .attr("stroke", function(d) { return colors(d).darker(1); })
          .on("click", function(d) {
            selectNodeCallback(d.data);
          })
          .on("mouseover", function(d) {
            div.transition()
              .duration(200)
              .style("opacity", .9);
            div.html(tooltipTmpl(d.data))
              .style("left", (d3.event.pageX) + "px")
              .style("top", (d3.event.pageY - 28) + "px");
          })
          .on("mouseout", function(d) {
            div.transition()
              .duration(500)
              .style("opacity", 0);
          });
    calculateNodes();

    // Annotate the nodes with text
    var subnetText = subnet.append("text");
    var subnetPrefix = subnetText.append("tspan")
          .attr("class", "matrix-subnet-prefix")
          .on("click", function(d) {
            selectNodeCallback(d.data);
          });
    calculateText();

    // Draw legends for the viz
    var legend = d3.select(mountElem).select(".legends").selectAll(".legends")
          .data(_.keys(colorMap))
          .enter()
          .append("g");
    var legendDot = legend
          .append("div")
          .style("display", "inline-block")
          .style("border", "1px solid #666")
          .style("width", "30px")
          .style("height", "10px")
          .style("margin-right", "5px")
          .style("background-color", function(d) { return colorMap[d]; });
    var legendText = legend
          .append("span")
          .style("margin-right", "10px")
          .text(function(d) { return d.toString(); });

    // Calculates the appropriate dimensions of all nodes depending on the domain of the xScale
    function calculateNodes() {
      // Only calculate bottom nodes
      subnet.transition()
        .duration(750)
        .attr("transform", function(d) {
          return "translate(" + xScale(d.x0) + "," + yScale(d.y0) + ")";
        });
      subnetRect.transition()
        .duration(750)
        .attr("width", function(d) {
          return xScale(d.x1) - xScale(d.x0);
        })
        .attr("height", function(d) {
          return yScale(d.y1) - yScale(d.y0);
        });
    }

    // Calculate what (if any) text should be shown for each prefix. TODO:
    // Should use the bounding box of the text instead.
    function calculateText() {
      subnetText.selectAll("tspan").transition()
        .duration(750)
        .attr("visibility", function(d) {
          return xScale(d.x0 + (d.x1 - d.x0)) - xScale(d.x0) > 30 ? "visible" : "hidden";
        })
        .attr("x", function(d) { return 0.5 * (xScale(d.x1) - xScale(d.x0)); })
        .attr("y", function(d) { return 0.5 * (yScale(d.y1) - yScale(d.y0)); })
        .text(function(d) {
          var _width = xScale(d.x1) - xScale(d.x0);
          if (_width > 100) {
            return d.data.prefix;
          } else if (_width > 50) {
            return "/" + d.data.prefixlen;
          } else {
            return "";
          }
        });
      // Center text
      subnetText.selectAll("tspan")
        .attr("x", function(d) { return 0.5 * (xScale(d.x1) - xScale(d.x0)); })
        .attr("y", function(d) { return 0.5 * (yScale(d.y1) - yScale(d.y0)); });
    }

    // Add a context which we can mount our brush and axis on
    var context = svg.append("g")
          .attr("transform", "translate(0, " + (height + BRUSH_BOX_PADDING) + ")")
          .attr("class", "context");

    // Construct brush behavior
    var brush = d3.brushX()
          .extent([[0, 0], [width, BRUSH_BOX_HEIGHT]])
          .on("end", brushended);
    var brushBox = context
          .append("rect")
          .attr("class", "brush-box")
          .attr("fill", "lightgrey")
          .attr("height", BRUSH_BOX_HEIGHT)
          .attr("width", width);
    context.append("g")
      .attr("class", "brush")
      .call(brush);

    // Construct zoom behavior
    var zoom = d3.zoom()
          .scaleExtent([1, Infinity])
          .translateExtent([[0, 0], [width, height]])
          .extent([[0, 0], [width, height]])
          .on("zoom", zoomed);
    svg.call(zoom);

    // TODO: Create small axis "grid" to draw this brush upon
    function brushended() {
      if (d3.event.sourceEvent && d3.event.sourceEvent.type === "zoom") return;
      if (!d3.event.sourceEvent) return; // Only transition after input.
      var s = d3.event.selection || canonicalXScale.range();
      xScale.domain(canonicalXScale.domain());
      xScale.domain(s.map(canonicalXScale.invert, xScale));
      // redraw stuff
      calculateText();
      calculateNodes();
      // update zoom selection to reflect brush selection
      svg.call(zoom.transform, d3.zoomIdentity
               .scale(width / (s[1] - s[0]))
               .translate(-s[0], 0));
    }

    function zoomed() {
      if (d3.event.sourceEvent && d3.event.sourceEvent.type === "brush") return; 
      var t = d3.event.transform;
      xScale.domain(t.rescaleX(canonicalXScale).domain());
      // redraw stuff
      calculateText();
      calculateNodes();
      // update brush selection to reflect zoom level
      context.select(".brush").call(brush.move, xScale.range().map(t.invertX, t));
    }

  };

  // Maps different types of nodes to different colors
  var colorMap = {
    "used": d3.hsl(52, 1.0, 0.5),
    "reserved": d3.hsl(210, 0.79, 0.46),
    "available": d3.hsl(0, 0, 1),
    "scope": d3.hsl(0, 0, 0.87)
  };
  // Map a node type to its particular color.
  function colors(d) {
    // root node
    if (d.depth === 0) {
      return d3.hsl(199, 0.91, 0.64);
    }
    if (_.has(colorMap, d.data.net_type)) {
      return colorMap[d.data.net_type];
    }
    return colorMap["used"];
  }

  module.exports = PrefixMap;

});
