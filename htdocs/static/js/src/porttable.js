define(['libs/datatables.min'], function(require) {

    /**
     * Set up the lookup arrays and objects
     */

    /* The data we want to use from the result set from the api. This determines
     * the order and what the table consist of. Remember that the table headers
     * need to be updated aswell */
    var duplexMap = {'f': 'FD', 'h': 'HD'};

    /** Renders a light indicating status (red or green) */
    function renderStatus(data, type, row, meta) {
        var color = data === 2 ? 'red' : 'green';
        return '<img src="/static/images/lys/' + color + '.png">';
    }

    var dtColumns = [
        {
            data: "ifname",
            render: function(data, type, row, meta) {
                return '<a href="' + row.object_url + '">' + data + '</a>';
            }
        },

        {data: "ifalias"},

        {
            data: 'module',
            render: function(data, type, row, meta) {
                return data
                    ? '<a href="' + data.object_url + '">' + data.name + '</a>'
                    : '';
            }
        },

        {data: "ifadminstatus", render: renderStatus},
        {data: "ifoperstatus", render: renderStatus},
        {data: "vlan"},

        {
            data: "trunk",
            render: function(data, type, row, meta) {
                if (data) {return 'Yes'}
                else if (data === false) {return ''}
                else {return 'N/A'}
            }
        },

        {
            data: "speed",
            render: function(data, type, row, meta) {
                var duplex = duplexMap[row.duplex] || ''
                return data + " " + duplex;
            }
        },

        {
            data: 'to_netbox',
            render: function(data, type, row, meta) {
                return data
                    ? '<a href="' + data.object_url + '">' + data.sysname + '</a>'
                    : '';
            }
        },

        {
            data: 'to_interface',
            render: function(data, type, row, meta) {
                return data
                    ? '<a href="' + data.object_url + '">' + data.ifname + '</a>'
                    : '';
            }
        },

    ];


    /**
     * Gets the selected checkboxes for interface classes
     * @returns {Array}
     */
    function getIfClasses() {
        return $('#ifclasses input:checked').map(function() {
            return this.value;
        }).get();
    }


    /**
     * Translate data keys from response to something datatables understand
     */
    function translateData(data) {
        var json = jQuery.parseJSON( data );
        json.recordsTotal = json.count;
        json.recordsFiltered = json.count;
        json.data = json.results;
        return JSON.stringify( json );
    }


    /** Create datatable */
    function portTable(selector, netboxid) {
        var dataTable = $(selector).DataTable({
            autoWidth: false,
            paging: false,
            ajax: {
                url: "/api/1/interface/?netbox=" + netboxid,
                dataFilter: translateData
            },
            columns: dtColumns,
            dom: "f<'#ifclasses'><'#infoprocessing'ir>t",
            language: {
                info: "_MAX_ entries",
                processing: "Loading...",
            }
        });

        createClassFilters(dataTable);
        fixSearchDelay(dataTable);
    }


    /**
     * Creates the checkboxes for filtering on ifclasses (swport, gwport)
     */
    function createClassFilters(dataTable) {
        var $form = $('#ifclasses').append("<form>");
        $form.append('<label><input type="radio" name="portgroup" value="all" checked>All ports</label>');
        $form.append('<label><input type="radio" name="portgroup" value="swport">Swports</label>');
        $form.append('<label><input type="radio" name="portgroup" value="gwport">Gwports</label>');
        $form.append('<label><input type="radio" name="portgroup" value="physicalport">Physical ports</label>');
        $form.on('change', function() {
            dataTable.draw();
            $form.find('input').prop('disabled', true);
        });
        dataTable.on('draw.dt', function() {
            $form.find('input').prop('disabled', false);
        })
    }


    /**
     * The searchdelay in DataTables starts whenever you start to write
     * (weird). Make it work so that the delay kicks in until you're actually
     * done typing.
     */
    function fixSearchDelay(dataTable) {
        $('div.dataTables_filter input').off('keyup.DT input.DT');

        var searchDelay = null,
            prevSearch = null;

        $('div.dataTables_filter input').on('keyup', function() {
            var search = $('div.dataTables_filter input').val();

            clearTimeout(searchDelay);

            if (search !== prevSearch) {
                searchDelay = setTimeout(function() {
                    prevSearch = search;
                    dataTable.search(search).draw();
                }, 400);
            }
        });
    }


    return portTable;

});
