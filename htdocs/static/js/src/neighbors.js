/* Javascript forced and smeared on the Unrecognized Neighbors page. No tests, no fuzz :p */
require(['libs/jquery.dataTables.min'], function() {

    console.log('Neighbors script loaded');

    /* Global variables */
    var $table = $('#unrecognized-neighbors-table'),
        $tableBody = $table.find('tbody'),

        // Elements regarding selection
        $selectAll = $('#select_all'),
        $ignoreSelected = $('#ignore_selected'),
        $unignoreSelected = $('#unignore_selected'),

        // definitions
        stateActive = 'active',
        stateIgnored = 'ignored',
        stateActiveText = 'Ignore',
        stateIgnoredText = 'Unignore',

        // Element for toggling display of ignored neighbors
        toggleIgnored = document.getElementById('toggle-ignored'),

        ignoredSinceIndex = 6,    // The index of the 'Ignored since' column

        setIgnoredUrl = NAV.urls.neighbors.neighbors_set_state;


    function addToggleAllCheckBoxesListener() {
        $selectAll.on('click', function() {
            var checkboxes = $tableBody.find('input[type=checkbox]');
            if (this.checked) {
                checkboxes.prop('checked', true);
            } else {
                checkboxes.prop('checked', false);
            }
        });
    }


    function ignoreSelected() {
        
    }


    /** Set ignored state on neighbor by executing a request to controller */
    function setIgnored($row, $button, ignored, dataTable) {
        var row = $row[0];

        $button.prop('disabled', true); // Disable button to avoid spamming for requests
        $row.find('.action-cell .alert-box').remove(); // Remove any previous error messages

        var request = $.post(setIgnoredUrl, {
            neighborid: $row.data('neighborid'),
            ignored: ignored
        });

        // When request is done successfully
        request.done(function(response) {
            console.log('Request was successful');
            // To avoid confusion because a row instantly disappears,
            // fade it out when not displaying all rows
            if (ignored === true && !toggleIgnored.checked) {
                $row.fadeOut(function() {
                    dataTable.fnUpdate(response, row, ignoredSinceIndex);
                    $row.show(); // Fadeout hides the row forever. Fix that.
                });
            } else {
                dataTable.fnUpdate(response, row, ignoredSinceIndex);
            }
        });

        // In case of error give user feedback
        request.fail(function() {
            console.log('Request was not successful');
            $row.find('.action-cell').append(
                $('<span class="alert-box alert" style="display: inline">Error altering neighbor</span>')
            );
        });

        request.always(function() {
            $button.prop('disabled', false); // Re-enable button
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
            "sDom": 'fit',  //  Put filter and info at the top of the table
            "oLanguage": {
                "sInfo": "_TOTAL_ neighbors"  // Format for number of entries visible
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
            return row.dataset.ignored.trim() === '';
        }
    }


    /** Add handler for what happens when the toggleIgnored is toggled */
    function addToggleIgnoredHandler(dataTable) {
        $('#toggle-ignored').click(function() {
            setIgnoredSinceVisibility(dataTable);
            dataTable.fnDraw(); // Redraw table
        });
    }


    /** Set visibility on the 'ignored since' column based on toggleIgnored state */
    function setIgnoredSinceVisibility(dataTable) {
        dataTable.fnSetColumnVis(ignoredSinceIndex, toggleIgnored.checked);
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

        var dataTable = applyDatatable();
        setIgnoredSinceVisibility(dataTable);
        addToggleIgnoredHandler(dataTable);
        addToggleAllCheckBoxesListener();

        filterQueryParameters(dataTable);

        $table.show();
        console.log('Neighbors done initializing');
    });


});
