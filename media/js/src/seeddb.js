require([
    'plugins/checkbox_selector', 'plugins/quickselect', 'libs/jquery', 'libs/jquery.dataTables.min', 'libs/FixedColumns.min'
], function (CheckboxSelector, QuickSelect) {
        $(function () {
            new CheckboxSelector('#select', '.selector').add();
            new QuickSelect('.quickselect');

            var table = $('#seeddb-content').dataTable({
                "bPaginate": true,
                "bLengthChange": true,
                "bFilter": false,
                "bSort": true,
                "bInfo": true,
                "bAutoWidth": true,
                "sDom": '<"top-left-side"i><"top-right-side"pl>t<"F">',
                "sScrollX": '100%',
                "aoColumnDefs": [
                    { 'bSortable': false, 'aTargets': [ 0 ] }
                ]
            });
            new FixedColumns(table, {
                "iLeftColumns": 2
            });
        });
    });
