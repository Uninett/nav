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
    function addIgnoreNeighborsHandlers() {
        // When ignore button is clicked, save neighbor state
        $tableBody.on('click', '.ignore-neighbor', function(event) {
            var $row = $(event.target).closest('tr');
            setIgnored($row, true);
        });

        $tableBody.on('click', '.unignore-neighbor', function(event) {
            var $row = $(event.target).closest('tr');
            setIgnored($row, false);
        });

    }


    /** Set ignored state on neighbor by executing a request to controller */
    function setIgnored($row, ignored) {
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
                updateCaption();
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


    /** Updates the caption with the premise that number of rows is important */
    function updateCaption(text) {
        $captionLength.html(findNumberOfRows());
        if (typeof text !== 'undefined') {
            $captionText.html(text);
        }
    }


    /** Returns the number of rows in the table */
    function findNumberOfRows() {
        return $tableBody.find('tr:visible').length;
    }


    /** Apply datatables plugin to table */
    function applyDatatable() {
        $table.dataTable({
            "bPaginate": false,  //  Do not show pagination
            "bInfo": false,      //  Do not show number of (filtered) results
            "bAutoWidth": false  //  Do not calculate row width
        });
    }


    /** Display the table */
    function showTable() {
        $table.show();
    }


    /* On page ready the following happens */
    $(function() {
        console.log('Neighbors ready');
        addIgnoreNeighborsHandlers();
        applyDatatable();
        showTable();
    });


});
