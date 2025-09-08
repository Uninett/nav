require(['libs/datatables.min', 'src/dt_plugins/ip_address_sort', 'src/dt_plugins/ip_address_typedetect'], function () {

    function initTimeField() {
        var time_field = $('#id_time_1');

        // Disable input if all time is pre-selected
        if ($('#id_time_0 :selected').val() === '') {
            time_field.attr('disabled', 'disabled');
        }

        $('#id_time_0').change(function() {
            var selected = $(this, 'option:selected');

            if (selected.val() === '') {
                time_field.val('');
                slack_help.hide();
                time_field.attr('disabled', 'disabled');
            } else {
                time_field.removeAttr('disabled');
                if (selected.val() === 'timestamp') {
                    time_field.val('YYYY-MM-DD hh:mm|slack');
                } else {
                    time_field.val('');
                }
            }
        });
    }
    function addTableCellListener(resulttable, datatable) {
        resulttable.on('click', 'td', function() {
            var filter = $(this).data('filter');
            if (filter) {
                datatable.fnFilter(filter);
            }
        });
    }
    function addFilterInputListener(resulttable, datatable) {
        var filter_input = $('#resulttable_filter input');
        filter_input.off();
        filter_input.keypress(function(e) {
            // i.e. enter was pressed
            if (e.keyCode === 13) {
                datatable.fnFilter(filter_input.val());
            }
        });
    }
    function initResulttable(resulttable) {
        // Add classes
        var nosort = resulttable.children('thead').data('nosort');

        // Iniialize
        var datatable = resulttable.dataTable({
            'iDisplayLength': 50,
            'bPaginate': false,
            "aaSorting": [],
            'aoColumnDefs': [
                {'bSortable': false, 'aTargets': nosort}
            ],
            'sDom': '<"ftable"<f><"info"i>>t',
            'oLanguage': {'sSearch': 'Filter results:'}
        });

        // Add listeners
        addTableCellListener(resulttable, datatable);
        addFilterInputListener(resulttable, datatable);
    }

    $(document).ready(function () {

        initTimeField();

        var resulttable = $('#resulttable');
        if (resulttable.length) {
            initResulttable(resulttable);
        }
    });
});
