require([], function() {

    function UsageFetcher(container) {
        this.page_size = 10;  // Results per query
        this.container = container;
        this.family = this.container.data('family') || 4;
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

            // For each result, modify the cell based on the result data
            for (var i = 0, l = data.results.length; i < l; i++) {
                var result = data.results[i];
                var $element = this.container.find('[data-netaddr="' + result.prefix + '"]');
                
                if (this.is_v4()) {
                    this.modifyV4Cell($element, result);
                } else {
                    this.modifyV6Cell($element, result);
                }
                $element.addClass('has-loaded');
            }
        },

        modifyV4Cell: function($element, result) {
            // Add correct class based on usage
            $element.removeClass(this.getColorClasses).addClass(this.getClass(result));
            if ($element.attr('colspan') > 4) {
                // Add link and text for usage if colspan is large enough
                $element.append(this.usageString(result));
            }
            this.createTooltipText($element, result);
        },

        modifyV6Cell: function($element, result) {
            $element.attr('style', 'background-color: ' + this.getIpv6Color(result));
            this.createTooltipText($element, result);
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


        createTooltipText: function($element, data) {
            var toAdd = ['<em>' + data.prefix + '</em><br>',
                         this.metaInfo(data),
                         this.createLink(data),
                         $element.attr('title')];
            $element.attr('title', toAdd.join('<br>'));
        },


        /** Creates a link for usage text */
        createLink: function(data) {
            return '<a href=' + data.url_machinetracker + '>' +
                'View active addresses' +
                '</a>';
        },


        /** String used for listing active vs max addresses */
        metaInfo: function(data) {
            if (this.is_v4()) {
                return ['Active IPs: ' + data.active_addresses + ' (of max ' + data.max_hosts + ')',
                        'Usage: ' + data.usage.toFixed(1) + '%'].join('<br>');
            } else {
                return 'Active IPs: ' + data.active_addresses;
            }
        },


        /** String used for displaying usage */
        usageString: function(data) {
            return '(' + data.usage.toFixed(0) + '%' + ')';
        },


        is_v4: function() {return this.family === 4;},
        is_v6: function() {return this.family === 6;},


        doubleLog: function(count) {
            return Math.log(Math.log(count + 1) + 1);
        },


        /** Returns a color based on active addresses using a mysterious formula */
        getIpv6Color: function(result) {
            if (result.active_addresses === 0) {
                return "#CCC";
            }
            var smallNumber1 = this.doubleLog(result.active_addresses);
            var smallNumber2 = this.doubleLog(Math.pow(2, 64));
            var new_color = 100 - parseInt(100 * smallNumber1 / smallNumber2);
            return "hsl(200,100%," + new_color + "%)";
        }

    };


    /**
     * Handler for adding and manipulating tooltips
     */
    function TooltipHandler(container) {
        this.container = container;
        this.openTips = [];  // Store open tooltips here
    }

    TooltipHandler.prototype = {
        addListeners: function() {
            var self = this;

            // Create tooltips on mouseenter to avoid title to be shown
            this.container.on('mouseenter', '.has-loaded', function(event) {
                var $target = $(event.target);

                if (!$target.data('selector')) {
                    // selector data attribute is only there if create has been
                    // run before
                    self.createTooltip($target);
                }
            });

            // Actually show the tooltip only on click.
            this.container.on('click', function(event) {
                var $target = $(event.target);

                if ($target.hasClass('has-loaded')) {
                    // if for some reason the tooltip has not been created, do it now
                    if (!$target.data('selector')) {
                        self.createTooltip($target);
                    }

                    if ($target.hasClass('open')) {
                        self.closeAllTips();
                    } else {
                        self.openTip($target);
                    }
                } else {
                    // If we click outside the cells, remove all tooltips
                    self.closeAllTips();
                }
            });

        },

        createTooltip: function(target) {
            console.log('Creating tooltip');
            Foundation.libs.tooltip.create(target);
        },

        closeAllTips: function() {
            var popped = this.openTips.pop();
            while (typeof popped !== 'undefined') {
                Foundation.libs.tooltip.hide(popped);
                popped = this.openTips.pop();
            }
        },

        openTip: function($target) {
            Foundation.libs.tooltip.showTip($target);
            this.closeAllTips();
            this.openTips.push($target);
        }

    };


    // Initialize stuff on page load
    $(function() {
        var $container = $('#subnet-matrix');
        var tooltipHandler = new TooltipHandler($container);
        tooltipHandler.addListeners();
        var fetcher = new UsageFetcher($container);
        fetcher.fetchUsage();
    });


});
