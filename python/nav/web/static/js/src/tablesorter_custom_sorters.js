/**
 * Adds custom parsers to the global $.tablesorter object
 * See https://mottie.github.io/tablesorter/docs/example-parsers.html
 */
define(["jquery-tablesorter"], function() {
  /**
   * Returns data-sort-value attribute of a DOM node if the attribute is
   * defined.  If not, returns fallback
   *
   * @param {Element} node A DOM node
   * @param {String} fallback Value to return if node does not have
   *                          attribute
   */
  function getSortValue(node, fallback) {
    if (node.hasAttribute("data-sort-value")) {
      return node.getAttribute("data-sort-value");
    } else {
      return fallback;
    }
  }

  $.tablesorter.addParser({
    id: "custom-iso-datetime",
    is: function(text, table, node) {
      return false;
    },
    format: function(text, table, node) {
      const value = getSortValue(node, text);
      if (value === "last") {
        return Number.NEGATIVE_INFINITY;
      }
      if (value === "first") {
        return Number.POSITIVE_INFINITY;
      }
      return new Date(value).getTime();
    },
    parsed: false,
    type: "numeric"
  });
});
