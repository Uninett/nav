require([
    'netmap/graph_view',
    'netmap/control_view',

], function (GraphView, ControlView) {

    $(function () {

        // Test if browser is IE and, if so, is it supported.
        if (navigator.appVersion.indexOf('MSIE') !== -1) {
            var version = parseFloat(navigator.appVersion.split("MSIE")[1]);
            var docMode = document.documentMode ? document.documentMode : 0;
            if (version < 9 || docMode < 9) {
                alert('Your version of Internet Explorer is too old to run Netmap.' +
                    ' Please upgrade to IE9 or make sure DocumentMode is set to 9 or newer');
            }
        }

        // Disable caching for netmap
        $.ajaxSetup({ cache: false });
        $.ajaxSetup({ timeout: 240000 });

        var controlView = new ControlView();
        new GraphView({netmapView: controlView.currentView});
    });
});
