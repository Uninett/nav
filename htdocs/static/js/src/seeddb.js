require([
    'plugins/checkbox_selector',
    'plugins/quickselect',
    'plugins/seeddb_hstore',
    'plugins/netbox_connectivity_checker',
    'plugins/ip_chooser',
    'plugins/seeddb_map',
    'libs/spin',
    'libs/jquery.dataTables.min',
    'libs/modernizr',
    'libs/FixedColumns.min'], function (CheckboxSelector, QuickSelect, FormFuck,
                                        connectivityChecker, IpChooser, seedDBRoomMap)
{

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

        initJoyride();  /* Start joyride if url endswith #joyride */

        if ($('#map').length && $('#id_position').length) {
            seedDBRoomMap('map', 'id_position', 'get_location_trigger');
        }

        /* The Datatables plugin works best when content is rendered. Thus
         * we activate it on load */
        if ($(tableSelector).find('tbody tr').length > 1) {
            enrichTable();
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

    function enrichTable() {
        var $wrapper = $(tableWrapper),
            keyPrefix = 'nav.seeddb.rowcount',
            key = [keyPrefix, $wrapper.attr('data-forpage')].join('.'),
            numRows = 10;
        if (Modernizr.localstorage) {
            var value = localStorage.getItem(key);
            if (value !== null) { numRows = value; }
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

        /* Apply DataTable */
        var table = $(tableSelector).dataTable({
            "bPaginate": true,      // Pagination
            "bLengthChange": true,  // Change number of visible rows
            "bFilter": false,       // Searchbox
            "bSort": true,          // Sort when clicking on headers
            "bInfo": true,          // Show number of entries visible
            "bAutoWidth": true,     // Resize table
            "sScrollX": '100%',     // Scroll when table is bigger than viewport
            "aoColumnDefs": [
                {
                    'bSortable': false,
                    'sWidth': '16px',
                    'aTargets': [ 0 ],  // Do not sort on first column
                    'bVisible': showCheckBoxes
                }
            ],
            "sPaginationType": "full_numbers", // Display page numbers in pagination
            "sDom": "<lip>t",   // display order of metainfo (lengthchange, info, pagination)
            "fnDrawCallback": function (oSettings) {
                /* Run this on redraw of table */
                $('.paginate_button').removeClass('disabled').addClass('button tiny');
                $('.paginate_active').addClass('button tiny secondary');
                $('.paginate_button_disabled').addClass('disabled');
                $(tableWrapper).removeClass('notvisible');
            },
            "aLengthMenu": [
                [10, 25, 50, -1],   // Choices for number of entries to display
                [10, 25, 50, "All"] // Text for the choices
            ],
            "iDisplayLength": numRows,  // The default number of rows to display
            "oLanguage": {"sInfo": "_START_-_END_ of _TOTAL_"},  // Format of number of entries visibile
        });

        table.fnSort([[1, 'asc']]);  // When loaded, sort ascending on second column

        /* Store rowcount when user changes it */
        if (Modernizr.localstorage) {
            $wrapper.find('.dataTables_length select').change(function (event) {
                var newValue = $(event.target).val();
                localStorage.setItem(key, newValue);
            });
        }
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

});
