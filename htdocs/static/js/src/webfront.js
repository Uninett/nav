require([
    'plugins/room_mapper',
    'plugins/navlets_controller',
    'plugins/sensors_controller',
    'libs/jquery-ui.min',
], function (RoomMapper, NavletsController, SensorsController) {
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
        var numColumns = $navletsContainer.data('widget-columns');
        var controller = new NavletsController($navletsContainer, numColumns);
        controller.container.on('navlet-rendered', function (event, node) {
            var mapwrapper = node.find('.mapwrapper');
            var room_map = mapwrapper.find('#room_map');
            if (room_map.length > 0) {
                createRoomMap(mapwrapper, room_map);
            }


            if (node.hasClass('SensorWidget')) {
                var sensor = new SensorsController(node.find('.room-sensor'));
            }
            
            
        });

        /* Add click listener to joyride button */
        $navletsContainer.on('click', '#joyrideme', function () {
            var menu = $('.toggle-topbar'),
                is_small_screen = menu.is(':visible');

            if (is_small_screen) {
                $('#joyride_for_desktop').remove();
            } else {
                $('#joyride_for_mobile').remove();
            }

            $(document).foundation('joyride', 'start');
        });

        /* Need some way of doing javascript stuff on widgets */
        $navletsContainer.on('click', '.watchdog-tests .label.alert', function (event) {
            $(event.target).closest('li').find('ul').toggle();
        });

    });

});
