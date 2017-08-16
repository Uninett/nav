define(['libs/datatables.min'], function(require) {

    var columns = [
        "ifname",
        "ifalias",
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

    // Render functions for columns that need special treatment
    dtColumns[columns.indexOf('ifadminstatus')].render = renderStatus;
    dtColumns[columns.indexOf('ifoperstatus')].render = renderStatus;
    dtColumns[columns.indexOf('trunk')].render = function(data, type, row, meta) {
        return data ? 'Yes': ''
    };


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
            // info: false,
            processing: true,
            serverSide: true,
            ajax: {
                url: "/api/1/interface/?netbox=" + netboxid,
                data: translateParameters,
                dataFilter: translateData
            },
            columns: dtColumns,
            dom: "<f<'#ifclasses'>i>t",
            language: {
                info: "Showing _MAX_ entries"
            }
        });

        createClassFilters(dataTable);

    }

    function createClassFilters(dataTable) {
        var $form = $('#ifclasses').append("<form>");
        $form.append('<label><input type="checkbox" value="swport">Show swports</label>');
        $form.append('<label><input type="checkbox" value="gwport">Show gwports</label>');
        $form.on('change', dataTable.draw);
    }

    return portTable;

});
