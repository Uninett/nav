define([
    'libs/datatables.min',
],

function() {

    var tableWrapper = '#tablewrapper',
        tableSelector = '#seeddb-content';
    var $dataTable = $(tableSelector),
        $tableWrapper = $(tableWrapper);


    function enrichTable(tableType) {
        var config = prepareDataTable(),
            $wrapper = config.wrapper,
            key = config.key;

        var tableTypes = {
            'default': applyDefaultDataTable,
            'cabling': applyCablingDataTable,
            'patch': applyPatchDataTable
        };

        var table = tableTypes[tableType](config);

        /* Store rowcount when user changes it */
        if (window.localStorage) {
            $wrapper.find('.dataTables_length select').change(function (event) {
                var newValue = $(event.target).val();
                localStorage.setItem(key, newValue);
            });
        }
    }

    function prepareDataTable() {
        var $wrapper = $(tableWrapper),
            keyPrefix = 'nav.seeddb.rowcount',
            key = [keyPrefix, $wrapper.attr('data-forpage')].join('.'),
            numRows = 10;
        if (window.localStorage) {
            var value = localStorage.getItem(key);
            if (value !== null) { numRows = +value; }
        }

        /* If neither a delete nor a move button is detected, no
         * action is available and thus the checkboxes for marking
         * action rows should not be displayed. */
        var showCheckBoxes = true;
        if (! ($("input[name='delete']").length || $("input[name='move']").length)) {
            showCheckBoxes = false;
        }

        // Add custom class to the wrapper element
        $.fn.dataTableExt.oStdClasses.sWrapper += ' dataTables_background';

        return {
            wrapper: $wrapper,
            key: key,
            numRows: numRows,
            showCheckBoxes: showCheckBoxes
        };
    }

    function getPageConfig(numRows) {
        // Enable and configure paging
        return {
            paging: true,
            pagingType: 'full_numbers',
            lengthChange: true,  // Change number of visible rows
            lengthMenu: [
                [10, 25, 50, -1],   // Choices for number of rows to display
                [10, 25, 50, "All"] // Text for the choices
            ],
            pageLength: numRows  // The default number of rows to display
        };
    }

    /* Runs on redraw of DataTable */
    function drawCallback(oSettings) {
        $('.paginate_button').removeClass('secondary').addClass('button tiny');
        $('.paginate_button.current').addClass('secondary');
        $('.ellipsis').addClass('button tiny secondary disabled paginate_button');
        $(tableWrapper).removeClass('notvisible');
    }

    function applyDefaultDataTable(options) {
        var numRows = options.numRows,
            showCheckBoxes = options.showCheckBoxes;

        var config = {
            // Enable and configure ordering
            ordering: true,  // Sort when clicking on headers
            order: [[1, 'asc']],
            columnDefs: [
                {
                    orderable: false,  // Do not sort
                    visible: showCheckBoxes, // Display or not based on 'showCheckBoxes'
                    targets: 0  // On this column
                }
            ],
            info: true,  // Show number of entries visible
            language: {
                info: '_START_ - _END_ of _TOTAL_'
            },

            dom: "<lip>t",   // display order of metainfo (lengthchange, info, pagination)
            drawCallback: drawCallback
        };
        $.extend(config, getPageConfig(numRows));

        /* Apply default DataTable */
        return $(tableSelector).DataTable(config);

    }

    function applyCablingDataTable(options) {
        var numRows = options.numRows,
            showCheckBoxes = options.showCheckBoxes;

        var columns = {
            0: 'id', 1: 'room', 2: 'jack', 3: 'building', 4: 'target_room',
            5: 'category', 6: 'description'
        };

        var config = {
            processing: true,  // Indicate on long loading times
            serverSide: true,  // https://datatables.net/manual/server-side
            ajax: {
                url: '/api/1/cabling?format=json',
                data: function(d) {
                    d.page = d.start / d.length + 1;
                    d.page_size = d.length;
                    d.search = d.search.value;
                    d.room = $('#id_room').val();
                    d.ordering = d.order.map(function(order) {
                        var direction = order.dir === 'asc' ? '' : '-';
                        return direction + columns[order.column];
                    }).join(',');
                },
                dataFilter: function(data){
                    var json = jQuery.parseJSON( data );
                    json.recordsTotal = json.count;
                    json.recordsFiltered = json.count;
                    json.data = json.results;
                    return JSON.stringify( json );
                }
            },
            columns: [
                { data: columns[0] },
                { data: columns[1] },
                { data: columns[2] },
                { data: columns[3] },
                { data: columns[4] },
                { data: columns[5] },
                { data: columns[6] }
            ],
            searching: true,
            // Enable and configure ordering
            ordering: true,  // Sort when clicking on headers
            order: [[1, 'asc']],
            columnDefs: [
                {
                    orderable: false,  // Do not sort
                    visible: showCheckBoxes, // Display or not based on 'showCheckBoxes'
                    render: function(data, type, row) {
                        return '<input type="checkbox" name="object" class="selector" value="' + data + '">';
                    },
                    targets: 0  // On this column (column 0)
                },
                {
                    targets: 2,
                    render: function(data, type, obj) {
                        return '<a href="' + NAV.urls.seeddb_cabling_edit + '?cablingid=' + obj.id + '">' + data + '</a>';
                    }
                }
            ],

            info: true,  // Show number of entries visible
            language: {
                info: '_START_ - _END_ of _TOTAL_'
            },
            dom: "<'filters'f><lip>t",   // display order of metainfo (lengthchange, info, pagination)
            drawCallback: drawCallback
        };
        $.extend(config, getPageConfig(numRows));


        /* Apply DataTable */
        var table = $(tableSelector).DataTable(config);

        /*
         Add a dropdown to select room. The dropdown is prepopulated. Do a new
         query when using the dropdown.
         */
        $('#id_room').appendTo('.filters').change(function() {
            table.draw();
        });

        $('#id_room').select2(); // Apply select2 to the room dropdown

        return table;
    }

    function applyPatchDataTable(options) {
        var numRows = options.numRows,
            showCheckBoxes = options.showCheckBoxes;

        var columns = {
            0: 'id', 1: 'cabling.room.id', 2: 'interface.netbox.sysname',
            3: 'interface.ifname', 4: 'interface.ifalias', 5: 'cabling.jack', 6: 'split'
        };

        var config = {
            processing: true,  // Indicate on long loading times
            serverSide: true,  // https://datatables.net/manual/server-side
            ajax: {
                url: '/api/1/patch?format=json',
                data: function(d) {
                    d.page = d.start / d.length + 1;
                    d.page_size = d.length;
                    d.search = d.search.value;
                    d.cabling__room = $('#id_room').val();
                    d.interface__netbox = $('#id_netbox').val();
                    d.ordering = d.order.map(function(order) {
                        var direction = order.dir === 'asc' ? '' : '-';
                        return direction + columns[order.column].split('.').join('__');
                    }).join(',');
                },
                dataFilter: function(data){
                    var json = jQuery.parseJSON( data );
                    json.recordsTotal = json.count;
                    json.recordsFiltered = json.count;
                    json.data = json.results;
                    return JSON.stringify( json );
                }
            },
            columns: [
                { data: columns[0] },
                { data: columns[1] },
                { data: columns[2] },
                { data: columns[3] },
                { data: columns[4] },
                { data: columns[5] },
                { data: columns[6] },
            ],
            searching: true,
            // Enable and configure ordering
            ordering: true,  // Sort when clicking on headers
            order: [[1, 'asc']],
            columnDefs: [
                {
                    orderable: false,  // Do not sort
                    visible: showCheckBoxes, // Display or not based on 'showCheckBoxes'
                    render: function(data, type, row) {
                        return '<input type="checkbox" name="object" class="selector" value="' + data + '">';
                    },
                    targets: 0  // On this column (column 0)
                },
                {
                    render: function(data, type, obj) {
                        return '<a href="' + NAV.urls.seeddb_patch_edit + '?netboxid=' + obj.interface.netbox.id + '">' + data + '</a>';
                    },
                    targets: 2
                }
            ],

            info: true,  // Show number of entries visible
            language: {
                info: '_START_ - _END_ of _TOTAL_'
            },
            dom: "<'filters'f><lip>t",   // display order of metainfo (lengthchange, info, pagination)
            drawCallback: drawCallback
        };
        $.extend(config, getPageConfig(numRows));


        /* Apply DataTable */
        var table = $(tableSelector).DataTable(config);

        /*
         Add dropdowns to select room and netbox. The dropdowns are
         prepopulated. Do a new query when using the dropdowns. They reset each
         other.
         */
        var $roomdropdown = $('#id_room'),
            $netboxdropdown = $('#id_netbox');
        $roomdropdown.appendTo('.filters').change(function() {
            $netboxdropdown.select2('val', '');
            table.draw();
        });
        $roomdropdown.select2(); // Apply select2 to the room dropdown

        $netboxdropdown.appendTo('.filters').change(function() {
            $roomdropdown.select2('val', '');
            table.draw();
        });
        $netboxdropdown.select2(); // Apply select2 to the room dropdown

        return table;
    }

    return {
        enrichTable: enrichTable,
        $dataTable: $dataTable,
        $tableWrapper: $tableWrapper
    };

});
