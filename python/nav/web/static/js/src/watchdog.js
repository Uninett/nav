require([], function () {

    /** Adds click handler on the status test labels */
    function addLabelClickHandlers() {
        $('#watchdog-tests').on('click', '.label.alert', function (event) {
            $(event.target).closest('li').find('ul').toggle();
        });
    }


    /** Do this on page ready */
    $(function () {
        addLabelClickHandlers();
    });

});
