define(['libs/jquery', 'libs/spin.min'], function () {
    /*
     * GraphFetcher
     *
     * Usage: new GraphFetcher(node, url, [config])
     *
     * node - jQuery element to work in
     * url - url to use when fetching graph-url
     * config - object containing options. (currently only image title)
     *
     * NAV's rrdgrapher returns an url when creating a graph. GraphFetcher
     * fetches that url with ajax, creates an image and puts the url as source
     *
     * In addition GraphFetcher adds some parameters to the request that may
     * be used to modify the graph.
     *
    */

    function GraphFetcher(node, url, config) {
        this.checkInput(node, url);
        this.node = node;
        this.url = url;
        this.config = config;

        this.buttons = {'day': 'Day', 'week': 'Week', 'month': 'Month', 'year': 'Year'};
        this.spinner = this.createSpinner();

        this.addButtons();
        this.loadGraph('day');
    }

    GraphFetcher.prototype = {
        checkInput: function (node, url) {
            if (!(node instanceof jQuery && node.length)) {
                throw new Error('Need a valid node to attach to');
            }
            if (!(typeof url === "string")) {
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
            var button= $('<button />').addClass('tiny secondary graph-button-' + timeframe).html(text);
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
            var that = this;
            var requestData = {'timeframe': timeframe};
            var jqxhr = $.ajax(this.url, {
                data: requestData,
                beforeSend: function () {
                    that.spinner.spin(that.node.get(0));
                }
            });
            this.handleXhr(jqxhr, requestData);
        },
        displayGraph: function (url) {
            var title = this.config.title || '';
            var attrs = {
                'src': url,
                'title': title
            };

            if ($('img', this.node).length > 0) {
                $('img', this.node).attr('src', url);
            } else {
                $('<img/>').attr(attrs).appendTo(this.node);
            }
        },
        handleXhr: function (xhr, requestData) {
            var that = this;
            xhr.fail(function () {
                if (!$('span.error', that.node).length) {
                    $('<span class="error"/>').text('Failed to load graph').appendTo(that.node);
                }
            });
            xhr.done(function (data) {
                that.displayGraph(data.url);
                that.selectButton(requestData.timeframe);
                $('span.error', that).remove();
            });
            xhr.always(function () {
                if (xhr.status != 503) {
                    that.node.show();
                }
                that.spinner.stop();
            });
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
