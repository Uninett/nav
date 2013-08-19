/**
 * Copyright (c) 2013 The New York Times
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
 */
/**
 * Network Administration Visualized changes:
 * Modified to fit the requirejs pattern and
 * not initialize on script.onload
 */
define(['libs/d3.v2'], function () {
  var doctype = '<?xml version="1.0" standalone="no"?><!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">';

  window.URL = (window.URL || window.webkitURL);

  function initialize() {
    var documents = [window.document],
        SVGSources = [];
    d3.selectAll("iframe").each(function() {
      if (this.contentDocument) {
        documents.push(this.contentDocument);
      }
    });
    documents.forEach(function(doc) {
      var styles = getStyles(doc);
      var newSources = getSources(doc, styles);
      // because of prototype on NYT pages
      for (var i = 0; i < newSources.length; i++) {
        SVGSources.push(newSources[i]);
      }
    });
    if (SVGSources.length > 1) {
      createPopover(SVGSources);
    } else if (SVGSources.length > 0) {
      download(SVGSources[0]);
    } else {
      alert("The Crowbar couldn’t find any SVG nodes.");
    }
  }

  function createPopover(sources) {
    cleanup();

  var drag = d3.behavior.drag()
      .origin(function() {
        var el = d3.select(this)
        return {
          x: el.style("left").replace("px", ""),
          y: el.style("top").replace("px", "")
        }
      })
      .on("drag", dragmove);

    sources.forEach(function(s1) {
      sources.forEach(function(s2) {
        if (s1 !== s2) {
          if ((Math.abs(s1.top - s2.top) < 38) && (Math.abs(s1.left - s2.left) < 38)) {
            s2.top += 38;
            s2.left += 38;
          }
        }
      })
    })

    var body = d3.select("body");

    var buttons = body.append("div")
        .attr("class", "svg-crowbar")
        .style("z-index", 1e7)
        .style("position", "absolute")
        .style("top", 0)
        .style("left", 0);

    var button = buttons.selectAll(".crowbar-button")
        .data(sources)
      .enter().append("div")
        .attr("class", "crowbar-button")
        .style("position", "absolute")
        .style("top", function(d) { return (d.top + document.body.scrollTop) + "px"; })
        .style("left", function(d) { return (document.body.scrollLeft + d.left) + "px"; })
        .style("padding", "4px")
        .style("border-radius", "3px")
        .style("color", "white")
        .style("text-align", "center")
        .style("font-family", "'Helvetica Neue'")
        .style("background", "rgba(0, 0, 0, 0.8)")
        .style("box-shadow", "0px 4px 18px rgba(0, 0, 0, 0.4)")
        .style("cursor", "move")
        .text(function(d, i) { return "SVG #" + i + ": " + (d.id ? "#" + d.id : "") + (d.class ? "." + d.class : "")})
      .append("button")
        .style("width", "150px")
        .style("font-size", "12px")
        .style("line-height", "1.4em")
        .style("margin", "5px 0 0 0")
        .text("Download")
        .on("click", function(d, i) {
          d3.event.preventDefault();
          download(d);
        });

    buttons.selectAll(".crowbar-button").call(drag);

    var html = body.append("div")
        .attr("class", "svg-crowbar")
        .style("background", "rgba(255, 255, 255, 0.7)")
        .style("position", "fixed")
        .style("left", 0)
        .style("top", 0)
        .style("width", "100%")
        .style("height", "100%");

    function dragmove(d) {
      d3.select(this)
          .style("left", d3.event.x + "px")
          .style("top", d3.event.y + "px");
    }
  }

  function cleanup() {
    d3.selectAll(".svg-crowbar").remove();
  }



  function getSources(doc, styles) {
    var svgInfo = [],
        svgs = d3.select(doc).selectAll("svg");

    styles = (styles === undefined) ? "" : styles;

    svgs.each(function () {
      var svg = d3.select(this);
      svg.attr("version", "1.1")
        .insert("defs", ":first-child")
          .attr("class", "svg-crowbar")
        .append("style")
          .attr("type", "text/css");

      // removing attributes so they aren't doubled up
      svg.node().removeAttribute("xmlns");
      svg.node().removeAttribute("xlink");

      // These are needed for the svg
      if (!svg.node().hasAttributeNS(d3.ns.prefix.xmlns, "xmlns")) {
        svg.node().setAttributeNS(d3.ns.prefix.xmlns, "xmlns", d3.ns.prefix.svg);
      }

      if (!svg.node().hasAttributeNS(d3.ns.prefix.xmlns, "xmlns:xlink")) {
        svg.node().setAttributeNS(d3.ns.prefix.xmlns, "xmlns:xlink", d3.ns.prefix.xlink);
      }

      var source = (new XMLSerializer()).serializeToString(svg.node()).replace('</style>', '<![CDATA[' + styles + ']]></style>');
      var rect = svg.node().getBoundingClientRect();
      svgInfo.push({
        top: rect.top,
        left: rect.left,
        width: rect.width,
        height: rect.height,
        class: svg.attr("class"),
        id: svg.attr("id"),
        childElementCount: svg.node().childElementCount,
        source: [doctype + source]
      });
    });
    return svgInfo;
  }

  function download(source) {
    var filename = "untitled";

    if (source.id) {
      filename = source.id;
    } else if (source.class) {
      filename = source.class;
    } else if (window.document.title) {
      filename = window.document.title.replace(/[^a-z0-9]/gi, '-').toLowerCase();
    }

    var url = window.URL.createObjectURL(new Blob(source.source, { "type" : "text\/xml" }));

    var a = d3.select("body")
        .append('a')
        .attr("class", "svg-crowbar")
        .attr("download", filename + ".svg")
        .attr("href", url)
        .style("display", "none");

    a.node().click();

    setTimeout(function() {
      window.URL.revokeObjectURL(url);
    }, 10);
  }

  function getStyles(doc) {
    var styles = "",
        styleSheets = doc.styleSheets;

    if (styleSheets) {
      for (var i = 0; i < styleSheets.length; i++) {
        processStyleSheet(styleSheets[i]);
      }
    }

    function processStyleSheet(ss) {
      if (ss.cssRules) {
        for (var i = 0; i < ss.cssRules.length; i++) {
          var rule = ss.cssRules[i];
          if (rule.type === 3) {
            // Import Rule
            processStyleSheet(rule.styleSheet);
          } else {
            // hack for illustrator crashing on descendent selectors
            if (rule.selectorText) {
              if (rule.selectorText.indexOf(">") === -1) {
                styles += "\n" + rule.cssText;
              }
            }
          }
        }
      }
    }
    return styles;
  }

  return initialize;
});