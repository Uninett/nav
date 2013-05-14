require(['plugins/room_mapper', 'plugins/navlet_controller', 'libs/jquery'], function (RoomMapper, NavletController) {

    function addRoomMap() {
        var mapper_node = $('#room_map');
        var wrapper = mapper_node.parent('.mapwrapper');
        if (mapper_node.length > 0) {
            $.getJSON('/ajax/open/roommapper/rooms/', function (data) {
                if (data.rooms.length > 0) {
                    wrapper.show();
                    new RoomMapper(mapper_node.get(0), data.rooms).createMap();
                }
            });
        }
    }

    function fetchNavlets() {
        var $container = $('#navlets'),
            url = $container.attr('data-list-navlets');

        $.getJSON(url, function (data) {
            var navlets = data, i, l;
            for (i=0, l=data.length; i<l; i++) {
                var controller = new NavletController($container, data[i]);
            }
        });
    }

    $(function () {
        addRoomMap();
        fetchNavlets();
    });

});
