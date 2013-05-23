define(['plugins/navlet_controller', 'libs/jquery'], function (NavletController) {
    /* Controller for loading and laying out the navlets, and adding buttons for manipulating the navlets */

    function NavletsController(node) {
        this.container = node;
        this.createLayout();

        this.fetch_navlets_url = this.container.attr('data-list-navlets');
        this.save_ordering_url = this.container.attr('data-save-order-url');

        this.activateOrderingButton = $('#navlet-ordering-activate');
        this.saveOrderingButton = $('#navlet-ordering-save');

        this.navletSelector = '.navlet';
        this.sorterSelector = '.navletColumn';

        this.fetchNavlets();
    }

    NavletsController.prototype = {
        createLayout: function () {
            var $row = $('<div class="row"/>').appendTo(this.container);
            this.column1 = $('<div class="large-6 column navletColumn"/>').appendTo($row);
            this.column2 = $('<div class="large-6 column navletColumn"/>').appendTo($row);
        },
        fetchNavlets: function () {
            var that = this;
            $.getJSON(this.fetch_navlets_url, function (data) {
                var navlets = data, i, l;
                for (i = 0, l = data.length; i < l; i++) {
                    if (data[i].column === 1) {
                        new NavletController(that.container, that.column1, data[i]);
                    } else {
                        new NavletController(that.container, that.column2, data[i]);
                    }
                }
                that.addNavletOrdering();
            });
        },
        addNavletOrdering: function () {
            var that = this;

            this.container.find(this.sorterSelector).sortable({
                disabled: true,
                connectWith: '.navletColumn',
                forcePlaceholderSize: true,
                placeholder: 'highlight'
            });

            this.activateOrderingButton.click(function () {
                that.activateOrdering();
            });

            this.saveOrderingButton.click(function () {
                that.saveOrder(that.findOrder());
            });

        },
        activateOrdering: function () {
            this.getSorter().sortable('option', 'disabled', false);
            this.getNavlets().addClass('outline');
            this.activateOrderingButton.hide();
            this.saveOrderingButton.show();
        },
        findOrder: function () {
            var ordering = {column1: {}, column2: {}};
            this.getNavlets(this.column1).each(function (index, navlet) {
                ordering.column1[$(navlet).attr('data-id')] = index;
            });
            this.getNavlets(this.column2).each(function (index, navlet) {
                ordering.column2[$(navlet).attr('data-id')] = index;
            });
            return ordering;
        },
        saveOrder: function (ordering) {
            var that = this,
                jqxhr = $.post(this.save_ordering_url, JSON.stringify(ordering));

             jqxhr.done(function () {
                 that.getSorter().sortable('option', 'disabled', true);
                 that.getNavlets().removeClass('outline');
                 that.activateOrderingButton.show();
                 that.saveOrderingButton.hide();
             });
        },
        getNavlets: function (column) {
            if (column) {
                return column.find(this.navletSelector);
            } else {
                return this.container.find(this.navletSelector);
            }
        },
        getSorter: function () {
            return this.container.find(this.sorterSelector);
        }

    };

    return NavletsController;

});
