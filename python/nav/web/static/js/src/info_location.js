require(
    [
        "plugins/tab_navigation",
        "plugins/room_mapper",
        "plugins/jquery_ui_helpers",
        "libs/jquery",
        "libs/jquery-ui.min",
        "plugins/lightbox"
    ],
    function(tab_navigation, RoomMapper, JUIHelpers) {
        /* Run javascript at document ready */
        $(function () {
            if ($('#infotabs').length) {
                add_tabs();
                add_navigation();
            }
        });

        /* Add tabs to locationview content */
        function add_tabs() {
            var tabconfig = {
                beforeLoad: JUIHelpers.cacheRequest,
                load: function (event, ui) {
                },
                create: function () {
                    setTimeout(function () {
                        // If the room_map element is visible 100 ms after the
                        // tabs are created, create the map
                        if (document.querySelector('#room_map').offsetParent) {
                            add_streetmap();
                        }
                    }, 200);
                },
                activate: function (event, ui) {
                    if (ui.newTab.attr('aria-controls') === 'locationinfo') {
                        add_streetmap();
                    }
                }
            };
            var tabs = $('#infotabs').tabs(tabconfig);
            tabs.show();
        }

        /* Add navigation to jQuery ui tabs */
        function add_navigation() {
            var wrapper = $('#infotabs');
            tab_navigation.add(wrapper);
        }

        function add_streetmap() {
            var position_node = $('#locationinfo td.locationid');
            var locationname = $(position_node).attr('data-locationid');
            if (document.querySelector('#room_map').childElementCount === 0) {
                new RoomMapper('room_map', {
                    location: locationname
                });
            }
        }
    }
);
