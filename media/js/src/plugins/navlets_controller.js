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
                    if (i % 2 === 0) {
                        new NavletController(that.column1, data[i]);
                    } else {
                        new NavletController(that.column2, data[i]);
                    }
                }
                that.addNavletOrdering();
            });
        },
        addNavletOrdering: function () {
            var that = this;

            this.container.find(this.sorterSelector).sortable({
                disabled: true,
                connectWith: '.navletColumn'
            });

            this.activateOrderingButton.click(function () {
                that.activateOrdering();
            });

            this.saveOrderingButton.click(function () {
                that.saveOrder(that.findOrder());
            });

        },
        activateOrdering: function () {
            this.container.find(this.sorterSelector).sortable('option', 'disabled', false);
            this.getNavlets().addClass('outline');
            this.activateOrderingButton.hide();
            this.saveOrderingButton.show();
        },
        findOrder: function () {
            var ordering = {};
            this.getNavlets().each(function (index, navlet) {
                ordering[$(navlet).attr('data-id')] = index;
            });
            return ordering;
        },
        saveOrder: function (ordering) {
            var that = this;
            $.post(this.save_ordering_url, ordering, function () {
                that.container.sortable('option', 'disabled', true);
                that.getNavlets().removeClass('outline');
                that.activateOrderingButton.show();
                that.saveOrderingButton.hide();
            });
        },
        getNavlets: function () {
            return this.container.find(this.navletSelector);
        }

    };

    return NavletsController;

});
