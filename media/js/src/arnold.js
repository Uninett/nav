require(['libs/jquery'], function () {
    $(function () {
        if ($('form.profileDetentionForm').length > 0) {
            addVlanToggler('#id_detention_type_0', '#id_detention_type_1', '.vlanrow')
        }
        if ($('form.manualDetentionForm').length > 0) {
            addVlanToggler('#id_method_0', '#id_method_1', '.vlanrow')
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
