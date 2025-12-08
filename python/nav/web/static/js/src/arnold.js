require(['jquery-tablesorter'], function () {
    $(function () {
        if ($('form.profileDetentionForm').length > 0) {
            addVlanToggler($('#id_detention_type'));
        }
        if ($('form.manualDetentionForm').length > 0) {
            addVlanToggler($('#id_method'));
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

    function addVlanToggler($selectNode) {
        var $row = $('.qvlanrow');
        if ($selectNode.val() !== 'quarantine') {
            $row.addClass('hidetrick');
        }
        $selectNode.change(function () {
            var $this = $(this);
            if ($this.val() === 'quarantine') {
                $row.removeClass('hidetrick');
            } else {
                $row.addClass('hidetrick');
            }
        });
    }

});
