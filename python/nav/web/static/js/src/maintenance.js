require(['plugins/hover_highlight', "libs/jquery-ui-timepicker-addon"], function (HoverHighlight) {
    var calendar = $('.calendar');

    if (calendar.length) {
        new HoverHighlight(calendar);
    }

    $(document).ready(function(){
        $('#id_no_end_time').change(function(){
            toggleEndTime(this);
        });

        $('.datetimepicker').datetimepicker({
            'dateFormat': 'yy-mm-dd',
            'timeFormat': 'HH:mm'
        });
    });

    function toggleEndTime(checkBox){
        var endTime = $('#id_end_time');
        if ($(checkBox).prop('checked')){
            $(endTime).attr('disabled', 'disabled');
        } else {
            $(endTime).removeAttr('disabled');
        }
    }
});
