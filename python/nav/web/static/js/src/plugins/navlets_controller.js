define(['plugins/navlet_controller'], function (NavletController) {

    /**
     * Controller for loading and laying out the navlets, and adding buttons for
     * manipulating the navlets
     */

    // What class to use for the different number of columns
    var columnsMapper = {
        '2': 'medium-6',
        '3': 'medium-4',
        '4': 'medium-3'
    };

    function NavletsController(node, columns) {
        this.container = node;
        this.numColumns = columns || 2;
        this.columns = this.createLayout(this.container, this.numColumns);

        this.fetch_navlets_url = this.container.attr('data-list-navlets');
        this.save_ordering_url = this.container.attr('data-save-order-url');

        this.navletSelector = '.navlet';
        this.sorterSelector = '.navletColumn';

        this.addContentListener();

        this.fetchNavlets();
        this.addAddNavletListener();
    }

    NavletsController.prototype = {
        createLayout: function (container, numColumns) {
            var $row = $('<div class="row"/>').appendTo(container),
                classes = "column navletColumn " + columnsMapper[numColumns],
                columns = [];

            if (this.container.hasClass('compact')) {
                $row.addClass('collapse');
            }

            for(var i = 0; i < numColumns; i++) {
                columns.push($('<div>').addClass(classes).appendTo($row));
            }
            return columns;
        },

        /** Displays an infobox when there are no widgets on a dashboard. */
        addContentListener: function() {
            var self = this;
            var message = $('<div class="alert-box info">No widgets added to this dashboard</div>');
            var messageContainer = this.container.find('.navletColumn:first');
            this.container.on('nav.navlets.fetched', function(event, meta) {
                if (meta.numNavlets === 0) {
                    messageContainer.append(message);
                }
            });
            this.container.on('nav.navlet.added', function() {
                message.detach();
            });
            this.container.on('nav.navlet.removed', function() {
                if (self.container.find('.navlet').length === 0) {
                    messageContainer.append(message);
                }
            });
        },
        fetchNavlets: function () {
            var that = this,
                request_config = {
                    cache: false, // Need to disable caching because of IE
                    dataType: 'json',
                    url: this.fetch_navlets_url
                },
                request = $.ajax(request_config);

            request.done(function (data) {
                var i, l;
                for (i = 0, l = data.items.length; i < l; i++) {
                    that.addNavlet(data.items[i]);
                }
                that.addNavletOrdering();
                that.container.trigger('nav.navlets.fetched', {numNavlets: data.items.length});
            });
        },
        addAddNavletListener: function () {
            const that = this;
            $(document).on('submit', '.add-user-navlet', function (event) {
                event.preventDefault();
                const $form = $(this);
                const request = $.post($form.attr('action'), $form.serialize(), 'json');

                request.done(function (data) {
                    that.addNavlet(data, true);
                    that.saveOrder(that.findOrder());
                    $('#navlet-list').remove();
                });

                request.fail(function () {
                    alert('Failed to add widget');
                });
            });
        },

        /**
         * Spawn a new widget on the existing dashboard.
         *
         * Triggers the event 'nav.navlet.added' on the widgets container.
         *
         * @param {object} data - metadata about the widget
         * @param {boolean} forceFirst - Force this widget to be placed in the top left corner.
         */
        addNavlet: function (data, forceFirst) {
            var column = data.column > this.numColumns ? this.numColumns : data.column;
            column = column < 1 ? 1 : column;
            new NavletController(this.container, this.columns[column - 1], data, forceFirst);
            this.container.trigger('nav.navlet.added');
        },
        addNavletOrdering: function () {
            var that = this;

            this.container.find(this.sorterSelector).sortable({
                connectWith: '.navletColumn',
                forcePlaceholderSize: true,
                handle: '.navlet-drag-button',
                placeholder: 'highlight',
                tolerance: 'pointer',
                start: function () {
                    that.getNavlets().addClass('outline');
                },
                stop: function () {
                    that.getNavlets().removeClass('outline');
                },
                update: function () {
                    that.saveOrder(that.findOrder());
                }
            });

        },
        findOrder: function () {
            var orderings = [];
            for(var i = 0; i < this.columns.length; i++) {
                var columnNavlets = {};
                this.getNavlets(this.columns[i]).each(function (index, navlet) {
                    columnNavlets[$(navlet).attr('data-id')] = index;
                });
                orderings.push(columnNavlets);
            }
            return orderings;
        },
        saveOrder: function (ordering) {
            // Get csrf token from #navlets-action-form
            const csrfToken = $('#navlets-action-form input[name="csrfmiddlewaretoken"]').val();
            $.ajax({
               url: this.save_ordering_url,
               type: 'POST',
               data: JSON.stringify(ordering),
               contentType: 'application/json',
               headers: {
                   'X-CSRFToken': csrfToken
               }
            }).fail(function() {
               console.error('Failed to save widget order');
            });
        },
        getNavlets: function (column) {
            if (column) {
                return column.find(this.navletSelector);
            } else {
                return this.container.find(this.navletSelector);
            }
        },
    };

    return NavletsController;

});
