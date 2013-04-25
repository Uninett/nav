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
                { 'bSortable': false, 'sWidth': '16px', 'aTargets': [ 0 ] }  // Do not sort on first column
            ],
            "sPaginationType": "full_numbers", // Display page numbers in pagination
            "sDom": "<li>t<p>",   // display order of metainfo (lengthchange, info, pagination)
            "fnDrawCallback": function (oSettings) {
                /* Run this on redraw of table */
                $('.paginate_button').removeClass('disabled').addClass('button tiny');
                $('.paginate_active').addClass('button tiny secondary');
                $('.paginate_button_disabled').addClass('disabled');
                $(tableWrapper).removeClass('notvisible');
            },
            "aLengthMenu": [
                [10, 25, 50, -1],   // Choices for number of entries to display
                [10, 25, 50, "All"] // Text for the choices
            ],
            "oLanguage": {"sInfo": "_START_-_END_ of _TOTAL_"}  // Format of number of entries visibile
        });

        table.fnSort([[1, 'asc']]);  // When loaded, sort ascending on second column
        $(window).bind('resize', function () {
            /* Adjust table size when resizing window */
            table.fnAdjustColumnSizing();
        });
    }

});


