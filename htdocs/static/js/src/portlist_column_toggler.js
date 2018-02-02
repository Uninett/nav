define([], function() {

    /** Toggle visibility of the buttons for toggling columns */
    function addContainerToggler($toggler, $toggleTarget) {
        $toggler.on('click', function() {
            $toggleTarget.slideToggle(function() {
                $toggler.find('i').toggleClass('fa-caret-right fa-caret-down');
            });
        });
    }

    /** Create a toggler for each th in the table */
    function createColumnTogglers(table, $container) {
        var $buttonList = $container.find('ul');
        table.columns().every(function() {
            var klass = this.visible() ? '': 'disabled';
            var $switcher = $('<li><div class="button tiny ' + klass + '">' + this.header().innerHTML + '</div></li>');
            $buttonList.append($switcher);
        });

        $buttonList.on('click', function(e) {
            var index = $buttonList.find('li').index($(e.target).closest('li'));
            var column = table.column(index);
            column.visible(!column.visible());
            $(e.target).toggleClass('disabled', !column.visible());  // Toggle button class
        })
    }


    function ColumnToggler(config) {
        var containerToggler = config.container.find('.toggle-header');
        var container = config.container.find('.toggle-container');
        addContainerToggler(containerToggler, container);
        createColumnTogglers(config.table, container);
    }

    return ColumnToggler;

})
