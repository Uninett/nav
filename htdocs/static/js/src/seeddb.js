require([
    'plugins/checkbox_selector',
    'plugins/quickselect',
    'plugins/seeddb_hstore',
    'plugins/netbox_connectivity_checker',
    'plugins/ip_chooser',
    'plugins/seeddb_map',
    'libs/spin',
    'libs/datatables.min',
    'libs/modernizr'],
function (CheckboxSelector, QuickSelect, FormFuck, connectivityChecker, IpChooser, seedDBRoomMap) {

    function executeOnLoad() {
        /**
         * Checks if we are on the DeviceGroup page. If so, initialize the
         * select multiple.
         */
        var $formElement = $('#id_netboxes'),
            $searchField = $('#device-group-select2');
        if ($formElement.length && $searchField.length) {
            initDeviceGroupSelectMultiple($formElement, $searchField);
        }

        /**
         * Checks if we are on the service page. If so, initalize the ajax
         * search for IP device and service handler
         */
        var $serviceCheckerAddForm = $('#service_checker_add_form');
        if ($serviceCheckerAddForm.length) {
            initSearchForIpDevice();
        }

        initJoyride();  /* Start joyride if url endswith #joyride */

        if ($('#map').length && $('#id_position').length) {
            seedDBRoomMap('map', 'id_position', 'get_location_trigger');
        }

        /* The Datatables plugin works best when content is rendered. Thus
         * we activate it on load */
        var $dataTable = $(tableSelector),
            $tableWrapper = $(tableWrapper);
        if ($tableWrapper.data('page') === 'cabling') {
            enrichTable('cabling');
        } else if ($tableWrapper.data('page') === 'patch') {
            enrichTable('patch');
        } else if ($dataTable.find('tbody tr').length > 1) {
            enrichTable('default');
        } else {
            $(tableWrapper).removeClass('notvisible');
        }

        new CheckboxSelector('#select', '.selector').add();
        var _quickselect = new QuickSelect('.quickselect');


        /* Add form to hstore fields in room */
        var $textarea = $('textarea#id_data');
        if ($textarea.length) {
            var _formfuck = new FormFuck($textarea);
        }

        activateIpDeviceFormPlugins();
        addConfirmLeavePage();
    }


    var tableWrapper = '#tablewrapper',
        tableSelector = '#seeddb-content';

    /* Internet Explorer caching leads to onload event firing before
     * script is loaded - thus we never get the load event. This code
     * will at least make it usable. */
    if (document.readyState === 'complete') {
        executeOnLoad();
    } else {
        $(window).load(executeOnLoad);
    }


    /**
     * Uses select2 to search for and display netboxes. Executes the search in
     * AJAX-requests.
     */
    function initDeviceGroupSelectMultiple($formElement, $searchField) {
        $searchField.select2({
            multiple: true,
            ajax: {
                url: NAV.urls.seeddb_netboxgroup_devicelist,
                dataType: 'json',
                quietMillis: 250,
                data: function (params) {
                    return {
                        query: params
                    };
                },
                results: function (data) {
                    return {
                        results: data
                    };
                }
            },
            /**
             * Populates the selection with options from the form element.
             * NB: The search field needs a value for this function to be run
             * (this is set directly in the html).
             */
            initSelection: function (element, callback) {
                var data = [];
                $formElement.find(':selected').each(function (index, option) {
                    data.push({
                        id: option.value,
                        text: option.innerHTML
                    });
                });
                return callback(data);
            },
            minimumInputLength: 3
        });

        /**
         * Sets the selected values in the form element to be the same as in
         * the select2 element when the form is submitted.
         */
        $('form.seeddb-edit').submit(function () {
            $formElement.val($searchField.select2('val'));
        });
    }

    function initJoyride() {
        /* Start joyride if url endswith #joyride */
        if (location.hash === '#joyride') {
            $(document).foundation({
                'joyride': {
                    'pre_ride_callback': function () {
                        var cards = $('.joyride-tip-guide').find('.joyride-content-wrapper');
                        cards.each(function (index, element) {
                            var counter = $('<small>')
                                    .attr('style', 'position:absolute;bottom:1.5rem;right:1.25rem')
                                    .html(index + 1 + ' of ' + cards.length);
                            $(element).append(counter);
                        });
                    },
                    'modal': false
                }
            });
            $(document).foundation('joyride', 'start');
        }
    }


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
        if (Modernizr.localstorage) {
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
        if (Modernizr.localstorage) {
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
            3: 'interface.ifname', 4: 'cabling.jack', 5: 'split'
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
        
    function activateIpDeviceFormPlugins() {
        // The connectivity checker
        var $form = $('#seeddb-netbox-form'),
            $addressField = $('#id_ip'),
            $feedbackElement = $('#verify-address-feedback');

        var chooser = new IpChooser($feedbackElement, $addressField);

        // Initialize connectivitychecker with a chooser as we only wants one.
        connectivityChecker(chooser);

        $form.on('submit', function (event, validated) {
            if (!validated) {
                event.preventDefault();
                var deferred = chooser.getAddresses();
                deferred.done(function () {
                    if (chooser.isSingleAddress) {
                        $form.trigger('submit', true);
                    }
                });
            }
        });
    }


    /**
     * Some forms are complex enough to varrant a confirmation if the user tries
     * to leave the page without saving the changed form.
     *
     * This function sets the return value on the beforeunload event if the
     * forms are changed but not saved before leaving the page, in effect
     * triggering the browsers "Are you sure you want to leave this
     * page"-confirmation.
     */
    function addConfirmLeavePage() {
        var setReturnValue = function (event) {
            event.returnValue = 'You have unsaved changes.';
        };

        var forms = $('#seeddb-netbox-form');

        forms.one('change', function() {
            window.addEventListener('beforeunload', setReturnValue);
        });
        forms.on('submit', function() {
            window.removeEventListener('beforeunload', setReturnValue);
        });
    }


    function initSearchForIpDevice() {
        $('#id_netbox').select2({
            placeholder: 'Search for IP device',
            minimumInputLength: 3,
            ajax: {
                url: NAV.urls.api_netbox_list,
                dataType: 'json',
                quietMillis: 250,
                data: function(params) {
                    return {
                        search: params
                    };
                },
                results: function(data, page, query) {
                    var results = data.results;
                    data.results.sort(function(a, b) {
                        if (a.sysname.toLowerCase() < b.sysname.toLowerCase()) {
                            return -1;
                        } else {
                            return 1;
                        }
                    });
                    return {
                        results: data.results.map(function(obj) {
                            return { id: obj.id, text: obj.sysname };
                        })
                    };
                }
            }
        });
    }

});
