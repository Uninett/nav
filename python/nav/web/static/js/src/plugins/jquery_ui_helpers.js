/* The new jquery ui removes some trades some functionality
   for flexibility. This means we need some helper functions */
define(["libs/spin.min", "jquery"], function (Spinner) {

    function cacheRequest(event, ui) {
        /* Cache is removed as an option in jquery-ui-1.10. Reimplement it */
        if (ui.tab.data("loaded")) {
            event.preventDefault();
            return;
        }

        ui.panel.css('min-height', '100px');
        var spinner = new Spinner({'top': 10,'left': 10}).spin(ui.panel.get(0));
        ui.jqXHR.done(function () {
            ui.tab.data("loaded", true);
        });
        ui.jqXHR.always(function () {
            spinner.stop();
        });
    }

    return {
        'cacheRequest': cacheRequest
    };

});
