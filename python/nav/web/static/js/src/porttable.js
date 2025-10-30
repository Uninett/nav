define(function(require) {

    var DataTables = require('libs/datatables.min');
    var moduleSort = require('dt_plugins/modulesort');
    var URI = require('libs/urijs/URI');
    var Moment = require('moment');


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
            render: function(data, type, row, meta) {
                if (isSwPort(row)) {
                    return '<a href="' + NAV.urls.portadmin_index + row.id + '" title="Configure port in Portadmin"><img src="/static/images/toolbox/portadmin.svg" style="height: 1em; width: 1em" /></a>';
                }
                return '';
            },
            orderable: false
        },

        {
            data: "ifname",
            type: "module",
            render: function(data, type, row, meta) {
                return '<a href="' + row.object_url + '">' + data + '</a>';
            }
        },

        {
            data: "ifalias",
            render: function(data, type, row, meta) {
                return '<a href="' + row.object_url + '">' + data + '</a>';
            }
        },

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

        {
            data: "vlan",
            render: function(data, type, row, meta) {
                if (row['trunk']) {
                    return "<span title='Trunk' style='border: 3px double black; padding: 0 5px'>" + data + "</span>"
                }
                return data;
            }
        },

        {
            data: "vlan_netident",
            render: function(data, type, row, meta) {
                return data;
            }
        },

        {
            data: "speed",
            render: function(data, type, row, meta) {
                if (row.duplex === 'h') {
                    return data + '<span class="label warning" title="Half duplex" style="margin-left: .3rem">HD</span>';
                }
                return row.speed ? data : "";
            }
        },

        // Last used
        {
            render: function(data, type, row, meta) {
                // If this is not a swport last_used is meaningless
                if (!isSwPort(row)) {
                    return '';
                }

                if (row.last_used) {
                    var date = new Date(row.last_used.end_time);
                    return date.getYear() > 5000 ? "Now" : Moment(row.last_used.end_time).format('YYYY-MM-DD HH:mm:ss');
                } else {
                    if (row.last_used === undefined) {
                        // Display this when no data loaded
                        return ''
                    }
                    if (row.last_used === null) {
                        // Display this for no last used in dataset
                        return '<span class="dim">Never</span>';
                    }
                    return '';
                }
            },
            visible: false
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


    /** Renders a light indicating status (red or green) */
    function renderStatus(data, type, row, meta) {
        var color = data === 2 ? 'red' : 'green';
        return '<img src="/static/images/lys/' + color + '.png">';
    }


    /* Returns if this is a swport or not */
    function isSwPort(row) {
        return row.baseport !== null;
    }



    /**
     * The table to be instantiated
     * @param {string} selector - the jQuery selector for the table
     * @param {int} netboxid - the netboxid of the device to list ports for
     */
    function PortTable(selector, netboxid) {
        this.netboxid = netboxid;

        this.selectors = {
            table: selector,
            formContainer: '#ifclasses',
            form: 'portlistform'
        }

        // Initialize dataTable and add all custom stuff
        this.dataTable = this.createDataTable();
        addLoadingIndicator(this.selectors.table);
        addCustomOrdering();
        fixSearchDelay(this.dataTable);

        // Special treatment for the last used column that is an optional column
        var lastUsedColIndex = 9;
        var lastUsedColumn = this.dataTable.column(lastUsedColIndex);

        // Create form, add handlers
        var $form = createForm(this.selectors.form, this.selectors.formContainer);
        setFormFields($form);
        formListener(this, $form);
        toggleLastUsedOnXHR(this.selectors.table, lastUsedColumn, $form);
    }

    PortTable.prototype = {
        createDataTable: function() {
            // https://datatables.net/reference/option/
            return $(this.selectors.table).DataTable({
                autoWidth: false,
                paging: false,
                processing: true,
                orderClasses: false,
                ajax: {
                    url: this.getUrl(),
                    dataFilter: translateData
                },
                columns: dtColumns,
                order: [[1, 'asc']],
                dom: "f<'#ifclasses'><'#infoprocessing'ir>t",
                language: {
                    info: "_TOTAL_ entries",
                    processing: "Loading...",
                }
            });
        },

        getUrl: function() {
            return URI("/api/1/interface/")
                .addSearch('page_size', 10000)
                .addSearch('netbox', this.netboxid)
                .addSearch(getLocalStorageValues())
                .toString();
        },

        /**
         * Load data using custom request because of chunked loading
         * I'm leaving this here as an example although it's not in use
         * Remember to adjust page_size
         */
        loadData: function() {
            var self = this;

            function loadMoreData(data) {
                self.dataTable.rows.add(data.results).draw();
                if (data.next) {
                    $.get(data.next, loadMoreData);
                } else {
                    $('#portlist_processing').hide();
                }
            }

            $('#portlist_processing').show();
            $.get(this.getUrl(), loadMoreData)
        }
    }


    /**
     *
     * Form related stuff
     *
     */

    var localStorageKey = 'nav.porttable.filters'; // Key for local storage of form values

    /**
     * The form for filtering data
     */
    function createForm(formID, formContainer) {
        var $form = $("<form id='" + formID + "'>").appendTo(formContainer);
        var fs1 = $('<fieldset>').appendTo($form);
        var fs2 = $('<fieldset>').appendTo($form);
        fs1.append('<legend>Port filters</legend>')
        fs1.append('<label><input type="radio" name="ifclass" value="all">All ports</label>');
        fs1.append('<label><input type="radio" name="ifclass" value="swport">Switch ports</label>');
        fs1.append('<label><input type="radio" name="ifclass" value="gwport">Router ports</label>');
        fs1.append('<label><input type="radio" name="ifclass" value="physicalport">Physical ports</label>');
        fs1.append('<label><input type="radio" name="ifclass" value="trunk">Trunks</label>');

        fs2.append('<legend>Optional</legend>')
        fs2.append('<label><input type="checkbox" name="last_used">Last used</label>');
        return $form;
    }

    // Set form values based on localstorage values
    function setFormFields($form) {
        var localStorageValues = getLocalStorageValues();
        if (localStorageValues) {
            $form.find('[value="' + localStorageValues.ifclass + '"]').prop('checked', true);
            $form.find('[name="last_used"]').prop('checked', localStorageValues.last_used);
        } else {
            $form.find('[value="all"]').prop('checked', true);
        }
    }

    function getLocalStorageValues() {
        return JSON.parse(localStorage.getItem(localStorageKey));
    }

    function setLocalStorageValues($form) {
        var formData = $form.serializeObject();
        localStorage.setItem(localStorageKey, JSON.stringify(formData));
        return formData;
    }

    function formListener(dt, $form) {
        $form.on('change', function() {
            var formData = setLocalStorageValues($form);
            dt.dataTable.ajax.url(dt.getUrl()).load();
        });
    }


    function addLoadingIndicator(tableSelector) {
        $(tableSelector).on('processing.dt', function(event, settings, processing) {
            if (processing) {
                $(this).css('opacity', .5);
            } else {
                $(this).css('opacity', 1);
            }
        })
    }

    /** Custom ordering for statuslight as it cant sort on html elements */
    function addCustomOrdering() {
        $.fn.dataTable.ext.type.order['statuslight-pre'] = function ( data ) {
            return data;
        };
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


    /**
     * The searchdelay in DataTables starts whenever you start to write
     * (weird). Make it work so that the delay kicks in until you're actually
     * done typing.
     */
    function fixSearchDelay(dataTable) {
        $('#ports div.dataTables_filter input').off('keyup.DT input.DT');

        var searchDelay = null,
            prevSearch = null;

        $('#ports div.dataTables_filter input').on('keyup', function() {
            var search = $('#ports div.dataTables_filter input').val();

            clearTimeout(searchDelay);

            if (search !== prevSearch) {
                searchDelay = setTimeout(function() {
                    prevSearch = search;
                    dataTable.search(search).draw();
                }, 400);
            }
        });
    }

    function toggleLastUsedOnXHR(tableSelector, column, $form) {
        $(tableSelector).on('xhr.dt', function(e, settings, json, xhr) {
            column.visible($form.get(0).elements.last_used.checked);
        });
    }


    return PortTable;

});
