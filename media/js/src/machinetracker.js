require(["libs/jquery.tablesorter.min"], function (tablesorter) {
        $(document).ready(function () {
            
            // Dict where key is the index of the column we do not want to sort
            columnsToNotSort = {};
            // Get all the th elements in the table
            headings = $('#tracker-table').children('thead').children('tr').children('th');

            // We do not want to sort columns without a heading, add them to dict
            $.each(headings, function(index, cell) {
                if(cell.innerHTML == "") 
                    columnsToNotSort[index] = {sorter : false};
            });
            
            // Enable tablesorter
            $('#tracker-table').tablesorter({
                headers: columnsToNotSort,
                widgets: ['zebra']});
            });
        });
