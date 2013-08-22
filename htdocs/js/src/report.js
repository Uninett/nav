require(['libs/jquery'], function () {
    $(document).ready(function () {
        $('#advToggle').click(function() {
            $('#advblock').toggle();
            var old_text = $(this).html().trim();
            var new_text;
            if (old_text === 'Advanced Options') {
                new_text = 'Close Advanced Options';
            }
            else {
                new_text = 'Advanced Options';
            }
            $(this).html(new_text);
        });
    });
});
