define(["jquery"], function () {
    function CounterDisplay(template, parentId, value, unit) {
        this.template = template;
        this.unit = unit;
        this.node = $('#' + parentId);
        this.refresh(value);
    }

    CounterDisplay.prototype.refresh = function (value) {
        this.node.html(this.template({ 'value': value, 'unit': this.unit }));
    };

    return CounterDisplay;

});
