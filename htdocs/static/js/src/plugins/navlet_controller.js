define(['libs/jquery', 'libs/spin.min'], function () {

    /*
    * Controller for a specific Navlet
    *
    * container: A wrapper for all Navlets containing data-attributes useful for the navlet
    * renderNode: In case of columns or other structures, this is the node the navlet should render in
    * navlet: An object containing the id for the navlet and the url to display it
    *
    * The controller initiates a request to the url given in the navlet object,
    * puts the result in its own node and add it to the renderNode.
    *
    * If the request fails for some reason, we need to make another request to
    * fetch the base template with the buttons and title rendered. This is
    * suboptimal, but only leads to overhead on errors.
    *
    */

    var NavletController = function (container, renderNode, navlet) {
        this.container = container;    // Navlet container
        this.renderNode = renderNode;  // The column this navlet should render in
        this.navlet = navlet;          // Object containing navlet information
        this.spinner = new Spinner();  // Spinner showing on load
        this.node = this.createNode(); // The complete node for this navlet
        this.removeUrl = this.container.attr('data-remove-navlet');           // Url to use to remove a navlet from this user
        this.baseTemplateUrl = this.container.attr('data-base-template-url'); // Url to use to fetch base template for this navlet

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

            $div.addClass(this.navlet.navlet_class);

            if (this.navlet.highlight) {
                $div.addClass('colorblock-navlet');
            }

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
                that.handleSuccessfulRequest(html, mode);
            });
            request.fail(function (jqxhr, textStatus, errorThrown) {
                that.handleErrorRequest(jqxhr);
            });
            request.always(function () {
                that.spinner.stop();
            });

        },
        handleSuccessfulRequest: function (html, mode) {
            this.node.html(html);
            this.applyListeners();
            this.addReloader(mode);
        },
        handleErrorRequest: function (jqxhr) {
            /*
             * Fetch base template for this navlet, display that and error
             */
            var that = this,
                request = $.get(this.baseTemplateUrl, {id: this.navlet.id});
            request.done(function (html) {
                that.node.html(html);
                that.applyListeners();
                if (jqxhr.status === 401 || jqxhr.status === 403) {
                    that.displayError('Not allowed');
                } else {
                    that.displayError('Could not load widget');
                }
            });
            request.fail(function () {
                that.displayError('Could not load widget');
            });
        },
        addReloader: function (mode) {
            /*
             * Reload periodically based on preferences
             * Remember to stop refreshing on edit
             */
            var that = this,
                preferences = this.navlet.preferences,
                image = this.node.find('img[data-image-reload]'),
                imageUrl = image.attr('src');

            if (mode === 'VIEW' && preferences && preferences.refresh_interval) {
                /* If this is a reload of image only */
                if (this.navlet.image_reload) {
                    this.refresh = setInterval(function () {
                        /* The random part is courtesy IE */
                        image.attr('src', imageUrl + '&bust=' + Math.random());
                    }, preferences.refresh_interval);
                } else {
                    this.refresh = setTimeout(function () {
                        that.renderNavlet.call(that);
                    }, preferences.refresh_interval);
                }
            } else if (mode === 'EDIT' && this.refresh) {
                clearTimeout(this.refresh);
            }
        },
        getModeSwitch: function () {
            /* Return edit-button */
            return this.node.find('.navlet-mode-switch');
        },
        getRenderMode: function () {
            /* Return mode based on edit-button. If it does not exist return VIEW */
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
//            this.applyReloadListener();
            this.applySubmitListener();
            if (this.navlet.is_title_editable) {
                this.applyTitleListener();
            }
            this.applyOnRenderedListener();
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
                if(confirm('Do you want to remove this widget from the page?')) {
                    var request = $.post(that.removeUrl, {'navletid': that.navlet.id});
                    request.fail(function () {
                        that.displayError('Could not remove widget, maybe it has become self aware...!');
                    });
                    request.done(function () {
                        that.node.remove();
                    });
                }
            });
        },
        applyReloadListener: function () {
            var that = this,
                reloadButton = this.node.find('.navlet-reload-button');
            reloadButton.on('click', function () {
                that.renderNavlet();
            });
        },
        applySubmitListener: function () {
            /*
             * Make sure a form in edit-mode is submitted by ajax, so that the
             * page does not reload.
             *
             * Preferences may be returned, handle and store them
             */
            if (this.getRenderMode() === 'EDIT') {
                var that = this,
                    form = this.node.find('form');

                form.submit(function (event) {
                    event.preventDefault();
                    var request = $.post(form.attr('action'), $(this).serialize());
                    request.done(function (data) {
                        // Update preferences if they are sent back from controller
                        if (data) {
                            that.navlet.preferences = JSON.parse(data);
                        }
                        that.renderNavlet('VIEW');
                    });
                    request.fail(function (jqxhr) {
                        that.displayError('Could not save changes: ' + jqxhr.responseText);
                    });
                });
            }
        },
        applyTitleListener: function () {
            /* Feel free to refactor this mess */
            var self = this;
            this.node.find('.subheader').click(function () {
                var $header = $(this),
                    $container = $($header.parents('.title-container').get(0)),
                    $input = $('<input type="text">').val($header.find('.navlet-title').text());

                $header.hide();
                $container.append($input);
                $input.on('keydown', function (event) {
                    if (event.which === 13) {
                        var request = $.post($header.attr('data-set-title'),
                            {
                                'id': self.navlet.id,
                                'preferences': JSON.stringify({
                                    'title': $input.val()
                                })
                            }
                        );
                        request.done(function () {
                            $header.find('.navlet-title').text($input.val());
                        });
                        request.error(function () {
                            alert("The Oompa Loompas didn't want to change the title (an error occured) - sorry!");
                        });
                        request.always(function () {
                            $input.remove();
                            $header.show();
                        });
                    }
                });
            });
        },
        applyOnRenderedListener: function () {
            this.container.trigger('navlet-rendered', [this.node]);
        },
        displayError: function (errorMessage) {
            this.getOrCreateErrorElement().text(errorMessage);
        },
        getOrCreateErrorElement: function () {
            /* If error element is already created, return existing element */
            var $element = this.node.find('.alert-box.alert');

            if (!$element.length) {
                $element = $('<span class="alert-box alert"/>');
                $element.appendTo(this.node);
            }

            return $element;
        }

    };

    return NavletController;
});
