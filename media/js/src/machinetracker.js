require(["libs/jquery.tablesorter.min"], function (tablesorter) {
        $(document).ready(function () {
            $('#tracker-table').tablesorter({
                headers: {2: {sorter:false}},
                widgets: ['zebra']});
            });
        });
