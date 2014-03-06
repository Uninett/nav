require(['plugins/room_mapper', 'plugins/navlets_controller', 'libs/jquery', 'libs/jquery-ui-1.8.21.custom.min'],
    function (RoomMapper, NavletsController) {
        'use strict';

        var $navletsContainer = $('#navlets');

        function createRoomMap(mapwrapper, room_map) {
            $.getJSON('/ajax/open/roommapper/rooms/', function (data) {
                if (data.rooms.length > 0) {
                    mapwrapper.show();
                    new RoomMapper(room_map.get(0), data.rooms).createMap();
                }
            });
        }

        $(function () {
            var controller = new NavletsController($navletsContainer);
            controller.container.on('navlet-rendered', function (event, node) {
                var mapwrapper = node.children('.mapwrapper');
                var room_map = mapwrapper.children('#room_map');
                if (room_map.length > 0) {
                    createRoomMap(mapwrapper, room_map);
                }
            });

            /* Add click listener to joyride button */
            $navletsContainer.on('click', '#joyrideme', function () {
                $(document).foundation('joyride', 'start');
            });

        });

    }
);


