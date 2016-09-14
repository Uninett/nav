define(function(require, exports, module) {

    var _sparkline = require("libs/jquery.sparkline");

    function PduController($navlet, dataUrl) {
        this.$navlet = $navlet;
        this.dataUrl = dataUrl;
        this.update();
    }

    PduController.prototype.update = function() {
        var self = this;
        $.get(this.dataUrl, function(response) {
            console.log(response);
            _.each(response, function(data) {
                var point = _.find(data.datapoints.reverse(), function(datapoint) {
                    return datapoint[0] !== null;
                });
                var load = point[0];
                var limit = 10;
                var config = {
                    type: 'bullet',
                    tooltipFormat: '{{value}} Ampere'
                };

                if (strEndsWith(data.target), '1') {
                    limit = limit * 2;
                }

                self.$navlet.find('[data-metric="' + data.target + '"]').sparkline([limit, load, limit], config);
            });
        });
    };

    function strEndsWith(str, suffix) {
        return str.match(suffix+"$")==suffix;
    }

    module.exports = PduController;

});
