require(['plugins/room_mapper', 'plugins/navlets_controller', 'libs/jquery', 'libs/jquery-ui-1.8.21.custom.min'],
    function (RoomMapper, NavletsController) {

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

        $(function () {
            addRoomMap();
            var controller = new NavletsController($('#navlets'));
        });

    }
);
