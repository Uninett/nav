require(["libs/jquery.tablesorter.min", "libs/jquery"], function (tablesorter) {

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
            $trackerTable = $('#tracker-table'),
            headings = $trackerTable.children('thead').children('tr').children('th');

        // We don't sort the icon cell and sort IP as text from the span
        $.each(headings, function(index, cell) {
            if(cell.innerHTML === "") {
                headerData[index] = {sorter : false};
            }

            if (cell.innerHTML === "IP") {
                textExtractionData[index] = function(node){
                    return $(node).find('span').text();
                };
                headerData[index] = {sorter: 'text', string: 'min'};
            }
        });

        // Enable tablesorter
        $trackerTable.tablesorter({
            headers: headerData,
            textExtraction: textExtractionData,
            widgets: ['zebra']
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
