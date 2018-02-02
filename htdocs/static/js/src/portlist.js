define(function(require) {

    var DataTables = require('libs/datatables.min');
    var moduleSort = require('dt_plugins/modulesort');
    var URI = require('libs/urijs/URI');
    var Moment = require('moment');
    var columnToggler = require('src/portlist_column_toggler');
    var filterController = require('src/portlist_filter_controller');
    require('libs/select2.min');
    require('libs/jquery.sparkline');

    var selectors = {
        table: '#portlist-table'
    }


    /*
     * dtColumns defines the data we want to use from the result set from the
     * api. They are in order of appearance in the table - changes here may need
     * changes in the template aswell.
     *
     * More information about the options for each column can be seen at
     * https://datatables.net/reference/option/ -> columns
     */
    var dtColumns = [
        {
            name: 'portadmin-link',
            render: function(data, type, row, meta) {
                if (isSwPort(row)) {
                    return '<a href="' + NAV.urls.portadmin_index + row.id + '" title="Configure port in Portadmin"><img src="/static/images/toolbox/portadmin.svg" style="height: 1em; width: 1em" /></a>';
                }
                return '';
            },
            orderable: false
        },

        {
            data: "netbox.sysname",
            name: 'netbox'
        },

        {
            data: "ifname",
            name: 'ifname',
            type: "module",
            render: function(data, type, row, meta) {
                return '<a href="' + row.object_url + '">' + data + '</a>';
            }
        },

        {
            data: "ifalias",
            name: 'ifalias',
            render: function(data, type, row, meta) {
                return '<a href="' + row.object_url + '">' + data + '</a>';
            }
        },

        {
            data: 'module',
            name: 'module',
            render: function(data, type, row, meta) {
                return data
                     ? '<a href="' + data.object_url + '">' + data.name + '</a>'
                     : '';
            }
        },

        {
            data: "ifadminstatus",
            name: 'adminstatus',
            type: "statuslight",
            render: renderStatus
        },

        {
            data: "ifoperstatus",
            name: 'operstatus',
            type: "statuslight",
            render: renderStatus
        },

        {
            data: "vlan",
            name: 'vlan',
            render: function(data, type, row, meta) {
                if (row['trunk']) {
                    return "<span title='Trunk' style='border: 3px double black; padding: 0 5px'>" + data + "</span>"
                }
                return data;
            }
        },

        {
            data: "speed",
            name: 'speed',
            render: function(data, type, row, meta) {
                if (row.duplex === 'h') {
                    return data + '<span class="label warning" title="Half duplex" style="margin-left: .3rem">HD</span>';
                }
                return row.speed ? data : "";
            }
        },

        {
            data: 'to_netbox',
            name: 'to-netbox',
            render: function(data, type, row, meta) {
                return data
                     ? '<a href="' + data.object_url + '">' + data.sysname + '</a>'
                     : '';
            }
        },

        {
            data: 'to_interface',
            name: 'to-interface',
            render: function(data, type, row, meta) {
                return data
                     ? '<a href="' + data.object_url + '">' + data.ifname + '</a>'
                     : '';
            }
        },

        {
            data: null,
            name: 'traffic-ifoutoctets',
            orderable: false,
            render: function() { return ''; },
            visible: false
        },

        {
            data: null,
            name: 'traffic-ifinoctets',
            orderable: false,
            render: function() { return ''; },
            visible: false
        },

        {
            data: null,
            name: 'last_used',
            orderable: false,
            render: function() { return ''; },
            visible: false
        }

    ];


    /** Renders a light indicating status (red or green) */
    function renderStatus(data, type, row, meta) {
        var color = data === 2 ? 'red' : 'green';
        return '<img src="/static/images/lys/' + color + '.png">';
    }

    /* Returns if this is a swport or not */
    function isSwPort(row) {
        return row.baseport !== null;
    }


    /** Check columns with dynamic content */
    function checkDynamicColumns(table) {

        // Map column names to actions
        var columnActions = {
            'traffic-ifoutoctets:name': function() {
                addSparklines(table, 'traffic-ifoutoctets:name', 'ifOutOctets');
            },
            'traffic-ifinoctets:name': function() {
                addSparklines(table, 'traffic-ifinoctets:name', 'ifInOctets');
            },
            'last_used:name': function() {
                addLastUsed(table, 'last_used:name')
            }
        }

        for (var selector in columnActions) {
            var column = table.column(selector);
            if (column.visible()) {
                columnActions[selector]();
            }
        }
    }

    function createTable() {
        return $(selectors.table).DataTable({
            autoWidth: false,
            paging: true,
            pagingType: 'simple',
            orderClasses: false,
            ajax: {
                url: filterController.getUrl(),
                dataFilter: translateData
            },
            columns: dtColumns,
            order: [[1, 'asc']],
            dom: "<pirl>t",
            language: {
                info: "_TOTAL_ entries",
                processing: "Loading...",
            }
        });
    }

    /**
     * Translate data keys from response to something datatables understand
     */
    function translateData(data) {
        var json = jQuery.parseJSON( data );
        json.recordsTotal = json.count;
        json.data = json.results;
        return JSON.stringify( json );
    }


    /*******************/
    /* DYNAMIC COLUMNS */
    /*******************/


    function isEmpty(cell) {
        return $(cell.node()).is(':empty');
    }

    function addLastUsed(table, column) {
        table.cells(null, column, {page: 'current'}).every(function() {
            var cell = this;
            if (isEmpty(cell)) {
                var fetchLastUsed = $.getJSON('/api/interface/' + getInterfaceId(table, cell) + '/last_used/');
                fetchLastUsed.then(function(response) {
                    var hasLink = table.row(cell.index().row).data().ifoperstatus === 1;
                    var timestamp = response.last_used ? Moment(response.last_used) : null;
                    if ((timestamp && timestamp.year() === 9999) || hasLink) {
                        cell.node().innerHTML = 'In use';
                    } else if (timestamp) {
                        cell.node().innerHTML = moment.format('YYYY-MM-DD HH:mm:ss');
                    }
                });
            }
        });
    }

    /********************/
    /** SPARKLINE STUFF */
    /********************/


    /** Adds sparklines to the cells in this column on the current page

       - For each cell, fetch the metrics for that interface.
       - Then find and modify the url for the metric/suffix we are looking for.
       - Use this url to fetch data.
       - Create a sparkline showing these data.

     */
    function addSparklines(table, column, suffix) {
        table.cells(null, column, {page: 'current'}).every(function() {
            var cell = this;
            if (isEmpty(cell)) {
                var fetchMetrics = $.getJSON('/api/interface/' + getInterfaceId(table, this) + '/metrics/');
                fetchMetrics
                    .then(function(metrics) {
                        return getGraphiteUri(metrics, suffix)[0];
                    })
                    .then(function(uri) {
                        return uri ? $.getJSON(uri.toString()) : [];
                    })
                    .then(function(response) {
                        response.forEach(function(data) {
                            createSparkLine(createSparkContainer(cell), convertToSparkLine(data));
                        });
                    })
            }
        });
    }

    /* Gets the interface id from the row-data of this cell */
    function getInterfaceId(table, cell) {
        return table.row(cell.index().row).data().id;
    }

    /*
     * Finds the correct url based on the suffix and modifies it for fetching data
     */
    function getGraphiteUri(metrics, suffix) {
        return metrics.filter(function(m) {
            return m.suffix === suffix;
        }).map(function(m) {
            return new URI(m.url)
                .removeSearch(['height', 'width', 'template', 'vtitle'])
                .addSearch('format', 'json');
        });
    }

    /* Creates a container for a sparkline inside a cell */
    function createSparkContainer(cell) {
        var $cell = $(cell.node());
        var $container = $('<div>').addClass('sparkline');
        $cell.append($container);
        return $container;
    }

    /* Maps data from graphite to format jquery.sparkline understands */
    function convertToSparkLine(data) {
        return data.datapoints.map(function(point) {
            return [point[1], Number(point[0]).toFixed()];
        });
    }

    function createSparkLine($container, dataPoints) {
        $container.sparkline(dataPoints, {
            tooltipFormatter: self.formatter,
            type: 'line',
            width: '100px'
        });
    }


    function updateDynamicColumns(table) {
        table.on('column-visibility.dt', function(e, settings, column, state) {
            checkDynamicColumns(table);
        })
        table.on('draw.dt', function() {
            checkDynamicColumns(table);
        });
    }

    /** TABLE INITIATION */
    function PortList() {
        var table = createTable();
        columnToggler({
            table: table,
            container: $('#column-toggler')
        });
        filterController.controller(table);
        updateDynamicColumns(table)
    }

    return PortList

});
