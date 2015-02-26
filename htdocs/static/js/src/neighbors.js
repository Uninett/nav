/* Javascript forced and smeared on the Unrecognized Neighbors page. No tests, no fuzz :p */
require(['libs/jquery', 'libs/jquery.dataTables.min'], function() {

    console.log('Neighbors script loaded');

    /* Some global variables */
    var $table = $('#unrecognized-neighbors-table'),
        $tableCaption = $table.find('caption'),
        $captionLength = $($tableCaption.find('span')[0]),
        $captionText = $($tableCaption.find('span')[1]),
        $tableBody = $table.find('tbody'),
        setIgnoredUrl = NAV.urls.neighbors.neighbors_set_state;


    /** Add event listeners to table for manipulating neighbor ignored state */
    function addIgnoreNeighborsHandlers(dataTable) {
        // When ignore button is clicked, save neighbor state
        $tableBody.on('click', '.ignore-neighbor', function(event) {
            var $row = $(event.target).closest('tr');
            setIgnored($row, true, dataTable);
        });

        $tableBody.on('click', '.unignore-neighbor', function(event) {
            var $row = $(event.target).closest('tr');
            setIgnored($row, false, dataTable);
        });

    }


    /** Set ignored state on neighbor by executing a request to controller */
    function setIgnored($row, ignored, dataTable) {
        console.log('setIgnored');

        // Remove any previous errors
        $row.find('.action-cell .alert-box').remove();

        var request = $.post(setIgnoredUrl, {
            neighborid: $row.data('neighborid'),
            ignored: ignored
        });

        // When request is done successfully, fade out the row
        request.done(function() {
            console.log('Request was successful');
            $row.fadeOut(function() {
                dataTable.fnDeleteRow($row.get(0)); // Delete row to update counter
            });
        });

        // In case of error give user feedback
        request.fail(function() {
            console.log('Request was not successful');
            $row.find('.action-cell').append(
                $('<span class="alert-box alert" style="display: inline">Error altering neighbor</span>')
            );
        });
    }

    /** Apply datatables plugin to table */
    function applyDatatable() {
        return $table.dataTable({
            "bFilter": true,      // Explicitly set filtering
            "bSort": true,        // Explicitly set sorting
            "bPaginate": false,   // Do not show pagination
            "bAutoWidth": false,  // Do not calculate row width
            "sDom": 'fit',  //  Put filter and info at the top of the table
            "oLanguage": {
                "sInfo": "_TOTAL_ unrecognized neighbors"  // Format number of entries visibile
            },
            "aoColumnDefs": [
                { 'bSortable': false, 'aTargets': [ -1 ] }  // Do not sort on last column
            ]
        });
    }


    /** Display the table */
    function showTable() {
        $table.show();
    }


    /* On page ready the following happens */
    $(function() {
        console.log('Neighbors ready');
        addIgnoreNeighborsHandlers(applyDatatable());
        showTable();
    });


});
