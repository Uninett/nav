define([], function () {

    /*
    * Controller for a specific Navlet
    *
    * node: The parent node for all the navlets. The navlet will be inserted here
    * navlet: An object containing the id for the navlet and the url to display it
    *
    */

    var NavletController = function (node, navlet) {
        this.mainNode = node;
        this.navlet = navlet;
        this.node = this.createNode();
        this.removeUrl = this.mainNode.attr('data-remove-navlet');

        this.renderNavlet('VIEW');
    };

    NavletController.prototype = {
        createNode: function () {
            /* Creates the node that the navlet will loaded into */
            var $div = $('<div/>');
            $div.attr({
                'class': 'navlet'
            });

            this.mainNode.append($div);
            return $div;
        },
        renderNavlet: function (mode) {
            /* Fetches the navlet and inserts the html */
            var that = this;

            $.get(this.navlet.url, {'mode': mode, 'id': this.navlet.id}, function (html) {
                that.node.html(html);
                that.applyListeners();
            });

        },
        applyListeners: function () {
            /* Applies listeners to the relevant elements */
            this.applyModeListener();
            this.applyRemoveListener();
        },
        applyModeListener: function () {
            /* Renders the navlet in the correct mode (view or edit) when clicking the switch button */
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
            /* Removes the navlet when user clicks the remove button */
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
