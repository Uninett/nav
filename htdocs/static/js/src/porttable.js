define(['libs/datatables.min'], function(require) {

    /**
     * Set up the lookup arrays and objects
     */

    /* The data we want to use from the result set from the api. This determines
     * the order and what the table consist of. Remember that the table headers
     * need to be updated aswell */
    var columns = [
        "ifname",
        "ifalias",
        "module.name",
        "ifadminstatus",
        "ifoperstatus",
        "vlan",
        "trunk",
        "speed"
    ]

    // Create object with index => value for columns
    var columnsRef = columns.reduce(function(obj, value, index) {
        obj[index] = value;
        return obj;
    }, {});

    // The columns definitions for the datatable
    var dtColumns = columns.map(function(value) {
        return {data: value};
    });


    /*
     * RENDER FUNCTIONS
     *
     * Not everything can be rendered directly from the api. Here we modify what
     * is rendered in some columns.
     */
    dtColumns[columns.indexOf('ifname')].render = function(data, type, row, meta) {
        return '<a href="' + row.object_url + '">' + data + '</a>';
    };
    dtColumns[columns.indexOf('ifadminstatus')].render = renderStatus;
    dtColumns[columns.indexOf('ifoperstatus')].render = renderStatus;
    dtColumns[columns.indexOf('trunk')].render = function(data, type, row, meta) {
        return data ? 'Yes': ''
    };

    var duplexMap = {'f': 'FD', 'h': 'HD'}
    dtColumns[columns.indexOf('speed')].render = function(data, type, row, meta) {
        var duplex = duplexMap[row.duplex] || ''
        return data + " " + duplex;
    };


    /** Renders a light indicating status (red or green) */
    function renderStatus(data, type, row, meta) {
        var color = data === 2 ? 'red' : 'green';
        return '<img src="/static/images/lys/' + color + '.png">';
    }


    /**
     * Translate datatables parameters to be compatible with django rest
     * framework parameters
     */
    function translateParameters(d) {
        d.page = d.start / d.length + 1;
        d.page_size = 1000;
        d.search = d.search.value;
        d.ordering = d.order.map(function(order) {
            var direction = order.dir === 'asc' ? '' : '-';
            return direction + columnsRef[order.column];
        }).join(',');
        d.ifclass = getIfClasses();
    }


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
            processing: true,
            serverSide: true,
            ajax: {
                url: "/api/1/interface/?netbox=" + netboxid,
                data: translateParameters,
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

    }


    /**
     * Creates the checkboxes for filtering on ifclasses (swport, gwport)
     */
    function createClassFilters(dataTable) {
        var $form = $('#ifclasses').append("<form>");
        $form.append('<label><input type="checkbox" value="swport">Show swports</label>');
        $form.append('<label><input type="checkbox" value="gwport">Show gwports</label>');
        $form.on('change', dataTable.draw);
    }


    return portTable;

});
