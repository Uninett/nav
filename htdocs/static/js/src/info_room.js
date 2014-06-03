require(
    [
        "plugins/tab_navigation",
        "info/global_dt_filters",
        "info/table_info_converter",
        "plugins/room_mapper",
        "plugins/sensors_controller",
        "dt_plugins/natsort",
        "dt_plugins/altsort",
        "dt_plugins/date_title_sort",
        "dt_plugins/modulesort",
        "libs/jquery",
        "libs/jquery-ui-1.8.21.custom.min",
        "libs/jquery.dataTables.min",
    ],
    function(tab_navigation, global_dt_filters, table_info_converter, RoomMapper, SensorsController) {
        /* Run javascript at document ready */
        $(function () {
            if ($('#infotabs').length) {
                add_tabs();
                add_navigation();
                add_streetmap();
            }

            var $mapContainer = $('#mapcontainer');
            if ($mapContainer.length) {
                fetchRoomPositions($mapContainer);
            }
        });

        /* Add tabs to roomview content */
        function add_tabs() {
            var tabconfig = {
                cache: true, // cache loaded pages
                spinner: '<img src="' + NAV.imagePath + '/main/process-working.gif">',
                load: function (event, ui) {
                    if (ui.panel.id === 'sensors') {
                        applyEnvironmentHandlers();
                    } else if (ui.panel.id === 'netboxinterfaces') {
                        applyNetboxInterfacesHandlers();
                    }
                }
            };
            var tabs = $('#infotabs').tabs(tabconfig);
            $('#infotabs').show();
        }

        function request_error(xhr, status, error) {
            console.error('Request error');
            $('<div class="messages error">Could not load netbox interfaces</div>').appendTo('#ui-tabs-1');
        }

        function applyNetboxInterfacesHandlers() {
            enrich_tables();
            add_filters();
            add_csv_download();
            $(document).foundation('reveal');  // Apply reveal after ajax request
            $(document).foundation('tooltip');  // Apply tooltip after ajax request
        }

        /* Add navigation to jQuery ui tabs */
        function add_navigation() {
            var wrapper = $('#infotabs');
            tab_navigation.add(wrapper);
        }

        function add_streetmap() {
            var position_node = $('#roominfo td.position');
            var roomname = $(position_node).attr('data-roomname');
            $.getJSON('/ajax/open/roommapper/rooms/' + roomname, function (data) {
                new RoomMapper('room_map', data.rooms).createMap();
            });
        }


        /* Enrich tables with dataTables module */
        function enrich_tables() {
            var dt_config = {
                bAutoWidth: false,
                bFilter: true,
                bInfo: true,
                bLengthChange: false,
                bPaginate: false,
                bSort: true,
                aoColumns: [
                    {'sType': 'module'},
                    {'sType': 'string'},
                    {'sType': 'alt-string'},
                    {'sType': 'natural'},
                    {'sType': 'title-date'}
                ],
                sDom: '<"H"i>t<"F">',
                fnInfoCallback: format_filter_text
            };

            $('table.netbox').dataTable(dt_config);

        }

        /* Custom format of search filter text */
        function format_filter_text(oSettings, iStart, iEnd, iMax, iTotal, sPre) {
            if (iEnd == iMax) {
                return "Showing " + iMax + " entries.";
            } else {
                var entrytext = iEnd == 1 ? "entry" : "entries";
                return "Showing " + iEnd + " " + entrytext + " (filtered from " + iMax + " entries).";
            }
        }

        /* Add global filtering to the tables */
        function add_filters() {
            var tables = $.fn.dataTable.fnTables();
            var primary_node = $('#netbox-global-search');
            var filters = ['last_seen', 'vlan'];

            try {
                global_dt_filters.add_filters(primary_node, tables, filters);
            } catch (error) {
                console.error(error.message);
            }
        }

        function add_csv_download() {
            var tables = $('#netboxes').find('table.netbox');
            var $form = $('#csv-download-form');
            $form.submit(function () {
                $form.find('[name=rows]').val(table_info_converter.create_csv(tables));
            });
        }

        function fetchRoomPositions(mapcontainer) {
            $.getJSON('/ajax/open/roommapper/rooms/', function (data) {
                new RoomMapper(mapcontainer.get(0), data.rooms).createMap();
            });
        }

        function applyEnvironmentHandlers() {
            /* Does stuff with the environment tab when it's loaded */
            var $page = $('#sensors'),
                $sensors = $page.find('.room-sensor'),
                $filters = $page.find('.sub-nav dd');


            new SensorsController($sensors);
            // Apply controller for each sensor

            // Filter controls
            $filters.on('click', function (event) {
                var $target = $(event.target),
                    $parent = $target.parent('dd');
                $filters.removeClass('active');
                $parent.addClass('active');

                switch ($target.attr('data-action')) {
                    case 'all':
                        $page.find('.rs-graph').show();
                        $page.find('.current').show();
                        break;
                    case 'charts':
                        $page.find('.rs-graph').show();
                        $page.find('.current').hide();
                        break;
                    case 'gauges':
                        $page.find('.rs-graph').hide();
                        $page.find('.current').show();
                        break;
                }
            });
        }
    }
);
