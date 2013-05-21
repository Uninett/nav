define(['plugins/navlet_controller', 'libs/jquery'], function (NavletController) {
    /* Controller for loading and laying out the navlets, and adding buttons for manipulating the navlets */

    function NavletsController(node) {
        this.container = node;
        this.fetch_navlets_url = this.container.attr('data-list-navlets');
        this.save_ordering_url = this.container.attr('data-save-order-url');

        this.activateOrderingButton = $('#navlet-ordering-activate');
        this.saveOrderingButton = $('#navlet-ordering-save');

        this.navletSelector = '.navlet';

        this.fetchNavlets();
    }

    NavletsController.prototype = {
        fetchNavlets: function () {
            var that = this;
            $.getJSON(this.fetch_navlets_url, function (data) {
                var navlets = data, i, l;
                for (i = 0, l = data.length; i < l; i++) {
                    var controller = new NavletController(that.container, data[i]);
                }
                that.addNavletOrdering();
            });
        },
        addNavletOrdering: function () {
            var that = this;

            this.container.sortable({
                'disabled': true
            });

            this.activateOrderingButton.click(function () {
                that.activateOrdering();
            });

            this.saveOrderingButton.click(function () {
                that.saveOrder(that.findOrder());
            });

        },
        activateOrdering: function () {
            this.container.sortable('option', 'disabled', false);
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
