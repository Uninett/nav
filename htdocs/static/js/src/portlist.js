define(function(require) {

    var DataTables = require('libs/datatables.min');
    var columnToggler = require('src/portlist_column_toggler');
    var filterController = require('src/portlist_filter_controller');
    var dynamicColumnsController = require('src/portlist_dynamic_columns_controller');
    var stateController = require('src/plugins/state_controller');

    var storageKey = 'DataTables_portlist-table_/formstate/';

    var selectors = {
        table: '#portlist-table',
        filterForm: '#filters',
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
                    return '<a href="' + NAV.urls.portadmin_index + row.id + '" title="Configure port in Portadmin"><img src="' + NAV.imagePath + '/toolbox/portadmin.svg" style="height: 1em; width: 1em" /></a>';
                }
                return '';
            },
            orderable: false,
            title: '<img src="' + NAV.imagePath + '/toolbox/portadmin.svg" style="height: 1em; width: 1em" />'
        },

        {
            data: "netbox.sysname",
            name: 'netbox',
            render: function(data, type, row, meta) {
                return '<a href="' + row.netbox.object_url + '">' + data + '</a>';
            },
            title: 'Device'
        },

        {
            data: "ifname",
            name: 'ifname',
            type: "module",
            render: function(data, type, row, meta) {
                return '<a href="' + row.object_url + '">' + data + '</a>';
            },
            title: 'Port'
        },

        {
            data: "ifalias",
            name: 'ifalias',
            render: function(data, type, row, meta) {
                return '<a href="' + row.object_url + '">' + data + '</a>';
            },
            title: 'Port Description'
        },

        {
            data: 'module',
            name: 'module',
            render: function(data, type, row, meta) {
                return data
                     ? '<a href="' + data.object_url + '">' + data.name + '</a>'
                     : '';
            },
            title: 'Module'
        },

        {
            data: "ifadminstatus",
            name: 'adminstatus',
            type: "statuslight",
            render: renderStatus,
            title: 'Admin'
        },

        {
            data: "ifoperstatus",
            name: 'operstatus',
            type: "statuslight",
            render: renderStatus,
            title: 'Link'
        },

        {
            data: "vlan",
            name: 'vlan',
            render: function(data, type, row, meta) {
                if (row['trunk']) {
                    return "<span title='Trunk' style='border: 3px double black; padding: 0 5px'>" + data + "</span>"
                }
                return data;
            },
            title: 'Vlan'
        },

        {
            data: "speed",
            name: 'speed',
            render: function(data, type, row, meta) {
                if (row.duplex === 'h') {
                    return data + '<span class="label warning" title="Half duplex" style="margin-left: .3rem">HD</span>';
                }
                return row.speed ? data : "";
            },
            title: 'Speed'
        },

        {
            data: 'to_netbox',
            name: 'to-netbox',
            render: function(data, type, row, meta) {
                return data
                     ? '<a href="' + data.object_url + '">' + data.sysname + '</a>'
                     : '';
            },
            title: 'To Device'
        },

        {
            data: 'to_interface',
            name: 'to-interface',
            render: function(data, type, row, meta) {
                return data
                     ? '<a href="' + data.object_url + '">' + data.ifname + '</a>'
                     : '';
            },
            title: 'To Port'
        },

        {
            data: null,
            name: 'traffic-ifoutoctets',
            orderable: false,
            render: function() { return ''; },
            visible: false,
            title: 'OutOctets'
        },

        {
            data: null,
            name: 'traffic-ifinoctets',
            orderable: false,
            render: function() { return ''; },
            visible: false,
            title: 'InOctets'
        },

        {
            data: null,
            name: 'traffic-ifouterrors',
            orderable: false,
            render: function() { return ''; },
            visible: false,
            title: 'OutErrors'
        },

        {
            data: null,
            name: 'traffic-ifinerrors',
            orderable: false,
            render: function() { return ''; },
            visible: false,
            title: 'InErrors'
        },

        {
            data: null,
            name: 'last_used',
            orderable: false,
            render: function() { return ''; },
            visible: false,
            title: 'Last Used'
        },

    ];


    /** Renders a light indicating status (red or green) */
    function renderStatus(data, type, row, meta) {
        var color = data === 2 ? 'red' : 'green';
        return '<img src="' + NAV.imagePath + '/lys/' + color + '.png">';
    }

    /* Returns if this is a swport or not */
    function isSwPort(row) {
        return row.baseport !== null;
    }


    /* Create the datatable */
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
            dom: '<"#portlist-controls"<"#columns-controls"p><irl>>t',
            language: {
                info: "_TOTAL_ entries",
                processing: "Loading...",
            },
            stateSave: true,
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

    /** TABLE INITIATION */

    function PortList() {
        var form = document.querySelector(selectors.filterForm);
        /* Set filters based on localstorage. Remember there are two filters,
        the ones we control and the ones DataTable controls. */
        stateController.setFormState(form, storageKey);

        var table = createTable();

        columnToggler({
            table: table,
            container: $('#column-toggler')
        });

        // Move the column toggler to the correct element
        $('#columns-controls').prepend($('#column-toggler').css('display', 'inline-block'));

        // Enable the different filters and column toggle functions
        filterController.controller(table);
        dynamicColumnsController(table);

        // Save form state on datatable state save
        table.on('stateSaveParams.dt', function() {
            stateController.setFormStateInStorage(form, storageKey);
        });
    }


    return PortList

});
