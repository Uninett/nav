define(['libs/jquery', 'libs/spin.min'], function () {
    /*
     * GraphFetcher
     *
     * Automatically loads graphite graphs based on class attributes.
     *
     * The graphs need a container element with the class
     * 'nav-metrics-container'
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
     * Example:
     * <div class='nav-metrics-container'>
     *   <div class="graphitegraph" data-url="{% url interface-counter-graph port.id 'Octets' %}"></div>
     *   <div class="graphitegraph" data-url="{% url interface-counter-graph port.id 'Octets' %}"></div>
     * </div>
     *
     * You can create buttons inside 'nav-metrics-controller' to open and
     * close all graphs. These need the class 'all-graph-opener' and
     * 'all-graph-closer' respectively.
     *
     * NB: Expected icon for indicating exxpandable is 'fa-toggle-right'
     */

    $(function () {
        $('.nav-metrics-container').each(function (index, element) {
            var $parent = $(element),
                graphs = [];

            $parent.find('.graphitegraph').each(function () {
                var $node = $(this);
                try {
                    graphs.push(new GraphFetcher($node, $node.attr('data-url')));
                } catch (error) {
                    console.log('Error initializing graphloader');
                }
            });

            /* Add listeners for opening and closing all graphs */
            $parent.find('.all-graph-opener').click(function () {
                for (var i=0, l=graphs.length; i<l; i++) {
                    graphs[i].open();
                }
            });
            $parent.find('.all-graph-closer').click(function () {
                for (var i=0, l=graphs.length; i<l; i++) {
                    graphs[i].close();
                }
            });
        });
    });

    function GraphFetcher(node, url) {
        this.checkInput(node, url);
        this.node = node;
        this.url = url;

        this.buttons = {'day': 'Day', 'week': 'Week', 'month': 'Month', 'year': 'Year'};
        this.spinner = this.createSpinner();

        this.isInitialized = false;
        var handlerId = this.node.attr('data-handler-id');
        if (handlerId) {
            var self = this;
            this.handler = $('#' + handlerId);
            this.icon = this.handler.find('i');
            this.handler.one('click', function () {
                self.open();
            });
        } else {
            this.init();
        }
        return this;
    }

    GraphFetcher.prototype = {
        init: function () {
            this.addButtons();
            this.loadGraph('day');
            var self = this;
            if (this.handler) {
                $(this.handler).click(function () {
                    if (self.node.is(':visible')) {
                        self.close();
                    } else {
                        self.open();
                    }
                });
            }
            this.isInitialized = true;
        },
        close: function () {
            this.node.hide();
            this.icon.removeClass('fa-toggle-down').addClass('fa-toggle-right');
        },
        open: function () {
            if (!this.isInitialized) {
                this.init();
            }

            this.node.show();
            this.icon.removeClass('fa-toggle-right').addClass('fa-toggle-down');
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
        },
        addButton: function (node, timeframe, text) {
            var that = this;
            var button = $('<button>').addClass('tiny secondary graph-button-' + timeframe).html(text);
            button.click(function () {
                that.loadGraph(timeframe);
            });
            button.appendTo(node);
        },
        selectButton: function(timeframe) {
            $('button', this.headerNode).each(function (index, element) {
                $(element).removeClass('active');
            });
            $('button.graph-button-' + timeframe, this.node).addClass('active');
        },
        loadGraph: function (timeframe) {
            this.displayGraph(this.getUrl(timeframe));
            this.selectButton(timeframe);
        },
        displayGraph: function (url) {
            var self = this;
            var image = new Image();
            image.src = url;
            image.onload = function () {
                self.node.find('img').remove();
                self.node.append(image);
            };
            image.onerror = function () {
                self.node.find('img').remove();
                self.node.append("<span class='alert-box alert'>Error loading image</span>");
            };
        },
        getUrl: function (timeframe) {
            var separator = '?';
            if (this.url.indexOf('?') >= 0) {
                separator = '&';
            }
            return this.url + separator + 'timeframe=' + timeframe;
        },
        createSpinner: function () {
            var options = {};  // Who knows, maybe in the future?
            /* Set a minimum height on the container so that the spinner displays properly */
            this.node.css('min-height', '100px');
            return new Spinner(options);
        }
    };

    return GraphFetcher;

});
