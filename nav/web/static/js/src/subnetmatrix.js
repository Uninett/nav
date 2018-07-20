require(['libs/underscore', 'libs/jquery.sparkline'], function() {

    function UsageFetcher(container) {
        this.page_size = 10;  // Results per query
        this.container = container;
        this.family = this.container.data('family') || 4;
        this.scope = this.container.data('scope');
        this.feedbackContainer = $('#subnet-matrix-feedback');
        this.color_mapping = {
            80: 'usage-high',
            50: 'usage-medium',
            10: 'usage-low',
            0: ' usage-vlow'
        };
        this.tooltipTemplateV4 = _.template(
            '<h5><%= heading %></h5>' +
                '<p>Active IPs: <%= active %> (of max <%= max %>)<br>' +
                'Usage: <%= usage %>%<br>' +
                '<% if (vlan_id) { %>VLAN: <%= vlan_id %><br><% } %>' +
                '<% if (net_ident) { %>netident: <%= net_ident %><br><% } %></p>' +
                '<a href="<%= url_machinetracker %>" title="<%= title_machinetracker %>">' +
                '<%= linktext_machinetracker %></a><br>' +
                '<a href="<%= url_report %>" title="<%= title_report %>">' +
                '<%= linktext_report %></a><br>' +
                '<a href="<%= url_vlan %>" title="<%= title_vlan %>">' +
                '<%= linktext_vlan %></a>'
        );
        this.tooltipTemplateV6 = _.template(
            '<h5><%= heading %></h5>' +
                '<p>Active IPs: <%= active %><br>' +
                '<% if (vlan_id) { %>VLAN: <%= vlan_id %><br><% } %>' +
                '<% if (net_ident) { %>netident: <%= net_ident %><br><% } %></p>' +
                '<a href="<%= url_machinetracker %>" title="<%= title_machinetracker %>">' +
                '<%= linktext_machinetracker %></a><br>' +
                '<a href="<%= url_report %>" title="<%= title_report %>">' +
                '<%= linktext_report %></a><br>' +
                '<a href="<%= url_vlan %>" title="<%= title_vlan %>">' +
                '<%= linktext_vlan %></a>'
        );
    }

    UsageFetcher.prototype = {

        /** Fetch the usages for all elements */
        fetchUsage: function(nextUrl) {
            var self = this;
            var url = nextUrl || this.getUrl();
            var request = $.getJSON(url);
            request.done(function(data) {
                if (data.next) {
                    self.fetchUsage(data.next);
                }
                self.handleData(data);
            });
            request.fail(function() {
                self.feedbackContainer.html('Some or all of the prefix usage data could not be loaded. If you want to try again, you must reload the page.');
                self.feedbackContainer.removeClass('hidden');
            });
        },

        getUrl: function() {
            var params = ['page_size=' + this.page_size,
                          'scope=' + encodeURIComponent(this.scope)];
            var query = params.join('&');
            return NAV.urls.api_prefix_usage_list + '?' + query;
        },

        /** Handles the responsedata */
        handleData: function(data) {
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
            this.createTooltipText($element, this.tooltipTemplateV4, result);
        },

        modifyV6Cell: function($element, result) {
            $element.attr('style', 'background-color: ' + this.getIpv6Color(result));
            this.createTooltipText($element, this.tooltipTemplateV6, result);
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


        createTooltipText: function($element, template, data) {
            var text = template({
                heading: data.prefix,
                active: data.active_addresses,
                max: data.max_hosts,
                usage: data.usage.toFixed(1),
                url_machinetracker: data.url_machinetracker,
                net_ident: data.net_ident,
                vlan_id: data.vlan_id,
                title_machinetracker: "View active addresses in MachineTracker",
                linktext_machinetracker: "View active addresses",
                url_report: data.url_report,
                title_report: "View report for " + data.prefix,
                linktext_report: "View report",
                url_vlan: data.url_vlan,
                title_vlan: "View vlan info for related vlan",
                linktext_vlan: "View vlan info"
            });
            $element.attr('title', text);
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

            // Create tooltips on mouseenter (as opposed to on click) to avoid title to be shown
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
                var $cell = event.target.nodeName === 'TD' ? $(event.target) : $(event.target).closest('td');

                if ($cell.hasClass('has-loaded')) {
                    // if for some reason the tooltip has not been created, do it now
                    if (!$cell.data('selector')) {
                        self.createTooltip($target);
                    }

                    if ($cell.hasClass('open')) {
                        self.closeAllTips();
                    } else {
                        self.openTip($cell);
                    }
                } else {
                    // If we click outside the cells, remove all tooltips
                    self.closeAllTips();
                }
            });

        },

        createTooltip: function(target) {
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
            this.closeAllTips();
            Foundation.libs.tooltip.showTip($target);
            this.addSparkline($target);
            this.openTips.push($target);
        },

        /**
         * Add sparklines to tooltips. The tooltips created by Foundation
         * tooltips can be found by following the selector on the element with
         * the listener.
         */
        addSparkline: function($target) {
            var self = this;
            var $toolTip = $('#' + $target.data('selector'));
            if ($toolTip.find('.usage-sparkline').length === 0) {
                var request = $.getJSON($target.data('url'));
                var sparkContainer = $('<div class="usage-sparkline">&nbsp;</div>');
                sparkContainer.appendTo($toolTip);

                request.done(function(response) {
                    if (response.length > 0) {
                        var data = response[0],
                            dataPoints = data.datapoints.map(function(point) {
                                return [point[1], point[0]];
                            });

                        sparkContainer.sparkline(dataPoints, {
                            tooltipFormatter: self.formatter,
                            type: 'line',
                            width: '100%'
                        });
                    } else {
                        sparkContainer.html('No data from Graphite');
                    }
                });

                request.error(function() {
                    sparkContainer.html('Error fetching data from Graphite');
                });
            }
        },

        /**
         * Formatter for sparkline tooltip
         */
        formatter: function(sparkline, options, fields) {
            var date = new Date(fields.x * 1000).toLocaleString();
            return '<div class="jqsfield"><span style="color:' + fields.color + '">&#9679</span> ' + fields.y + '<br/> ' + date + '</div>';
        }

    };


    // Initialize stuff on page load
    $(function() {
        var $container = $('#subnet-matrix');
        if ($container.length) {
            var tooltipHandler = new TooltipHandler($container);
            tooltipHandler.addListeners();
            var fetcher = new UsageFetcher($container);
            fetcher.fetchUsage();
        }
    });


});
