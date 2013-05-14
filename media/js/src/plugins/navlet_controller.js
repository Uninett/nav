define([], function () {

    var NavletController = function (node, navlet) {
        this.mainNode = node;
        this.navlet = navlet;
        this.node = this.createNode();

        this.renderNavlet('VIEW');
    };

    NavletController.prototype = {
        renderNavlet: function (mode) {
            var that = this;

            $.get(this.navlet.url, {'mode': mode}, function (html) {
                that.node.html(html);
                that.applyListeners();
            });

        },
        createNode: function () {
            var $div = $('<div/>');
            $div.attr({
                'data-id': this.navlet.id,
                'class': 'navlet'
            });

            this.mainNode.append($div);
            return $div;
        },
        applyListeners: function () {
            console.log('Applying listeners to ' + this.navlet.id);
            var that = this,
                modeSwitch = this.node.find('.navlet-mode-switch');

            if (modeSwitch.length > 0) {
                var mode = modeSwitch.attr('data-mode') === 'VIEW' ? 'EDIT' : 'VIEW';
                modeSwitch.click(function () {
                    that.renderNavlet(mode);
                });
            }
        }

    };

    return NavletController;
});
