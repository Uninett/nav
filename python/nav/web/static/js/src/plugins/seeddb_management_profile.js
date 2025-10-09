require([],
function () {

    function executeOnLoad() {
        /**
         * Verifies we're on the Management Profiles edit form page before
         * initializing the magic form switching code.
         */
        var $formElement = $('#seeddb-management-profile-form')
        if ($formElement.length) {
            protocolChanged();
            $('#id_protocol').change(protocolChanged);
        }
    }

    function protocolChanged() {
        var $selected_protocol = $('#id_protocol').val();
        $('fieldset.protocol-configuration').hide();
        $('fieldset.protocol-configuration input').prop("disabled", true);
        var $show_id = '#protocol-' + $selected_protocol;
        console.log('Enabling ' + $show_id);
        $($show_id + ' input').prop("disabled", false);
        $($show_id).show();

    }

    /* Internet Explorer caching leads to onload event firing before
     * script is loaded - thus we never get the load event. This code
     * will at least make it usable. */
    if (document.readyState === 'complete') {
        executeOnLoad();
    } else {
        $(window).on('load', executeOnLoad);
    }

});
