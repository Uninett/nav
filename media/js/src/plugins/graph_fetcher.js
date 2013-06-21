define(['libs/jquery'], function () {

    function GraphFetcher(graphurl, metric, handler, target) {
        this.graphurl = graphurl;
        this.metric = metric;
        this.handler = handler;
        this.target = target;

        this.addLoadGraphListener();
    }

    GraphFetcher.prototype = {
        fetchGraph: function () {
            console.log("Fetching graph");
            console.log(this.metric);
            var self = this;
            $.get(this.graphurl + this.metric, function (data) {
                console.log(data);
                var $image = $('<img/>').attr('src', data);
                $image.appendTo(self.target);
                self.rebindListener();
            });
        },
        addLoadGraphListener: function () {
            var self = this;
            this.handler.click(function () {
                self.fetchGraph();
            });
        },
        rebindListener: function () {
            var self = this;
            this.handler.unbind('click');
            this.handler.click(function () {
                self.target.toggle();
            })
        }
    };

    return GraphFetcher;

});
