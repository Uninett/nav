require(['libs/jquery', 'libs/jquery.tablesorter.min'], function () {
    $(function () {
        if ($('form.profileDetentionForm').length > 0) {
            addVlanToggler('#id_detention_type_0', '#id_detention_type_1', '.vlanrow')
        }
        if ($('form.manualDetentionForm').length > 0) {
            addVlanToggler('#id_method_0', '#id_method_1', '.vlanrow')
        }

        // Add tablesorter to history table
        if ($('.arnold-history tbody').length > 0) {
            $('.arnold-history').tablesorter({
                headers: {
                    0: { sorter: 'ipAddress'},
                    8: { sorter: false}
                }
            });
        }

        // Add tablesorter to detained ports table
        if ($('.arnold-detainedports tbody').length > 0) {
            $('.arnold-detainedports').tablesorter({
                headers: {
                    0: { sorter: 'ipAddress'},
                    7: { sorter: false},
                    8: { sorter: false}
                }
            });
        }

    });

    function addVlanToggler(hideNode, showNode, node) {
        if ($(hideNode).prop('checked')) {
            $(node).hide();
        }
        $(hideNode).click(function () {
            $(node).hide()
        });
        $(showNode).click(function () {
            $(node).show()
        })
    }

});
