require(['libs/jquery'], function () {
    $(function () {
        $('#watchdog-tests').on('click', '.label.alert', function (event) {
            $(event.target).next().toggle();
        });
    });
});
