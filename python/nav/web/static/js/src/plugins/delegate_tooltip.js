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
            // selector data attribute is only there if create has been run before
            if ($target.data('selector')) {
                Foundation.libs.tooltip.showTip($target);
            } else {
                var url = $target.data('url');
                var tipTextElement = $target.find('.tooltip-text');

                // Support fetching tooltip from API
                if (url) {
                    $.ajax({
                        url: $target.data('url'),
                        headers: {
                            'Accept': 'text/x-nav-html'
                        },
                        success: function(data) {
                            $target.attr('title', data);
                            createTooltip($target);
                        }
                    });
                } else if (tipTextElement.length) {
                    // Enable using a separate element for the tooltip text.
                    $target.attr('title', tipTextElement.html());
                    createTooltip($target);
                } else {
                    createTooltip($target);
                }
            }
        });
    }

    function createTooltip($target) {
        Foundation.libs.tooltip.create($target);
        Foundation.libs.tooltip.showTip($target);
        $target.on('mouseleave', function (event) {
            Foundation.libs.tooltip.hide($target);
        });
    }

    return delegateTooltip;
});
