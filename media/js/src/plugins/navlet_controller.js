define(['libs/jquery', 'libs/spin.min'], function () {

    /*
    * Controller for a specific Navlet
    *
    * container: A wrapper for all Navlets containing data-attributes useful for the navlet
    * renderNode: In case of columns or other structures, this is the node the navlet should render in
    * navlet: An object containing the id for the navlet and the url to display it
    *
    */

    var NavletController = function (container, renderNode, navlet) {
        this.container = container;    // Navlet container
        this.renderNode = renderNode;  // The column this navlet should render in
        this.navlet = navlet;          // Object containing navlet information
        this.spinner = new Spinner();  // Spinner showing on load
        this.node = this.createNode(); // The complete node for this navlet
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
            /* Renders the navlet and inserts the html */
            var that = this;

            if (mode === undefined) {
                mode = 'VIEW';
            }

            var request = $.ajax({
                url: this.navlet.url,
                data: {'mode': mode},
                beforeSend: function () {
                    that.spinner.spin(that.node.get(0));
                }
            });
            request.done(function (html) {
                that.node.html(html);
                that.applyListeners();
                that.node.foundation();  // Initialize Foundation script on this node
                var preferences = that.navlet.preferences;
                if (preferences && preferences.refresh_interval) {
                    setTimeout(function () {
                        that.renderNavlet.call(that);
                    }, preferences.refresh_interval);
                }
            });
            request.fail(function (jqxhr, textStatus, errorThrown) {
                that.displayError('Could not load Navlet');
            });
            request.always(function () {
                that.spinner.stop();
            });

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
                    request.fail(function () {
                        that.displayError('Could not remove Navlet, maybe it has become self aware...!');
                    });
                    request.done(function () {
                        that.node.remove();
                    });
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
                    request.fail(function (jqxhr) {
                        that.displayError('Could not save changes: ' + jqxhr.responseText);
                    });
                });
            }
        },
        displayError: function (errorMessage) {
            this.getOrCreateErrorElement().text(errorMessage);
        },
        getOrCreateErrorElement: function () {
            var $element = this.node.find('.alert-box.alert'),
                $header = this.node.find('.subheader');

            if (!$element.length) {
                $element = $('<span class="alert-box alert"/>');
                if ($header.length) {
                    $element.insertAfter($header);
                } else {
                    $element.appendTo(this.node);
                }
            }

            return $element;
        }

    };

    return NavletController;
});
