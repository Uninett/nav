require([
    'netmap/graph_view',
    'netmap/control_view',
    'netmap/graph'

], function (GraphView, ControlView, Graph) {

    $(function () {

        var controlView = new ControlView();
        var graphView = new GraphView({netmapView: controlView.currentView});
    });
});