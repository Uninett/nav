define([
    'plugins/quickselect',
    'libs-amd/text!testResources/templates/quickselect.html',
    'libs/jquery'], function (QuickSelect, html) {
    describe("QuickSelect", function () {
        beforeEach(function () {
            this.wrapper = $('<div></div>');
            this.html = $(html);
            this.wrapper.append(this.html);
            $('body').append(this.wrapper);
            new QuickSelect($('.quickselect', this.wrapper));

            this.searchbox = $('textarea.search', this.wrapper);
            this.textAreas = $('select', this.wrapper);
            this.clones = this.textAreas.clone();
        });

        afterEach(function () {
            this.wrapper.remove();
        });

        it("should add a search field", function() {
            assert($('div.quickselect > label', this.wrapper).length > 0);
        });

        it("should add a 'select all' button on textarea with multiple class", function() {
            assert.strictEqual($('select[multiple]', this.wrapper).parent('div').find('input[type=button]').length, 2);
        });

        it("should not add a 'select all' button on textarea without multiple class", function() {
            assert.strictEqual(this.textAreas.not('[multiple]').parent('div').find('input[type=button]').length, 0);
        });

        it("'select all' button should select all options in this textarea", function() {
            var parent = $('#id_room', this.wrapper).parent('div');

            /* Order is important here */
            this.searchbox.val('finland');
            this.searchbox.trigger('keyup', [this.textAreas, this.clones]);
            parent.find('input[type=button]').click();
            assert.strictEqual($('option:selected', parent).length, 2);
        });

        it("should have only one arrow in the label", function() {
            var arrowContainers = $('div.quickselect div > label', this.wrapper);
            var counter = 0;
            $('span', arrowContainers).each(function () {
                if ($(this).css('display') === 'none') {
                    counter++;
                }
            });
            assert.strictEqual(counter, 3);
        });

        it("should flip arrow on label click", function () {
            var label = $('label[for=id_room]', this.html);
            label.click();
            assert.isFalse(label.find('.downarrow').is(':visible'));
            assert.isTrue(label.find('.uparrow').is(':visible'));
        });

        it("should display the hidden select when label is clicked", function () {
            var label = $('label[for=id_room]', this.wrapper);
            label.click();
            assert.ok(label.parent().find('select').is(':visible'));
        });

        it("should set size on textarea to 10", function() {
            assert.strictEqual(this.textAreas.filter('[size=10]').length, this.textAreas.length);
        });

        describe("search", function () {
            it("should filter options when typing in search field", function () {
                this.searchbox.text('fa').keyup();
                assert.equal(this.html.find("[name='netbox'] option").length, 1);
            });
            it("should show all options when searching for nothing", function () {
                this.searchbox.text('fa').keyup();
                this.searchbox.text('').keyup();
                assert.equal(this.html.find("[name='netbox'] option").length, 3);
            });
            it("should work without optgroup", function () {
                this.searchbox.val('abs').keyup();
                assert.strictEqual($('option', this.textAreas).length, 1);
            });
            it("should work with several searchwords", function () {
                this.searchbox.val('absint alter').keyup();
                assert.strictEqual($('option', this.textAreas).length, 2);
            });
            it("should work with several searchwords on several textareas", function () {
                this.searchbox.val('absint bergen').keyup();
                assert.strictEqual($('option', this.textAreas).length, 2);
            });
            it("should work with optgroups", function () {
                this.searchbox.val('badeland tfoutrondheim').keyup();
                assert.strictEqual($('option', this.textAreas).length, 2);
            });
            it("should work on optgroups", function () {
                this.searchbox.val('finland').keyup();
                assert.strictEqual($('option', this.textAreas).length, 3);
            });

        });

    });
});
