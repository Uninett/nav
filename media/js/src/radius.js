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

        if ($('#resulttable').length) {

            // Add classes
            $.fn.dataTableExt.oStdClasses.sStripeOdd = 'oddrow';
            $.fn.dataTableExt.oStdClasses.sStripeEven = 'evenrow';

            // Iniialize
            var resulttable = $('#resulttable').dataTable({
                'iDisplayLength': 50,
                'sDom': '<"wrapper"lipftp>'
            });

            // Hack to change the label of the filter box
            var filter_label = $('#resulttable_filter label');
            filter_label.contents().filter(function() {
                return this.nodeType === Node.TEXT_NODE;
            }).remove();
            filter_label.prepend('Filter results:');

            // Register filter function
            $.fn.add_filter = function(text) {
                resulttable.fnFilter(text);
            };
        }
    });
});
