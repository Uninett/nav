define(["libs/jquery-1.4.4.min"], function () {

    function TableUtil(node) {
        this.node = node;
    }

    TableUtil.prototype = {
        addRowToggleTrigger: function () {
            var clicknode = $('.toggletrigger', this.node);
            if (clicknode) {
                var rows = $('tr.hidden', this.node);
                var textnode = $('span.infotext', clicknode);
                var hellip = $('span.hellip', clicknode);
                var nodetext = '';

                $(clicknode).toggle(function () {
                    $(rows).show();
                    $(hellip).hide();
                    nodetext = $(textnode).text();
                    $(textnode).text('Show less');
                }, function () {
                    $(rows).hide();
                    $(hellip).show();
                    $(textnode).text(nodetext);
                });
            }
        }
    };

    return TableUtil

});
