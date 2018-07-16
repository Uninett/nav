require([
    'plugins/seeddb_datatables',
    'plugins/checkbox_selector',
    'plugins/quickselect',
    'plugins/seeddb_hstore',
    'plugins/netbox_connectivity_checker',
    'plugins/ip_chooser',
    'plugins/seeddb_map',
    'libs/modernizr'],
function (datatables, CheckboxSelector, QuickSelect, FormFuck, connectivityChecker, IpChooser, seedDBRoomMap) {

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
        if (datatables.$tableWrapper.data('page') === 'cabling') {
            datatables.enrichTable('cabling');
        } else if (datatables.$tableWrapper.data('page') === 'patch') {
            datatables.enrichTable('patch');
        } else if (datatables.$dataTable.find('tbody tr').length > 1) {
            datatables.enrichTable('default');
        } else {
            datatables.$tableWrapper.removeClass('notvisible');
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

        addParentSelect2();
    }


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


    /** Add Select2 to parent fields. They demand extra styling and thus special treatment */
    function addParentSelect2() {
        $('#id_parent').select2({
            dropdownCssClass: 'parent-element'
        });
    }

});
