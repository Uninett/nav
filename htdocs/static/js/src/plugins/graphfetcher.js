define(['libs/jquery', 'libs/spin.min'], function () {
    /*
     * GraphFetcher
     *
     * Automatically loads graphite graphs based on class attributes.
     *
     * In the template set the following attributes on the element that the
     * graph should load in:
     *
     * class='graphitegraph'
     * data-url: The url of the controller returning the graph image
     *   (you need to write this controller). GraphFetcher adds a 'timeframe'
     *   parameter indicating timeframe. Valid timeframes are in the buttons
     *   list.
     * data-handler-id: If you have a button or something that shows the
     *   graph, set this to the id of that element. Otherwise the graph is
     *   loaded on page load.
     *
     */

    $(function () {
        $('.graphitegraph').each(function () {
            var $node = $(this);
            try {
                new GraphFetcher($node, $node.attr('data-url'));
            } catch (error) {
                console.log('Error initializing graphloader');
            }
        });
    });

    function GraphFetcher(node, url) {
        this.checkInput(node, url);
        this.node = node;
        this.url = url;

        this.buttons = {'day': 'Day', 'week': 'Week', 'month': 'Month', 'year': 'Year'};
        this.spinner = this.createSpinner();

        var handlerId = this.node.attr('data-handler-id');
        if (handlerId) {
            var self = this;
            this.handler = $('#' + handlerId);
            this.handler.one('click', function () {
                self.init();
                self.node.show();
            });
        } else {
            this.init();
        }

    }

    GraphFetcher.prototype = {
        init: function () {
            this.addButtons();
            this.loadGraph('day');
            var self = this;
            if (this.handler) {
                $(this.handler).click(function () {
                    self.node.toggle();
                });
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
