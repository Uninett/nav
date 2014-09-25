require(["libs/jquery.tablesorter.min", "libs/jquery"], function (tablesorter) {
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
    });

});

