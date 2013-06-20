require(["libs/jquery-ui-timepicker-addon"], function () {
    $(function () {
        $('.datetimepicker').datetimepicker({ 
            'dateFormat': 'yy-mm-dd',
            'timeFormat': 'HH:mm'
            });
    }); 
});

