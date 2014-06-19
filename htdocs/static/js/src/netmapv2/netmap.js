require([
    'netmap/graph_view',
    'netmap/control_view'

], function (GraphView, ControlView) {

    $(function () {

        var controlView = new ControlView();
        var graphView = new GraphView();
    });
});