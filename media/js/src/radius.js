require(['libs/jquery', 'libs/jquery.dataTables.min'], function () {
    $(document).ready(function () {

        var time_field = $('#id_time_0');

        if ($('#id_time_1 :selected').val() === '') {
            time_field.attr('disabled', 'disabled');
        }

        $('#id_time_1').change(function() {
            var selected = $(this, 'option:selected');

            if (selected.val() === '') {
                time_field.val('');
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

        if ($('#resulttable').length) {
            $('#resulttable').dataTable({
                'iDisplayLength': 50,
                'sStripeOdd': 'oddrow',
                'sStripeEven': 'evenrow'
            });
        }
    });
});
