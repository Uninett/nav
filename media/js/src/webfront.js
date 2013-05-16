require(['plugins/room_mapper', 'plugins/navlet_controller', 'libs/jquery', 'libs/jquery-ui-1.8.21.custom.min'],
    function (RoomMapper, NavletController) {

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
                addNavletOrdering($container);
            });
        }

        function addNavletOrdering($container) {
            var $activateButton = $('#navlet-ordering-activate'),
                $saveButton = $('#navlet-ordering-save'),
                $navlets = $container.find('.navlet');
            $container.sortable({
                'disabled': true
            });

            $activateButton.click(function ($button) {
                $container.sortable('option', 'disabled', false);
                $navlets.addClass('outline');
                $activateButton.hide();
                $saveButton.show();
            });

            $saveButton.click(function () {
                var $navlets = $container.find('.navlet'),
                    ordering = {};

                $navlets.each(function (index, navlet) {
                    ordering[$(navlet).attr('data-id')] = index;
                });

                $.post($container.attr('data-save-order-url'),
                    ordering,
                    function () {
                        $container.sortable('option', 'disabled', true);
                        $navlets.removeClass('outline');
                        $activateButton.show();
                        $saveButton.hide();
                    }
                );
            });
        }

        $(function () {
            addRoomMap();
            fetchNavlets();
        });

    }
);
