/* Javascript forced and smeared on the Unrecognized Neighbors page. No tests, no fuzz :p */
require(['libs/jquery.dataTables.min'], function() {

    console.log('Neighbors script loaded');

    /* Global variables */
    var $table = $('#unrecognized-neighbors-table'),
        $tableBody = $table.find('tbody'),
        dataTable,

        // Elements regarding selection
        $selectAll = $('#select_all'),
        $ignoreSelected = $('#ignore-selected'),
        $unignoreSelected = $('#unignore-selected'),

        // Element for toggling display of ignored neighbors
        toggleIgnored = document.getElementById('toggle-ignored'),

        ignoredSinceIndex = 6,    // The index of the 'Ignored since' column

        setIgnoredUrl = NAV.urls.neighbors.neighbors_set_state;


    /** Apply all listeners */
    function applyListeners() {
        addToggleIgnoredHandler(dataTable);
        addToggleAllCheckBoxesListener();

        $ignoreSelected.click(function() {
            setIgnoredState('ignore');
        });

        $unignoreSelected.click(function() {
            setIgnoredState('unignore');
        });
    }


    /** Add handler for what happens when the toggleIgnored is clicked */
    function addToggleIgnoredHandler() {
        $('#toggle-ignored').click(function() {
            setIgnoredSinceVisibility();
            dataTable.fnDraw(); // Redraw table
        });
    }


    /** Set visibility on the 'ignored since' column based on toggleIgnored state */
    function setIgnoredSinceVisibility() {
        dataTable.fnSetColumnVis(ignoredSinceIndex, toggleIgnored.checked);
    }


    /** Listen to clicks on checkbox for toggling all checkboxes in column */
    function addToggleAllCheckBoxesListener() {
        $selectAll.on('change', function() {
            var checkboxes = $tableBody.find('input[type=checkbox]');
            if (this.checked) {
                checkboxes.prop('checked', true);
            } else {
                checkboxes.prop('checked', false);
            }
        });
    }

    /** Returns values of all checkboxes as a list */
    function getCheckboxIds(checkboxes) {
        return checkboxes.map(function() {
            return this.value;
        }).get();
    }

    function setIgnoredState(action) {
        var checkboxes = $tableBody.find(':checked');

        if (checkboxes.length <= 0) {
            return;
        }

        var neighborids = getCheckboxIds(checkboxes),
            $rows = checkboxes.closest('tr');

        var request = $.post(setIgnoredUrl, {
            neighborids: neighborids,
            action: action
        });

        request.done(function(response) {
            console.log('Request was successful');

            // Reset all checkboxes
            checkboxes.prop('checked', false);
            $selectAll.prop('checked', false);

            // Update datasets with new values. Set value of ignored since column
            if (action === 'ignore') {
                $rows.each(function() {
                    this.dataset.ignored = 'true';
                    dataTable.fnUpdate(response, this, ignoredSinceIndex, false);
                });
            } else {
                $rows.each(function() {
                    this.dataset.ignored = 'false';
                    dataTable.fnUpdate('', this, ignoredSinceIndex, false);
                });
            }
            dataTable.fnDraw();
        });
        
        request.fail(function() {
            console.log('Request failed');
        });

    }

    /** Apply datatables plugin to table */
    function applyDatatable() {
        // Register new filtering function based on neighbor state
        $.fn.dataTableExt.afnFiltering.push(filterNeighborState);

        return $table.dataTable({
            "bFilter": true,      // Explicitly set filtering
            "bSort": true,        // Explicitly set sorting
            "bPaginate": false,   // Do not show pagination
            "bAutoWidth": false,  // Do not calculate row width
            "oLanguage": {
                "sInfo": "_TOTAL_ neighbors",  // Format for number of entries visible
                "sSearch": "Filter:"
            },
            "aoColumnDefs": [
                { 'bSortable': false, 'aTargets': [ 0 ] }  // Do not sort on first column
            ]
        });
    }


    /**
     * Filter rows based on neighbor state. This function is called
     * for every filtering event
     */
    function filterNeighborState(oSettings, aData, iDataIndex) {
        var row = oSettings.aoData[iDataIndex].nTr;

        if (toggleIgnored.checked) {
            return true;        // Show everything
        } else {
            return row.dataset.ignored === 'false';
        }
    }


    /** If a query parameter named filter is found, use that to run an initial filter */
    function filterQueryParameters(dataTable) {
        var params = window.location.search.substr(1).split('=');
        if (params[0] === 'filter') {
            dataTable.fnFilter(params[1]);
        }
    }

    /** On page ready the following happens */
    $(function() {
        console.log('Neighbors ready');

        dataTable = applyDatatable();
        setIgnoredSinceVisibility();
        applyListeners();

        filterQueryParameters(dataTable);

        $table.show();
        console.log('Neighbors done initializing');
    });


});
