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
        $(table.table().header()).find('th').each(function(index, element) {
            var $switcher = $('<li><div class="button tiny">' + element.innerHTML + '</div></li>');
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
        addContainerToggler(config.containerToggler, config.container);
        createColumnTogglers(config.table, config.container);
    }

    return ColumnToggler;

})
