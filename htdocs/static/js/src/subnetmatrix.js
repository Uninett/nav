require([], function() {

    var color_mapping = {
        80: 'usage-high',
        50: 'usage-medium',
        10: 'usage-low',
        0: ' usage-vlow'
    };

    
    /**
     * Fetch the usages for all elements
     */
    function fetchUsage(nextUrl) {
        var url = nextUrl || getUrl(4);
        var request = $.getJSON(url);
        request.done(handleData);
    }


    function getUrl(family) {
        var page_size = 10;  // Results per query
        return NAV.urls.api_prefix_usage_list + '?family=' + family + '&page_size=' + page_size;
    }
    
    
    /**
     * Handles the responsedata
     */
    function handleData(data) {
        if (data.next) {
            fetchUsage(data.next);
        }

        var $table = $('#subnet-matrix');

        // For each result, modify the cell based on the result data
        for (var i = 0, l = data.results.length; i < l; i++) {
            var result = data.results[i];

            var $element = $table.find('[data-netaddr="' + result.prefix + '"]');
            // Add correct class based on usage
            $element.removeClass(getColorClasses).addClass(getClass(result.usage));

            if ($element.attr('colspan') <= 4) {
                // This is a small cell
                addToTitle($element.closest('td'), result);
            } else {
                // Add link and text for usage
                $element.append(createLink(result));
            }
        }
    }


    /**
     * Remove the classes used to setting colors
     */
    function getColorClasses(index, classString) {
        return classString.split(/\s+/).filter(function(klass) {
            return klass.match(/^(subnet|usage)/);
        }).join(' ');
    }


    /**
     * Returns correct css-class based on usage
     */
    function getClass(usage) {
        var values = Object.keys(color_mapping).map(Number).sort();
        values.reverse();
        for (var i = 0; i < values.length; i++) {
            var value = values[i];
            if (usage >= value) {
                return color_mapping[value];
            }
        }

        return 'subnet-other';
        
    }


    /**
     * Creates a link for usage text
     */
    function createLink(data) {
        return $('<a>')
            .attr('href', data.url_machinetracker)
            .attr('title', addresString(data))
            .html(usageString(data));
    }


    /**
     * String used for listing active vs max addresses
     */
    function addresString(data) {
        return data.active_addresses + '/' + data.max_hosts;
    }
    

    /**
     * String used for displaying usage 
     */
    function usageString(data) {
        return '(' + data.usage.toFixed(0) + '%' + ')';
    }


    function addToTitle($element, data) {
        $element.attr('title', $element.attr('title') + ' ' + usageString(data));
    }


    // On page load, fetch all usages
    $(function() {
        fetchUsage();
    });


});
