require([], function() {


    function UsageFetcher() {
        this.page_size = 10;  // Results per query
        this.table = $('#subnet-matrix');
        this.family = this.table.data('family') || 4;
        this.color_mapping = {
            80: 'usage-high',
            50: 'usage-medium',
            10: 'usage-low',
            0: ' usage-vlow'
        };
    }

    UsageFetcher.prototype = {
        
        /** Fetch the usages for all elements */
        fetchUsage: function(nextUrl) {
            var self = this;
            var url = nextUrl || this.getUrl();
            var request = $.getJSON(url);
            request.done(function(data) {
                self.handleData(data);
            });
        },
        
        getUrl: function() {
            var query = 'family=' + this.family + '&page_size=' + this.page_size;
            return NAV.urls.api_prefix_usage_list + '?' + query;
        },

        /** Handles the responsedata */
        handleData: function(data) {
            if (data.next) {
                this.fetchUsage(data.next);
            }

            console.log(data);
            
            // For each result, modify the cell based on the result data
            for (var i = 0, l = data.results.length; i < l; i++) {
                var result = data.results[i];
                var $element = this.table.find('[data-netaddr="' + result.prefix + '"]');
                
                if (this.is_v4()) {
                    this.modifyV4Cell($element, result);
                } else {
                    this.modifyV6Cell($element, result);
                }
            }
        },

        modifyV4Cell: function($element, result) {
            // Add correct class based on usage
            $element.removeClass(this.getColorClasses).addClass(this.getClass(result));
            if ($element.attr('colspan') <= 4) {
                // This is a small cell
                this.addToTitle($element.find('a'), result);
            } else {
                // Add link and text for usage
                $element.append(this.createLink(result));
            }
        },

        modifyV6Cell: function($element, result) {
            $element.attr('style', 'background-color: ' + this.getIpv6Color(result));
            var $link = $element.find('a');
            var newTitle = 'Active IPs: ' + result.active_addresses + '. ' + $link.attr('title');
            $link.attr('title', newTitle);
        },


        /** Remove the color related classes */
        getColorClasses: function(index, classString) {
            return classString.split(/\s+/).filter(function(klass) {
                return klass.match(/^(subnet|usage)/);
            }).join(' ');
        },


        /** Returns correct css-class based on usage */
        getClass: function(result) {
            var values = Object.keys(this.color_mapping).map(Number).sort();
            values.reverse();
            for (var i = 0; i < values.length; i++) {
                var value = values[i];
                if (result.usage >= value) {
                    return this.color_mapping[value];
                }
            }

            return 'subnet-other';
        },


        /** Creates a link for usage text */
        createLink: function(data) {
            return $('<a>')
                .attr('href', data.url_machinetracker)
                .attr('title', this.addresString(data) + 'Click to see addresses in Machine Tracker.')
                .html(this.usageString(data));
        },


        /** String used for listing active vs max addresses */
        addresString: function(data) {
            return 'Usage: ' + data.active_addresses + ' of max ' + data.max_hosts + ' addresses. ';
        }, 
    

        /** String used for displaying usage */
        usageString: function(data) {
            return '(' + data.usage.toFixed(0) + '%' + ')';
        },


        addToTitle: function($element, data) {
            var toAdd = $element.attr('title') + ' - ' + this.addresString(data) +
                    'Click to see the report for this prefix.';
            
            $element.attr('title', toAdd);
        },


        is_v4: function() {return this.family === 4;},
        is_v6: function() {return this.family === 6;},


        doubleLog: function(count) {
            return Math.log(Math.log(count + 1) + 1);
        },
    

        /** Returns a color based on active addresses using a mysterious formula */
        getIpv6Color: function(result) {
            var smallNumber1 = this.doubleLog(result.active_addresses);
            var smallNumber2 = this.doubleLog(Math.pow(2, 64));
            var new_color = 256 - parseInt(255 * smallNumber1 / smallNumber2) - 1;
            var asHex = new_color.toString(16);
            return "#ff" + asHex + asHex;
        }
        
    };


    // On page load, fetch all usages
    $(function() {
        var fetcher = new UsageFetcher();
        fetcher.fetchUsage();
    });


});
