define(["jquery"], function () {

    function TableUtil(node, limit) {
        this.node = node;
        this.limit = limit || 10;
    }

    TableUtil.prototype = {
        addRowToggleTrigger: function () {
            var container = $('tbody', this.node).length > 0 ? $('tbody', this.node) : this.node;
            var rows = $('tr', container);

            if (rows.length > this.limit) {
                var that = this;
                var colspan = rows.first().find('td').length;
                var numRows = rows.length;
                var hiddenRows = rows.slice(this.limit);
                var clickNode = createToggleRow(getShowText(numRows), colspan);

                hiddenRows.hide();
                clickNode.toggle(function () {
                    hiddenRows.show();
                    $('.hellip', clickNode).hide();
                    $('.toggle-infotext', clickNode).text(getHideText());
                }, function () {
                    hiddenRows.hide();
                    $('.hellip', clickNode).show();
                    $('.toggle-infotext', clickNode).text(getShowText(numRows));
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

        var hellip = $('<span class="hellip">&hellip;</span>');
        var infoText = $('<span class="toggle-infotext">' + nodeText + '</span>');
        toggleCell.append(hellip, infoText);
        return toggleRow;
    }

    function getShowText(numRows) {
        return "Show all " + numRows + " rows";
    }

    function getHideText() {
        return "Show less";
    }

    return TableUtil

});
