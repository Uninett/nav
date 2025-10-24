require([], function () {


    function addToggleFiltersListener() {
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
    }


    function addReportWidgetListener() {
        var $wrapper = $('#add-report-widget-wrapper'),
            $feedback = $wrapper.find('span'),
            $button = $wrapper.find('button');

        function displayFeedback() {
            $feedback.fadeIn('fast', function () {
                setTimeout(function () {
                    $feedback.fadeOut('slow');
                }, 2000);
            });
        }

        $button.click(function () {
            console.log("Adding widget");
            var request = $.post($button.data("report_url"), {
                report_id: $button.data("report_id"),
                query_string: $button.data("report_qs")
            });

            request.done(function () {
                $feedback.removeClass('error').addClass('success').text('Widget added');
                displayFeedback();
            });

            request.fail(function () {
                $feedback.removeClass('success').addClass('error').text('Error adding widget');
                displayFeedback();
            });
        });
    }


    function addTogglePageSizeListener() {
        var form = $('#reportPageSize');
        form.change(function(event) {
            var filters = $('#report_filters_form, #reportPageSize').serialize();
            window.location = window.location.pathname + '?' + filters;
        });
    }


    $(document).ready(function () {
        addToggleFiltersListener();
        addReportWidgetListener();
        addTogglePageSizeListener();
    });


});
