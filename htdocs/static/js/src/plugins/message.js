define(["libs/d3.v2"], function () {

   function messageTooltip(node, message) {
       var d3Node = d3.select(node);
       var messageNode = d3Node.append("a")
           .attr("href", "#")
           .attr("title", message)
           .attr("class", "messageTooltip")
           .text(message);
       messageNode.transition()
           .delay(1500).transition().style("opacity", 0).each("end", function () {
               d3.select(this).remove();
           });
   }

   return {'messageTooltip':messageTooltip};

});
