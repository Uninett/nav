define([], function () {

    var NavletController = function (node, navlet) {
        this.mainNode = node;
        this.navlet = navlet;
        this.node = this.createNode();
        this.removeUrl = this.mainNode.attr('data-remove-navlet');

        this.renderNavlet('VIEW');
    };

    NavletController.prototype = {
        createNode: function () {
            var $div = $('<div/>');
            $div.attr({
                'class': 'navlet'
            });

            this.mainNode.append($div);
            return $div;
        },
        renderNavlet: function (mode) {
            var that = this;

            $.get(this.navlet.url, {'mode': mode, 'id': this.navlet.id}, function (html) {
                that.node.html(html);
                that.applyListeners();
            });

        },
        applyListeners: function () {
            console.log('Applying listeners to ' + this.navlet.id);
            this.applyModeListener();
            this.applyRemoveListener();
        },
        applyModeListener: function () {
            var that = this,
                modeSwitch = this.node.find('.navlet-mode-switch');

            if (modeSwitch.length > 0) {
                var mode = modeSwitch.attr('data-mode') === 'VIEW' ? 'EDIT' : 'VIEW';
                modeSwitch.click(function () {
                    that.renderNavlet(mode);
                });
            }
        },
        applyRemoveListener: function () {
            var that = this,
                removeButton = this.node.find('.navlet-remove-button'),
                url = this.mainNode.attr('data-remove-navlet');

            removeButton.click(function () {
                if(confirm('Do you want to remove this navlet from the page?')) {
                    $.post(that.removeUrl, {'navletid': that.navlet.id}, function () {
                        window.location.reload();
                    });
                }
            });

        }

    };

    return NavletController;
});
