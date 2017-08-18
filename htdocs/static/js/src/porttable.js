define(function(require) {

    var DataTables = require('libs/datatables.min');
    var moduleSort = require('dt_plugins/modulesort');
    var URI = require('libs/urijs/URI');

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
            type: "module",
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

        {
            data: "ifadminstatus",
            type: "statuslight",
            render: renderStatus
        },

        {
            data: "ifoperstatus",
            type: "statuslight",
            render: renderStatus
        },

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
    function PortTable(selector, netboxid) {
        this.netboxid = netboxid;
        this.selector = selector;
        this.dataTable = this.createDataTable();

        this.addCustomOrdering();
        this.addPortGroupListeners(createClassFilters());
        fixSearchDelay(this.dataTable);
    }

    PortTable.prototype = {
        createDataTable: function() {
            return $(this.selector).DataTable({
                autoWidth: false,
                paging: false,
                ajax: {
                    url: this.getUrl().toString(),
                    dataFilter: translateData
                },
                columns: dtColumns,
                dom: "f<'#ifclasses'><'#infoprocessing'ir>t",
                language: {
                    info: "_MAX_ entries",
                    processing: "Loading...",
                }
            });
        },

        /** Custom ordering for statuslight as it cant sort on html elements */
        addCustomOrdering: function() {
            $.fn.dataTable.ext.type.order['statuslight-pre'] = function ( data ) {
                return data;
            };
        },

        addPortGroupListeners: function($form) {
            var self = this;
            $form.on('change', function() {
                var selectedGroup = $form.find('[name=portgroup]:checked').val();
                var newUrl = self.getUrl().setSearch('ifclass[]', selectedGroup);
                console.log(newUrl.toString());
                self.dataTable.ajax.url(newUrl.toString()).load();
            });
        },

        getUrl: function() {
            return URI("/api/1/interface/")
                .addSearch('page_size', 1000)
                .addSearch('netbox', this.netboxid);
        }

    }


    /**
     * Creates the checkboxes for filtering on ifclasses (swport, gwport)
     */
    function createClassFilters() {
        var $form = $('#ifclasses').append("<form>");
        $form.append('<label><input type="radio" name="portgroup" value="all" checked>All ports</label>');
        $form.append('<label><input type="radio" name="portgroup" value="swport">Swports</label>');
        $form.append('<label><input type="radio" name="portgroup" value="gwport">Gwports</label>');
        $form.append('<label><input type="radio" name="portgroup" value="physicalport">Physical ports</label>');
        return $form;
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


    return PortTable;

});
