require(['libs/jquery'], function () {
    $(document).ready(function () {
        $('#advToggle').click(function() {
            $('#advblock').toggle();
            var old_text = $(this).html().trim();
            var new_text;
            if (old_text === 'Report filters') {
                new_text = 'Close report filters';
            }
            else {
                new_text = 'Report filters';
            }
            $(this).html(new_text);
        });
    });
});
