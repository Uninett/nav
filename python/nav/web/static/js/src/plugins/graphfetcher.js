define([
    'plugins/rickshaw_graph',
    'libs/urijs/URI',
    'libs/spin.min'
], function (RickshawGraph, URI, Spinner) {
    /*
     * GraphFetcher
     *
     * Automatically loads graphite graphs based on class attributes.
     *
     * See 'graphfetcher_controller' for global controls.
     *
     * Every graph needs the following:
     * class='graphitegraph'
     * data-url: The url of the controller returning the graph image
     *   (you need to write this controller). GraphFetcher adds a 'timeframe'
     *   parameter indicating timeframe. Valid timeframes are in the buttons
     *   list.
     * data-handler-id: If you have a button or something that shows the
     *   graph, set this to the id of that element. Otherwise the graph is
     *   loaded on page load.
     *
     * NB: Expected icon for indicating expandable is 'fa-chevron-right'
     *
     * config options:
     * - hideAddGraphButton: Hides the button for adding graph as widget
     * - linkTarget: if set will wrap a link around image (only valid if graph
         is an image)
     */

    function GraphFetcher(node, urls, config) {
        this.checkInput(node, urls);
        this.node = node;
        this.graphContainer = this.node.find('.rickshaw-container')[0];
        this.urls = urls.split(';');
        this.lastUrlIndex = -1;
        this.urlIndex = 0;  // Index of this.urls
        this.config = _.extend({}, config);

        this.buttons = {
            'day': 'Day',
            'week': 'Week',
            'month': 'Month',
            'year': 'Year'
        };
        this.lastTimeFrame = '';
        this.timeframe = 'day';
        this.isOpen = false;
        this.spinner = this.createSpinner();

        this.isInitialized = false;
        var handlerId = this.node.attr('data-handler-id');
        if (handlerId) {
            this.handler = $('#' + handlerId);
            this.icon = this.handler.find('i');
            this.addToggleHandler();
        } else {
            this.init();
        }
        return this;
    }

    GraphFetcher.prototype = {
        init: function () {
            if (!this.config.hideTimeIntervalButtons) {
                this.addButtons();
            }
            this.loadGraph();
            this.isInitialized = true;
        },
        addToggleHandler: function () {
            var self = this;
            $(this.handler).click(function () {
                if (self.node.is(':visible')) {
                    self.close();
                } else {
                    self.open();
                }
            });
        },
        close: function () {
            this.isOpen = false;
            this.node.hide();
            this.icon.removeClass('fa-chevron-down').addClass('fa-chevron-right');
        },
        open: function () {
            if (!this.isInitialized) {
                this.init();
            }
            if (this.shouldReloadGraph()) {
                this.loadGraph();
            }
            this.node.show();
            this.isOpen = true;
            this.icon.removeClass('fa-chevron-right').addClass('fa-chevron-down');
        },
        shouldReloadGraph: function () {
            return (this.lastTimeFrame !== this.timeframe) || (this.lastUrlIndex !== this.urlIndex);
        },
        changeUrlIndex: function (index) {
            if (this.urls.length > index) {
                this.urlIndex = index;
            }
        },
        checkInput: function (node, url) {
            if (!(node instanceof jQuery && node.length)) {
                throw new Error('Need a valid node to attach to');
            }
            if (typeof url !== "string") {
                throw new Error('Need a string as url');
            }
        },
        addButtons: function () {
            var headerNode = $('<div>').appendTo(this.node);
            this.headerNode = headerNode;

            for (var key in this.buttons) {
                if (this.buttons.hasOwnProperty(key)) {
                    this.addButton(headerNode, key, this.buttons[key]);
                }
            }
            if (this.graphContainer) {
                this.appendToggleTrendCheckbox();
            }
            if (!this.config.hideAddGraphButton) {
                this.appendAddGraphButton();
            }
        },
        addButton: function (node, timeframe, text) {
            var that = this;
            var button = $('<button>').addClass('tiny secondary graph-button-' + timeframe).html(text);
            button.click(function () {
                that.timeframe = timeframe;
                that.loadGraph();
            });
            button.appendTo(node);
        },
        appendAddGraphButton: function () {
            var self = this,
                button = $('<button>').addClass('tiny secondary right').text('Add graph to dashboard');
            button.click(function () {
                /* Image url is a redirect to graphite. Fetch proxy url and use
                 that as preference for graph widget */
                var url = new URI(self.generatedURL).removeQuery('format', ''),
                    headRequest = $.ajax(url.toString(), {'type': 'HEAD'});
                headRequest.done(function (data, status, xhr) {
                    var proxyUrl = xhr.getResponseHeader('X-Where-Am-I');
                    if (proxyUrl) {
                        var request = $.post(NAV.addGraphWidgetUrl,
                            {
                                'url': new URI(proxyUrl).removeQuery('format').toString(),
                                'target': window.location.pathname + window.location.hash
                            });
                        request.done(function () {
                            button.removeClass('secondary').addClass('success');
                        });
                        request.fail(function () {
                            button.removeClass('secondary').addClass('alert');
                        });
                    }
                });
            });
            this.headerNode.append(button);
        },
        appendToggleTrendCheckbox: function () {
            this.trends = $('<input type="checkbox">');
            var trendLabel = $('<label>').html('Show trends ').css({
                display: 'inline-block',
                'margin-left': '1em'
            });
            trendLabel.append(this.trends);
            this.headerNode.append(trendLabel);
            trendLabel.change(this.loadGraph.bind(this));
        },
        selectButton: function () {
            $('button', this.headerNode).each(function (index, element) {
                $(element).removeClass('active');
            });
            this.node.find('button.graph-button-' + this.timeframe).addClass('active');
        },
        loadGraph: function () {
            this.lastTimeFrame = this.timeframe;
            this.lastUrlIndex = this.urlIndex;
            this.displayGraph(this.getUrl());
            this.selectButton();
        },
        displayGraph: function (url) {
            var self = this;

            if (!this.graphContainer) {
                // If we have no container, assume old loading with images.
                var image = new Image();
                image.src = url;
                image.onload = function () {
                    self.node.find('img, a').remove();
                    self.node.prepend(image);
                    if (self.config.linkTarget) {
                        var link = $('<a>').attr('href', self.config.linkTarget);
                        self.node.find('img').wrap(link);
                    }
                };
                image.onerror = function () {
                    self.node.find('img').remove();
                    self.node.append("<span class='alert-box alert'>Error loading image</span>");
                };
            } else {
                $.get(url, function (data) {
                    self.rickshawgraph = self.getMin(data) < 0 ?
                                         new RickshawGraph(self.graphContainer, data, url, 'auto'):
                                         new RickshawGraph(self.graphContainer, data, url);
                });
            }
        },

        /**
         * Find minimum value for a dataset from Graphite
         */
        getMin: function(data) {
            return _.min(data.map(function(d) {
                return _.min(
                    d.datapoints.filter(function(point) {
                        return point[0] !== null;
                    }).map(function(point) {
                        return point[0];
                    }));
            }));
        },

        /**
         * We expect the urls to be urls to graphite. This means that they
         * should have parameters specifiying how to draw the graph.
         */
        getUrl: function () {
            var self = this;
            var url = this.urls[this.urlIndex];
            var uri = new URI(url);
            var addTimeShift = this.graphContainer && this.trends.is(':checked');

            if (url.indexOf('?') >= 0) {
                // If we have timeframe buttons use those for interval
                // If we don't have buttons use 'from'-parameter
                // If we have neither use default timeframe
                var interval;
                if (this.config.hideTimeIntervalButtons && uri.hasQuery('from')) {
                    interval = uri.query(true).from;
                } else {
                    interval = '-1' + this.timeframe;
                }

                uri.setQuery({
                    from: interval,
                    width: this.node.width()
                });

                if (addTimeShift) {
                    var targets = [].concat(uri.query(true).target);  // target is either list or string
                    uri.addQuery('target', targets.map(function (target) {
                        var timeshiftCall = 'timeShift(' + target + ',"' + interval + '")';
                        var targetAlias = getSeriesName(target) + ' (' + getTimeDescription(self.timeframe) + ')';
                        return 'alias(' + timeshiftCall + ', "' + targetAlias + '")';
                    }));
                }
            } else {
                uri.setQuery('timeframe', this.timeframe);
            }

            var generatedURL = uri.toString();
            this.generatedURL = generatedURL;
            return generatedURL;
        },

        createSpinner: function () {
            var options = {};  // Who knows, maybe in the future?
            return new Spinner(options);
        }
    };

    /**
     * @param {string} timeframe - Timeframe to map from */
    function getTimeDescription(timeframe) {
        var mappings = {
            'd': 'day',
            'w': 'week',
            'm': 'month',
            'y': 'year'
        };

        for (var time in mappings) {
            if (mappings.hasOwnProperty(time)) {
                if (timeframe.substr(0, 1) === time) {
                    return '1 ' + mappings[time] + ' ago';
                }
            }
        }
    }

    /** Assume optimistically that alias is always the last wrapped function */
    function getSeriesName(target) {
        if (target.match(/alias/)) {
            var parts = target.split(',');
            return parts[parts.length - 1].replace(/[")]/g, '');
        }
        return target;
    }

    return GraphFetcher;

});
