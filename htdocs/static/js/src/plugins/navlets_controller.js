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

        this.fetchNavlets();
        this.addAddNavletListener();
    }

    NavletsController.prototype = {
        createLayout: function (container, numColumns) {
            var $row = $('<div class="row"/>').appendTo(container),
                classes = "column navletColumn " + columnsMapper[numColumns],
                columns = [];

            for(var i = 0; i < numColumns; i++) {
                columns.push($('<div>').addClass(classes).appendTo($row));
            }
            return columns;
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
                for (i = 0, l = data.length; i < l; i++) {
                    that.addNavlet(data[i]);
                }
                that.addNavletOrdering();
            });
        },
        addAddNavletListener: function () {
            var that = this;
            $('.add-user-navlet').submit(function (event) {
                event.preventDefault();
                var request = $.post($(this).attr('action'), $(this).serialize(), 'json');
                request.done(function (data) {
                    that.addNavlet(data);
                    $('#navlet-list').foundation('reveal', 'close');
                });
                request.fail(function () {
                    alert('Failed to add widget');
                });
            });
        },
        addNavlet: function (data) {
            var column = data.column > this.numColumns ? this.numColumns : data.column;
            new NavletController(this.container, this.columns[column - 1], data);
        },
        addNavletOrdering: function () {
            var that = this;

            this.container.find(this.sorterSelector).sortable({
                connectWith: '.navletColumn',
                forcePlaceholderSize: true,
                handle: '.navlet-drag-button',
                placeholder: 'highlight',
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
            $.post(this.save_ordering_url, JSON.stringify(ordering));
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
