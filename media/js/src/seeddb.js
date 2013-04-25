require([
    'plugins/checkbox_selector', 'plugins/quickselect', 'libs/jquery', 'libs/jquery.dataTables.min', 'libs/FixedColumns.min'
], function (CheckboxSelector, QuickSelect) {
    var tableWrapper = '#tablewrapper';
    var tableSelector = '#seeddb-content';


    $(function () {
        new CheckboxSelector('#select', '.selector').add();
        var qSelect = new QuickSelect('.quickselect');

        if ($(tableSelector).find('tbody tr').length > 1) {
            enrichTable();
        } else {
            $(tableWrapper).removeClass('notvisible');
        }
    });


    function enrichTable() {
        /* Apply DataTable */
        var table = $(tableSelector).dataTable({
            "bPaginate": true,      // Pagination
            "bLengthChange": true,  // Change number of visible rows
            "bFilter": false,       // Searchbox
            "bSort": true,          // Sort when clicking on headers
            "bInfo": true,          // Show number of entries visible
            "bAutoWidth": true,     // Resize table
            "sScrollX": '100%',     // Scroll when table is bigger than viewport
            "aoColumnDefs": [
                { 'bSortable': false, 'aTargets': [ 0 ] }  // Do not sort on first column
            ],
            "sPaginationType": "full_numbers", // Display page numbers in pagination
            "sDom": "<lip>t",   // display order of metainfo (lengthchange, info, pagination)
            "fnDrawCallback": function (oSettings) {
                /* Run this on redraw of table */
                $('.paginate_button').removeClass('disabled').addClass('button tiny');
                $('.paginate_active').addClass('button tiny secondary');
                $('.paginate_button_disabled').addClass('disabled');
                $(tableWrapper).removeClass('notvisible');
            }
        });

        /* if the number of columns are bigger than two, fix the two first columns */
        if (table.fnGetData(0).length > 2) {
            var fixed = new FixedColumns(table, {
                "iLeftColumns": 2,       // Fix the two first columns
                "sHeightMatch": "auto"   // Calculate new height every time
            });
        }

    }

});


