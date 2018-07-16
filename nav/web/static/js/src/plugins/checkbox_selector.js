define([], function () {
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
        checkbox.change(function() {
            $(that.selector).prop("checked", checkbox.prop('checked'));
        });
    };

    return CheckboxSelector;

});
