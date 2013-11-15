define(['libs/jquery', 'libs/spin.min'], function () {
    /*
     * GraphFetcher (whisper-version)
     *
     * Displays graphs from whisper-files
     *
     * graphurl - url for fetching an url to an image
     * handler - the node used for interaction - displaying and hiding the graph
     * target - the target node for the graph
     *
     * Workflow:
     * Sends a request for an url using the graphurl. Creates an image,
     * appends it to the target and and sets the src = response from
     * graphurl-request. Attaches listeners to the handler for displaying
     * and hiding the graph.
     *
     */
    function GraphFetcher(graphurl, target, handler) {
        this.graphurl = graphurl;
        this.target = target;
        this.handler = handler;
        this.buttons = {'1d': 'Day', '1w': 'Week', '1mon': 'Month', '1y': 'Year'};
        this.image = false;

        this.initialize();
    }

    GraphFetcher.prototype = {
        initialize: function () {
            this.addButtons();
            this.addLoadGraphListener();
        },
        addButtons: function () {
            var headerNode = $('<div/>').appendTo(this.target);
            this.headerNode = headerNode;

            for (var key in this.buttons) {
                if (this.buttons.hasOwnProperty(key)) {
                    this.addButton(headerNode, key, this.buttons[key]);
                }
            }
        },
        addButton: function (node, timeframe, text) {
            var self = this;
            var button= $('<button />').addClass('graph-button-' + timeframe).html(text);
            button.click(function () {
                self.fetchGraph(timeframe);
            });
            button.appendTo(node);
        },
        addLoadGraphListener: function () {
            var self = this;
            this.handler.click(function () {
                self.fetchGraph();
            });
        },
        fetchGraph: function (timeframe) {
            if (this.loading) {
                // Exit if already loading a graph
                return;
            } else {
                this.loading = true;
            }

            timeframe = timeframe ? timeframe : '1w';
            var self = this,
                xhr = $.ajax(this.graphurl, {
                    data: {timeframe: timeframe},
                    beforeSend: function () {
                        self.target.show();
                        self.startSpinner();
                    }
                });
            this.handleXhr(xhr, timeframe);
        },
        handleXhr: function (xhr, timeframe) {
            var self = this;
            xhr.done(function (data) {
                self.updateImage(data);
                self.selectButton(timeframe);
            });

            xhr.always(function () {
                self.spinner.stop();
                self.loading = false;
            });
        },
        updateImage: function (data) {
            if (this.image) {
                this.image.attr('src', data);
            } else {
                this.image = $('<img/>').attr('src', data);
                this.image.appendTo(this.target);
                this.rebindListener();
            }
        },
        rebindListener: function () {
            var self = this;
            this.handler.unbind('click');
            this.handler.click(function () {
                self.target.toggle();
            });
        },
        selectButton: function(timeframe) {
            $('button', this.target).each(function () {
                $(this).removeClass('button-selected');
            });
            $('button.graph-button-' + timeframe, this.target).addClass('button-selected');
        },
        startSpinner: function () {
            if (!this.spinner) {
                this.spinner = this.createSpinner();
            }
            this.spinner.spin(this.target.get(0));
        },
        stopSpinner: function () {
            this.spinner.stop();
        },
        createSpinner: function () {
            var options = {};  // Who knows, maybe in the future?
            /* Set a minimum height on the container so that the spinner displays properly */
            this.target.css('height', '200px');
            return new Spinner(options);
        }
    };

    return GraphFetcher;

});
