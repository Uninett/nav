require(
    [
        "plugins/tab_navigation",
        "info/global_dt_filters",
        "info/table_info_converter",
        "plugins/room_mapper",
        "plugins/sensors_controller",
        "plugins/jquery_ui_helpers",
        "dt_plugins/natsort",
        "dt_plugins/altsort",
        "dt_plugins/date_title_sort",
        "dt_plugins/modulesort",
        "libs/jquery",
        "libs/jquery-ui.min",
        "libs/datatables.min",
        "plugins/lightbox"
    ],
    function(tab_navigation, global_dt_filters, table_info_converter, RoomMapper, SensorsController, JUIHelpers) {
        /* Run javascript at document ready */
        $(function () {
            if ($('#infotabs').length) {
                add_tabs();
                add_navigation();
            }

            var $mapContainer = $('#mapcontainer');
            if ($mapContainer.length) {
                fetchRoomPositions($mapContainer);
            }
        });

        /* Add tabs to roomview content */
        function add_tabs() {
            var tabconfig = {
                beforeLoad: JUIHelpers.cacheRequest,
                load: function (event, ui) {
                    if (ui.tab.attr('aria-controls') === 'sensors') {
                        applyEnvironmentHandlers();
                    } else if (ui.tab.attr('aria-controls') === 'netboxinterfaces') {
                        applyNetboxInterfacesHandlers();
                    }
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
                    if (ui.newTab.attr('aria-controls') === 'roominfo') {
                        add_streetmap();
                    }
                }
            };
            var tabs = $('#infotabs').tabs(tabconfig);
            tabs.show();
        }

        function request_error(xhr, status, error) {
            console.error('Request error');
            $('<div class="messages error">Could not load netbox interfaces</div>').appendTo('#ui-tabs-1');
        }

        function applyNetboxInterfacesHandlers() {
            enrich_tables();
            add_filters();
            add_csv_download();
            // Necessary for HTMX to process content added by AJAX request
            htmx.process(document.getElementById("netboxes"))
        }

        /* Add navigation to jQuery ui tabs */
        function add_navigation() {
            var wrapper = $('#infotabs');
            tab_navigation.add(wrapper);
        }

        function add_streetmap() {
            var position_node = $('#roominfo td.position');
            var roomname = $(position_node).attr('data-roomname');
            if (document.querySelector('#room_map').childElementCount === 0) {
                new RoomMapper('room_map', { room: roomname });
            }
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
            if (iEnd === iMax) {
                return "Showing " + iMax + " entries.";
            } else {
                var entrytext = iEnd === 1 ? "entry" : "entries";
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
            new RoomMapper(mapcontainer.get(0));
        }

        function applyEnvironmentHandlers() {
            /* Does stuff with the environment tab when it's loaded */
            var $page = $('#sensors'),
                $sensors = $page.find('.room-sensor'),
                $filters = $page.find('.sub-nav dd');


            // Apply controller for each sensor
            var _controller = new SensorsController($sensors);

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
