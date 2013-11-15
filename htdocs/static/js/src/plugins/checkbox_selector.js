define(['libs/jquery'], function () {
    /*
     * Create a checkbox on node, that when clicked on
     * checks and unchecks the checkboxes with selector
     */

    function CheckboxSelector(node, selector) {
        this.node = typeof node === 'string' ? $(node) : node;
        this.selector = selector;
    }

    CheckboxSelector.prototype.add = function () {
        var checkbox = $('<input type="checkbox"/>');
        var that = this;
        this.node.append(checkbox);
        checkbox.click(function() {
            if (checkbox.prop('checked')) {
                $(that.selector).attr("checked", "checked");
            } else {
                $(that.selector).removeAttr("checked");
            }
        });
    };

    return CheckboxSelector;

});
