require.config({
    baseUrl: "/js/"
});
require(['src/info/room_mapper', 'libs/jquery-1.4.4.min'], function (RoomMapper) {

    $(function () {
        var mapper_node = $('#room_map');
        var wrapper = mapper_node.parent('.mapwrapper');
        if (mapper_node.length > 0) {
            $.getJSON('/info/room/positions/', function (data) {
                wrapper.show();
                new RoomMapper(mapper_node.get(0), data.rooms).createMap();
            });
        }
    });

});
