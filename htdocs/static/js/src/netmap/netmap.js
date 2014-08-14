require([
    'netmap/graph_view',
    'netmap/control_view',
    'netmap/graph'

], function (GraphView, ControlView, Graph) {

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

        document.navNetmapAppSpinner.stop();

        var controlView = new ControlView();
        var graphView = new GraphView({netmapView: controlView.currentView});
    });
});