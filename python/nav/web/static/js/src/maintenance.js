require(['plugins/quickselect', 'plugins/hover_highlight', "libs/jquery-ui-timepicker-addon"], function (QuickSelect, HoverHighlight) {
    var calendar = $('.calendar');
    var quickselect = $('.quickselect');

    if (calendar.length) {
        new HoverHighlight(calendar);
    }

    if (quickselect.length) {
        new QuickSelect(quickselect);
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
