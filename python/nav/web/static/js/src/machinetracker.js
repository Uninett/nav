require(["src/libs/tablesort_extensions", "jquery"], function (tablesort) {

    var ns = "nav.machinetracker",
        elementIds = ['id_netbios', 'id_dns'],
        searchFormId = 'search_form';

    /**
     * Enable setting and getting of local search settings (checkboxes only)
     * using localstorage. Do not do this when following links, only on clean
     * url
     */
    function addLocalStateSettings() {
        var form = $('#' + searchFormId);
        if (!window.location.search && window.localStorage && form.length) {
            addSettingsListener(form);
            setElementState();
        }
    }

    /**
     * Add listener for changes in selected elements. Store changes in
     * localstorage.
     */
    function addSettingsListener(form) {
        form.on('change', function(event) {
            var element = event.target;
            if (elementIds.indexOf(element.id) >= 0) {
                localStorage.setItem(getKey(element), element.checked);
            }
        });
    }

    /**
     * Set element checked state based on localstorage
     */
    function setElementState() {
        for(var i = 0, l = elementIds.length; i < l; i++) {
            var element = document.getElementById(elementIds[i]);
            if (element) {
                element.checked = getLocalSetting(element);
            }
        }
    }

    /**
     * Returns the value of the local setting
     * @param {object} element A DOM element with an ID attribute
     * @returns {boolean}
     */
    function getLocalSetting(element) {
        return localStorage.getItem(getKey(element)) === 'true';
    }

    /**
     * Create the key used for storing the state of this element in
     * localstorage
     * @param {object} element A DOM element with an ID attribute
     * @returns {string}
     */
    function getKey(element) {
        return [ns, element.id].join('.');
    }


    $(document).ready(function () {

        // Data parameters for tablesorter
        var headerData = {},
            textExtractionData = {},
            trackerTable = document.getElementById('tracker-table');

        if (!trackerTable) {
            addLocalStateSettings();
            return;
        }

        const headings = trackerTable.querySelectorAll('thead tr th');

        // Configure sorters based on column headers
        headings.forEach(function(cell, index) {
            const header = cell.innerHTML.trim();

            if (header === "") {
                headerData[index] = { sorter: false };
            } else if (header === "IP") {
                textExtractionData[index] = function(node) {
                    const span = node.querySelector('span');
                    return span ? span.textContent : node.textContent;
                };
                headerData[index] = { sorter: 'ip-address' };
            } else if (header === "Start time" || header === "End time") {
                headerData[index] = { sorter: 'iso-datetime' };
            }
        });

        tablesort.init(trackerTable, {
            headers: headerData,
            textExtraction: textExtractionData
        });

        // If the form is reloaded, display correct data
        var $days = $('#id_days'), $hide = $('#id_hide');
        if ($days.val() === "-1") {
            $hide.attr('checked', 'true');
            $days.attr('disabled', 'disabled');
            $days.val("7");
        }

        addLocalStateSettings();

    });

});
