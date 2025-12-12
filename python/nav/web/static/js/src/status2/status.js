require([
    'status/views',
    'libs/backbone',
], function (StatusView) {

    var selectors = {
        filterFormId: 'status-form', // Id of the form for filtering statuses
        filterClearId: 'clear-status-form', // Id of the button for clearing the form
        statelessDaysId: 'id_stateless_threshold' // Id of the stateless days input
    };

    /**
     * Clear, not reset, the status form.
     */
    function clearFilterForm() {
        var $form = $('#' + selectors.filterFormId);
        $form.find('.select2').each(function() {
            $(this).val(null).trigger('change');
        });
        $form.find('input:checkbox').removeAttr('checked');
        $form.find('#' + selectors.statelessDaysId).val('24');
    }

    /**
     * Wait for ready signal to start doing stuff
     */
    $(function() {
        console.log('Initializing app');
        var statusView = new StatusView();

        $('#' + selectors.filterClearId).click(clearFilterForm);
    });

});
