require(['libs/jquery', 'libs/jquery.dataTables.min'], function () {
    $(document).ready(function () {

        var time_field = $('#id_time_0');
        var slack_help = $('a.tooltip');

        if ($('#id_time_1 :selected').val() === '') {
            time_field.attr('disabled', 'disabled');
        }

        $('#id_time_1').change(function() {
            var selected = $(this, 'option:selected');

            if (selected.val() === '') {
                time_field.val('');
                slack_help.hide();
                time_field.attr('disabled', 'disabled');
            } else {
                time_field.removeAttr('disabled');
                if (selected.val() === 'timestamp') {
                    time_field.val('YYYY-MM-DD hh:mm|slack');
                    slack_help.show();
                } else {
                    time_field.val('');
                    slack_help.hide();
                }
            }
        });

        var resulttable = $('#resulttable');
        if (resulttable.length) {

            // Add classes
            $.fn.dataTableExt.oStdClasses.sStripeOdd = 'oddrow';
            $.fn.dataTableExt.oStdClasses.sStripeEven = 'evenrow';
            $.fn.dataTableExt.oStdClasses.sSortAsc = 'headerSortDown';
            $.fn.dataTableExt.oStdClasses.sSortDesc = 'headerSortUp';


            var nosort = resulttable.children('thead').data('nosort');

            // Iniialize
            var datatable = resulttable.dataTable({
                'iDisplayLength': 50,
                'bPaginate': false,
                "aaSorting": [],
                'aoColumnDefs': [
                    {'bSortable': false, 'aTargets': nosort}
                ],
                'sDom': '<"caption"<"info"i><"filter"f>>t'
            });

            // Hack to change the label of the filter box
            var filter_label = $('#resulttable_filter label');
            filter_label.contents().filter(function() {
                return this.nodeType === Node.TEXT_NODE;
            }).remove();
            filter_label.prepend('Filter results:');
            filter_label.append(
                '<button type="button" onclick="javascript:$.fn.add_filter(\'\')">clear</button>'
            );

            // Set caption width to the table width
            $('.caption').css('width', function() {
               return resulttable.css('width');
            });

            // Register filter function
            $.fn.add_filter = function(text) {
                datatable.fnFilter(text);
            };
        }
    });
});
