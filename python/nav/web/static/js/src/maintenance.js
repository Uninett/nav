require(['plugins/hover_highlight', "flatpickr"], function (HoverHighlight, flatpickr) {
    var calendar = $('.calendar');

    if (calendar.length) {
        new HoverHighlight(calendar);
    }

    $(document).ready(function(){
        $('#id_no_end_time').change(function(){
            toggleEndTime(this);
        });

        flatpickr('.datetimepicker', {
            enableTime: true,
            dateFormat: "Y-m-d H:i",
            time_24hr: true,
            allowInput: true
        })
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
