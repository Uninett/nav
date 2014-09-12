/* The new jquery ui removes some trades some functionality
   for flexibility. This means we need some helper functions */
define(["libs/jquery"], function () {

    function cacheRequest(event, ui) {
        /* Cache is removed as an option in jquery-ui-1.10. Reimplement it */
        if (ui.tab.data("loaded")) {
            event.preventDefault();
            return;
        }

        ui.jqXHR.success(function () {
            ui.tab.data("loaded", true);
        });
    }

    return {
        'cacheRequest': cacheRequest
    };

});
