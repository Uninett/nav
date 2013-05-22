define([], function () {

    /*
    * Controller for a specific Navlet
    *
    * node: The parent node for all the navlets. The navlet will be inserted here
    * navlet: An object containing the id for the navlet and the url to display it
    *
    */

    var NavletController = function (container, renderNode, navlet) {
        this.container = container;
        this.renderNode = renderNode;
        this.navlet = navlet;
        this.node = this.createNode();
        this.removeUrl = this.container.attr('data-remove-navlet');

        this.renderNavlet('VIEW');
    };

    NavletController.prototype = {
        createNode: function () {
            /* Creates the node that the navlet will loaded into */
            var $div = $('<div/>');
            $div.attr({
                'data-id': this.navlet.id,
                'class': 'navlet'
            });

            this.renderNode.append($div);
            return $div;
        },
        renderNavlet: function (mode) {
            /* Fetches the navlet and inserts the html */
            var that = this;

            var request = $.get(this.navlet.url, {'mode': mode});
            request.done(function (html) {
                that.node.html(html);
                that.applyListeners();
            });
            request.fail(this.displayError);

        },
        getModeSwitch: function () {
            return this.node.find('.navlet-mode-switch');
        },
        getRenderMode: function () {
            var modeSwitch = this.getModeSwitch(),
                mode = 'VIEW';
            if (modeSwitch.length) {
                mode = modeSwitch.attr('data-mode');
            }
            return mode;
        },
        applyListeners: function () {
            /* Applies listeners to the relevant elements */
            this.applyModeListener();
            this.applyRemoveListener();
            this.applySubmitListener();
        },
        applyModeListener: function () {
            /* Renders the navlet in the correct mode (view or edit) when clicking the switch button */
            var that = this,
                modeSwitch = this.getModeSwitch();

            if (modeSwitch.length > 0) {
                var mode = this.getRenderMode() === 'VIEW' ? 'EDIT' : 'VIEW';

                modeSwitch.click(function () {
                    that.renderNavlet(mode);
                });
            }
        },
        applyRemoveListener: function () {
            /* Removes the navlet when user clicks the remove button */
            var that = this,
                removeButton = this.node.find('.navlet-remove-button');

            removeButton.click(function () {
                if(confirm('Do you want to remove this navlet from the page?')) {
                    var request = $.post(that.removeUrl, {'navletid': that.navlet.id});
                    request.done(window.location.reload);
                    request.fail(that.displayError);
                }
            });
        },
        applySubmitListener: function () {
            if (this.getRenderMode() === 'EDIT') {
                var that = this,
                    form = this.node.find('form');

                form.submit(function (event) {
                    event.preventDefault();
                    var request = $.post(form.attr('action'), $(this).serialize());
                    request.done(function () {
                        that.renderNavlet('VIEW');
                    });
                    request.fail(that.displayError);
                });
            }
        },
        displayError: function (jqxhr, textStatus, errorThrown) {
            if (jqxhr.responseText) {
                alert(jqxhr.responseText);
            } else {
                alert(errorThrown);
            }
        }

    };

    return NavletController;
});
