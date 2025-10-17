define(['plugins/checkbox_selector', 'jquery'], function (CheckboxSelector) {
    describe("Checkbox Selector", function () {
        beforeEach(function () {
            this.table = $('<table><tr><th id="blapp"></th></tr><tr><td><input type="checkbox" class="selector" /><input type="checkbox" class="selector" /></td></tr></table>');
            $('body').append(this.table);
            this.cs = new CheckboxSelector($("#blapp", this.table), '.selector');
            this.cs.add();
        });
        it("should create a checkbox in the node", function () {
            assert.strictEqual(
                this.table.find('#blapp input[type=checkbox]').length, 1);
        });
        it("should toggle on all the other checkboxes based on main one", function () {
            var mainCheckbox = this.table.find('#blapp input[type=checkbox]');
            mainCheckbox.click();
            var toggled = 0;
            this.table.find('.selector').each(function () {
                if ($(this).prop('checked')) {
                    toggled++;
                }
            });
            assert.equal(toggled, 2);
        });
        afterEach(function () {
           $('body').empty();
        });
    });
});
