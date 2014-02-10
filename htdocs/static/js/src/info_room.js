require(
    [
        "plugins/tab_navigation",
        "info/global_dt_filters",
        "info/table_info_converter",
        "plugins/room_mapper",
        "dt_plugins/natsort",
        "dt_plugins/altsort",
        "dt_plugins/date_title_sort",
        "dt_plugins/modulesort",
        "libs/jquery",
        "libs/jquery-ui-1.8.21.custom.min",
        "libs/jquery.dataTables.min",
        "libs/downloadify.min",
        "libs/swfobject"
    ],
    function(tab_navigation, global_dt_filters, table_info_converter, RoomMapper) {
        /* Run javascript at document ready */
        $(window).load(function () {

            if ($('#infotabs').length != 0) {
                add_tabs();
                add_navigation();
                add_streetmap();
            }

            if ($('#mapcontainer').length > 0) {
                fetchRoomPositions($('#mapcontainer'));
            }
        });

        /* Add tabs to roomview content */
        function add_tabs() {
            var tabconfig = {
                cache: true, // cache loaded pages
                spinner: '<img src="' + NAV.imagePath + '/main/process-working.gif">',
                ajaxOptions: {
                    error: request_error,
                    success: request_success
                }
            };
            var tabs = $('#infotabs').tabs(tabconfig);
            $('#infotabs').show();
        }

        function request_error(xhr, status, error) {
            console.error('Request error');
            $('<div class="messages error">Could not load netbox interfaces</div>').appendTo('#ui-tabs-1');
        }

        function request_success() {
            enrich_tables();
            add_filters();
//            add_csv_download();
            add_helper_dialog();
        }

        /* Add navigation to jQuery ui tabs */
        function add_navigation() {
            var wrapper = $('#infotabs');
            tab_navigation.add(wrapper);
        }

        function add_streetmap() {
            var position_node = $('#roominfo td.position');
            var roomname = $(position_node).attr('data-roomname');
            console.log('Adding streetmap');
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
            var tables = $('#netboxes table.netbox');

            var config = {
                filename: 'interfaces.csv',
                data: function () {
                    return table_info_converter.create_csv(tables);
                },
                transparent: false,
                swf: '/js/extras/downloadify.swf',
                downloadImage: NAV.imagePath + '/roominfo/csv.png',
                width: 41,
                height: 13,
                append: false
            };
            $('#downloadify').downloadify(config);
        }

        function add_helper_dialog() {
            var dialog = $('#searchhelptext').dialog({
                autoOpen: false,
                title: 'Search help',
                width: 500
            });
            $('#searchhelp').click(function () {
                dialog.dialog('open');
            });
        }

        function fetchRoomPositions(mapcontainer) {
            $.getJSON('/ajax/open/roommapper/rooms/', function (data) {
                new RoomMapper(mapcontainer.get(0), data.rooms).createMap();
            });
        }
    }
);
