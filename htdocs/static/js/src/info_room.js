require(
    [
        "plugins/tab_navigation",
        "info/global_dt_filters",
        "info/table_info_converter",
        "plugins/room_mapper",
        "libs/rickshaw.min",
        "dt_plugins/natsort",
        "dt_plugins/altsort",
        "dt_plugins/date_title_sort",
        "dt_plugins/modulesort",
        "libs/jquery",
        "libs/jquery-ui-1.8.21.custom.min",
        "libs/jquery.dataTables.min",
        "libs/justgage.min"
    ],
    function(tab_navigation, global_dt_filters, table_info_converter, RoomMapper, Rickshaw) {
        /* Run javascript at document ready */
        $(window).load(function () {

            if ($('#infotabs').length != 0) {
                add_tabs();
                add_navigation();
                add_streetmap();
            }

            var $mapContainer = $('#mapcontainer');
            if ($mapContainer.length > 0) {
                fetchRoomPositions($mapContainer);
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
            addSensor();
            addGraphs();
        }

        function request_error(xhr, status, error) {
            console.error('Request error');
            $('<div class="messages error">Could not load netbox interfaces</div>').appendTo('#ui-tabs-1');
        }

        function request_success() {
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

        function addSensor() {
            var gauge1 = new JustGage({
                id: "envsensor1",
                value: 67,
                min: 0,
                max: 100,
                title: "Temperature"
            });
            var gauge2 = new JustGage({
                id: "envsensor2",
                value: 50,
                min: 0,
                max: 100,
                title: "Temperature"
            });
            var gauge3 = new JustGage({
                id: "envsensor3",
                value: 44,
                min: 0,
                max: 100,
                title: "Temperature"
            });

            var gauges = [gauge1, gauge2, gauge3];

            setInterval(function () {
                for (var i = 0,l = gauges.length; i<l; i++) {
                    gauges[i].refresh(parseInt(Math.random() * 100));
                }
            }, 10000);
        }

        function addGraphs() {
            $.get('http://localhost:9080/graphite/render/?width=399&height=187&_salt=1393919244.764&connectedLimit=&lineWidth=3&hideLegend=true&graphOnly=false&hideGrid=false&hideYAxis=false&target=nav.devices.uninett-gw_uninett_no.sensors.VTT_1_outlet_temperature_Sensor&format=json', function (data) {
                var results = data[0].datapoints.map(function (point) {
                        return {
                            x: point[1],
                            y: point[0]
                        };
                    });
                drawGraph(results);
            });

            function drawGraph(points) {
                var graph1 = new Rickshaw.Graph({
                    element: document.querySelector('#rs-chart1'),
                    width: 300,
                    height: 150,
                    renderer: 'line',
                    max: '110',
                    series: [{
                        color: 'steelblue',
                        data: points,
                        name: 'Temperature'
                    }]
                });

                var x_axis = new Rickshaw.Graph.Axis.Time({
                    'graph': graph1
                });
                var y_axis = new Rickshaw.Graph.Axis.Y({
                    'graph': graph1,
                    'orientation': 'left',
//                    'tickFormat': Rickshaw.Fixtures.Number.formatKMBT,
                    'element': document.getElementById('yaxis')
                });

                var hoverDetail = new Rickshaw.Graph.HoverDetail({
                    graph: graph1,
                    formatter: function (series, x, y) {
                        var date = '<span class="date">' + new Date(x * 1000).toUTCString() + '</span>';
                        var swatch = '<span class="detail_swatch" style="background-color: ' + series.color + '"></span>';
                        var content = swatch + series.name + ": " + parseInt(y) + '<br>' + date;
                        return content;
                    }
                });

                graph1.render();
            }
        }

    }
);
