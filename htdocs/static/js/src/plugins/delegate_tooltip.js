define([], function() {
    /**
     * Create tooltips on the fly
     *
     * This function attaches a listener to a parent element that creates
     * tooltips whenever the mouseover event triggers on the child elements
     * defined by the selector string
     * 
     * This is necessary because of the way Foundation loops through each
     * element and creates dom-elements on page load, thus totally killing
     * performance when the number of tooltips grow large.
     *
     * This solution is bare bones. It does not handle any extra options on the
     * element. It does not handle touch devices. Thus it is only functional for
     * desktop users.
     *
     * @param {jQuery|DomElement} parent - The element to delegate events to
     * @param {string} selector - The selector to apply tooltips to
     */
    function delegateTooltip(parent, selector) {
        var $parent = parent instanceof jQuery ? parent : $(parent);

        $parent.on('mouseenter', selector, function(event) {
            var $target = $(event.target);
            if (!$target.data('selector')) {
                // selector data attribute is only there if create has been run
                // before
                // Enable using a separate element for the tooltip text.
                var tipTextElement = $target.find('.tooltip-text');
                if (tipTextElement.length) {
                    $target.attr('title', tipTextElement.html());
                }
                Foundation.libs.tooltip.create($target);
                $target.on('mouseleave', function (event) {
                    Foundation.libs.tooltip.hide($target);
                });
            }
            Foundation.libs.tooltip.showTip($target);
        });
    }

    return delegateTooltip;
});
