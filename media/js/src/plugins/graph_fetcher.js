define(['libs/jquery'], function () {

    function GraphFetcher(graphurl, metric, handler, target) {
        this.graphurl = graphurl;
        this.metric = metric;
        this.handler = handler;
        this.target = target;
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
            console.log("Fetching graph");
            var self = this;
            timeframe = timeframe ? timeframe : '1w';
            $.get(this.graphurl + this.metric, {timeframe: timeframe}, function (data) {
                self.updateImage(data);
                self.selectButton(timeframe);
            });
        },
        updateImage: function (data) {
            console.log('Updating image');
            console.log(data);
            if (this.image) {
                this.image.attr('src', data);
            } else {
                this.image = $('<img/>').attr('src', data);
                this.image.appendTo(this.target);
                this.target.show();
                this.rebindListener();
            }
        },
        rebindListener: function () {
            console.log('Rebinding listener');
            var self = this;
            this.handler.unbind('click');
            this.handler.click(function () {
                self.target.toggle();
            });
        },
        selectButton: function(timeframe) {
            $('button', this.target).each(function (index, element) {
                $(element).removeClass('button-selected');
            });
            $('button.graph-button-' + timeframe, this.target).addClass('button-selected');
        }

    };

    return GraphFetcher;

});
