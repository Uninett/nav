define(function(require) {

    var URI = require('libs/urijs/URI');
    var Moment = require('moment');
    require('jquery-sparkline');

    var storedMetricsRequests = {};
    var storedDataRequests = {};

    function isEmpty(cell) {
        return $(cell.node()).is(':empty');
    }

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
                addSparkLine(table, cell, suffix);
            }
        });
    }

    function addSparkLine(table, cell, suffix) {
        var interfaceId = getInterfaceId(table, cell);

        if (!storedMetricsRequests[interfaceId]) {
            storedMetricsRequests[interfaceId] = $.getJSON(NAV.urls.api_interface_list + interfaceId + '/metrics/');
        }

        storedMetricsRequests[interfaceId]
         .then(function(metrics) {
             return getGraphiteUri(metrics, suffix)[0];
         })
         .then(function(uri) {
             if (uri) {
                 var requestKey = [interfaceId, suffix].join(':');
                 if (!storedDataRequests[requestKey]) {
                     storedDataRequests[requestKey] = $.getJSON(uri.toString());
                 }
                 return storedDataRequests[requestKey];
             }
             return [];
         })
         .then(function(response) {
             response.forEach(function(data) {
                 createSparkLine(createSparkContainer(cell), convertToSparkLine(data));
             });
         })

    }

    function getRow(table, cell) {
        return table.row(cell.index().row);
    }

    /* Gets the interface id from the row-data of this cell */
    function getInterfaceId(table, cell) {
        return getRow(table, cell).data().id;
    }

    /*
     * Finds the correct url based on the suffix and modifies it for fetching data
     */
    function getGraphiteUri(metrics, suffix) {
        return metrics.filter(function(m) {
            return m.suffix === suffix;
        }).map(function(m) {
            console.log(m.url);
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


    /* Adds last used to a column */
    function addLastUsed(table, column) {
        table.cells(null, column, {page: 'current'}).every(function() {
            var cell = this;
            if (isEmpty(cell)) {
                var fetchLastUsed = $.getJSON(NAV.urls.api_interface_list + getInterfaceId(table, cell) + '/last_used/');
                fetchLastUsed.then(function(response) {
                    var hasLink = table.row(cell.index().row).data().ifoperstatus === 1;
                    var timestamp = response.last_used ? Moment(response.last_used) : null;
                    if ((timestamp && timestamp.year() === 9999) || hasLink) {
                        cell.node().innerHTML = 'In use';
                    } else if (timestamp) {
                        cell.node().innerHTML = timestamp.format('YYYY-MM-DD HH:mm:ss');
                    } else {
                        cell.node().innerHTML = "N/A"
                    }
                });
            }
        });
    }

    /** Check if we need to update columns with dynamic content

       Dynamic content is data that is not gotten directly from the API-query,
       but need to be inserted in a custom way.  */
    function checkDynamicColumns(table) {

        // Define what columns are dynamic and the action to take
        var columnActions = {
            'traffic-ifoutoctets:name': function() {
                addSparklines(table, 'traffic-ifoutoctets:name', 'ifOutOctets');
            },
            'traffic-ifinoctets:name': function() {
                addSparklines(table, 'traffic-ifinoctets:name', 'ifInOctets');
            },
            'traffic-ifouterrors:name': function() {
                addSparklines(table, 'traffic-ifouterrors:name', 'ifOutErrors');
            },
            'traffic-ifinerrors:name': function() {
                addSparklines(table, 'traffic-ifinerrors:name', 'ifInErrors');
            },
            'last_used:name': function() {
                addLastUsed(table, 'last_used:name')
            }
        }

        for (var selector in columnActions) {
            var column = table.column(selector);
            if (column.visible()) {
                // If the column is visible, execute the action.
                columnActions[selector]();
            }
        }
    }

    function updateDynamicColumns(table) {
        // Update columns when the user toggles a column on/off
        table.on('column-visibility.dt', function(e, settings, column, state) {
            checkDynamicColumns(table);
        })

        // Update columns when the table is (re)drawn
        table.on('draw.dt', function() {
            checkDynamicColumns(table);
        });
    }

    function controller(table) {
        updateDynamicColumns(table);
    }

    return controller;

});
