/* Javascript forced and smeared on the Unrecognized Neighbors page. No tests, no fuzz :p */
require(['libs/jquery'], function() {

    console.log('Neighbors script loaded');

    /* Some global variables */
    var $globalError = $('.global-neighbor-error'),
        $table = $('#unrecognized-neighbors-table'),
        $tableCaption = $table.find('caption'),
        $captionLength = $($tableCaption.find('span')[0]),
        $captionText = $($tableCaption.find('span')[1]),
        $tableBody = $table.find('tbody'),
        setIgnoredUrl = NAV.urls.neighbors.neighbors_set_state,
        fetchNeighborsUrl = NAV.urls.neighbors.neighbors_render_tbody,
        showUnrecognizedButton = $('#show-unrecognized-button'),
        showIgnoredButton = $('#show-ignored-button');


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


    /** Add handlers for displaying ignored and unignored neighbors */
    function addButtonGroupHandlers() {
        showUnrecognizedButton.on('click', function() {
            fetchNeighbors(false, setUnrecognizedMode);
        });
        showIgnoredButton.on('click', function() {
            fetchNeighbors(true, setIgnoredMode);
        });
    }


    /** Alter other parts of the page when going in unrecognized mode */
    function setUnrecognizedMode() {
        showUnrecognizedButton.addClass('active');
        showIgnoredButton.removeClass('active');
        updateCaption('unrecognized neighbors');
    }


    /** Alter other parts of the page when going in ignored mode */
    function setIgnoredMode() {
        showIgnoredButton.addClass('active');
        showUnrecognizedButton.removeClass('active');
        updateCaption('hidden neighbors');
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


    /** Repopulate the table body with html with neighbors */
    function fetchNeighbors(ignored, successAction) {
        $globalError.hide();

        var request = $.get(fetchNeighborsUrl, {
            ignored: ignored
        });

        request.done(function(data) {
            renderResponse(data);
            successAction();
        });

        request.fail(function() {
            renderErrorResponse();
        });
    }


    /** Render successful response when fetching neighbors */
    function renderResponse(data) {
        $tableBody.empty().append(data);
    }


    function renderErrorResponse() {
        $globalError.show().html(
            "Error loading unrecognized neighbors"
        );
    }


    /* On page ready the following happens */
    $(function() {
        console.log('Neighbors ready');
        addIgnoreNeighborsHandlers();
        addButtonGroupHandlers();
    });


});
