require([
    'plugins/seeddb_datatables',
    'plugins/checkbox_selector',
    'plugins/seeddb_hstore',
    'plugins/seeddb_management_profile',
    'plugins/seeddb_map'],
function (datatables, CheckboxSelector, FormFuck, ManagementProfile, seedDBRoomMap) {

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
        $(window).on('load', executeOnLoad);
    }


    /**
     * Uses select2 to search for and display netboxes. Executes the search in
     * AJAX-requests.
     */
    function initDeviceGroupSelectMultiple($formElement, $searchField) {
        // Pre-populate with existing selections from the form element
        const initialData = [];
        $formElement.find(':selected').each(function (index, option) {
            initialData.push({
                id: option.value,
                text: option.innerHTML
            });
        });

        $searchField.select2({
            multiple: true,
            ajax: {
                url: NAV.urls.api_netbox_list,
                dataType: 'json',
                delay: 250,
                data: function(params) {
                    return {
                        search: params.term
                    };
                },
                processResults: netboxListSelect2
            },
            minimumInputLength: 3
        });

        // Set initial selection if there are pre-selected values
        if (initialData.length > 0) {
            // For Select2 v4, we need to add option elements and trigger change
            initialData.forEach(function(item) {
                if ($searchField.find('option[value="' + item.id + '"]').length === 0) {
                    const option = new Option(item.text, item.id, true, true);
                    $searchField.append(option);
                }
            });
            $searchField.trigger('change');
        }

        /**
         * Sets the selected values in the form element to be the same as in
         * the select2 element when the form is submitted.
         */
        $('form.seeddb-edit').submit(function () {
            $formElement.val($searchField.val());
        });
    }

    function activateIpDeviceFormPlugins() {
        // The connectivity checker
        var $form = $('#seeddb-netbox-form'),
            $addressField = $('#id_ip');

        $form.on('submit', function (event, validated) {
            if (!validated) {
                event.preventDefault();
                const verification = $.get(
                    NAV.urls.seeddb.validateIpAddress,
                    {'address': $addressField.val()}
                );
                verification.done(function () {
                    $form.trigger('submit', true);
                })
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

    function netboxListSelect2(data, _params) {
        const results = data.results;
        results.sort(function(a, b) {
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

    function initSearchForIpDevice() {
        $('#id_netbox').select2({
            placeholder: 'Search for IP device',
            minimumInputLength: 3,
            ajax: {
                url: NAV.urls.api_netbox_list,
                dataType: 'json',
                delay: 250,
                data: function(params) {
                    return {
                        search: params.term
                    };
                },
                processResults: netboxListSelect2
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
