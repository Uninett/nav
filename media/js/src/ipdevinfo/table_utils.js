define(["libs/jquery-1.4.4.min"], function () {

    function TableUtil(node, limit) {
        this.node = node;
        this.limit = limit || 10;
        this.nodeTextShow = "Show all";
        this.nodeTextHide = "Show less";
    }

    TableUtil.prototype = {
        addRowToggleTrigger: function () {
            var container = $('tbody', this.node).length > 0 ? $('tbody', this.node) : this.node;
            var rows = $('tr', container);

            if (rows.length > this.limit) {
                var that = this;
                var colspan = rows.first().find('td').length;
                var hiddenRows = rows.slice(this.limit);
                var clickNode = createToggleRow(this.nodeTextShow, colspan);

                hiddenRows.hide();
                clickNode.toggle(function () {
                    hiddenRows.show();
                    $('.hellip', clickNode).hide();
                    $('.toggle-infotext', clickNode).text(that.nodeTextHide);
                }, function () {
                    hiddenRows.hide();
                    $('.hellip', clickNode).show();
                    $('.toggle-infotext', clickNode).text(that.nodeTextShow);
                });
                clickNode.appendTo(container);
            }
        }
    };

    function createToggleRow(nodeText, colspan) {
        var toggleRow = $('<tr class="toggletrigger"></tr>');
        var toggleCell = $('<td></td>');
        toggleCell.attr('colspan', colspan);
        toggleRow.append(toggleCell);
        toggleCell.append('<span class="hellip">&hellip;</span>',
            '<span class="toggle-infotext">' + nodeText + '</span>');
        return toggleRow;
    }

    return TableUtil

});
