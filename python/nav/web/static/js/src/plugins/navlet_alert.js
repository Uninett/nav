define((require, exports, module) => {

    const DEFAULT_OPTIONS ={
        alertType: '',
        dataUrl: '',
        onState: null,
        onMessage: 'No on message provided',
        offMessage: 'No off message provided'
    }

    function AlertController($navlet, options) {
        this.$navlet = $navlet;
        this.$alertBox = $navlet.find('.alert-box');
        this.$timestamp = $navlet.find('.alert-update-timestamp span');
        this.options = {...DEFAULT_OPTIONS, ...options};
        this.text = {
         on: options.onMessage,
         off: options.offMessage,
         unknown: 'N/A'
        };
        this.alertType = options.alertType;
        this.isDestroyed = false;

        this.update();
        this.refreshHandler = this.update.bind(this);
        this.cleanupHandler = this.cleanup.bind(this);
        $navlet.on('refresh', this.refreshHandler);
        $navlet.on('htmx:beforeSwap', this.cleanupHandler);
    }

    AlertController.prototype.cleanup = function() {
        if (this.isDestroyed) return;
        this.$navlet.off('refresh', this.refreshHandler);
        this.$navlet.off('htmx:beforeSwap', this.cleanupHandler);
        this.isDestroyed = true;
    }

    AlertController.prototype.feedBack = function(text, klass) {
        this.$alertBox.attr('class', 'alert-box with-icon');
        if (klass) {
         this.$alertBox.addClass(klass);
        }
        this.$alertBox.html(text);
    }

    AlertController.prototype.update = function() {
        if (this.isDestroyed) return;
        const request = $.get(this.options.dataUrl);

        request.done((data) => {
         if (!data || data.length === 0) {
             this.feedBack('<strong>Got no data from Graphite</strong> - perhaps the metric name is wrong?');
             return;
         }

         if (!data[0]?.datapoints) {
             this.feedBack('<strong>Got invalid data from Graphite</strong>');
             return;
         }

         const datapoints = data[0].datapoints.reverse();

         this.$timestamp.text('N/A');

         for (let i=0; i<datapoints.length; i++) {
             const value = datapoints[i][0];
             const epoch = datapoints[i][1];
             if (value !== null) {
                 if (value === this.state.onState) {
                     this.feedBack(this.text.on, this.alertType);
                 } else {
                     this.feedBack(this.text.off, 'success');
                 }
                 this.$timestamp.text(new Date(epoch * 1000).toLocaleString());
                 break;
             }
             if (i >= 3) {
                 this.feedBack(this.text.unknown);
             }
         }
        });

        // Very basic error handling
        request.fail((jqXhr, textStatus, errorThrown) => {
         this.feedBack(['<strong>Error updating widget:</strong>', jqXhr.status, jqXhr.statusText].join(' '));
        });
    }

    module.exports = AlertController;
});
