require([
    'netmap/graph_view',
    'netmap/control_view',
    'netmap/graph'

], function (GraphView, ControlView, Graph) {

    $(function () {

        // Disable caching for netmap
        $.ajaxSetup({ cache: false });

        document.navNetmapAppSpinner.stop();

        var controlView = new ControlView();
        var graphView = new GraphView({netmapView: controlView.currentView});
    });
});