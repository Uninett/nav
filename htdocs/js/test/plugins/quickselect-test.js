define(['plugins/quickselect', 'libs/jquery'], function (QuickSelect) {
    describe("QuickSelect", function () {
        beforeEach(function () {
            this.wrapper = $('<div></div>');
            var html ='<div class="quickselect">' +
                '<div><label for="id_netbox">IP device</label>' +
                '<select size="5" name="netbox" id="id_netbox">' +
                '<option value="1">absint.online.ntnu.no</option>' +
                '<option value="2">altersex.samfundet.no</option>' +
                '<option value="3">fattimainn-gw.uninett.no</option>' +
                '</select>' +
                '<p><input type="submit" name="submit_netbox" value="Add IP device"></p>' +
                '</div>' +
                '<div class="collapse">' +
                '<label for="id_loc">Location</label>' +
                '<select multiple="multiple" size="5" name="loc" id="id_loc">' +
                '<option value="bergen">bergen (Bergen)</option>' +
                '<option value="finland">finland (vodkaland)</option>' +
                '<option value="hochhaus">hochhaus (ich haben eels in mein hovercraft)</option>' +
                '</select>' +
                '<p><input type="submit" name="submit_loc" value="Add location"></p>' +
                '</div>' +
                '<div class="collapse">' +
                '<label for="id_room">Location</label>' +
                '<select multiple="multiple" size="10" name="room" id="id_room" style="display: block; ">' +
                '<optgroup label="finland (vodkaland)">' +
                '<option value="sauna">sauna ()</option>' +
                '<option value="someroom">someroom (Ett rom!)</option>' +
                '</optgroup>' +
                '<optgroup label="nordavind (kald)">' +
                '<option value="badeland">badeland ()</option>' +
                '</optgroup>' +
                '<optgroup label="norge (Norge)">' +
                '<option value="tfoutrondheim">tfoutrondheim (Otto Nielsens vei 12)</option>' +
                '</optgroup>' +
                '</select>' +
                '<p><input type="submit" name="submit_room" value="Add room"></p>' +
                '</div>';
                '</div>';

            this.html = $(html);
            this.wrapper.append(this.html);
            new QuickSelect($('.quickselect', this.wrapper));

            this.searchbox = $('textarea.search', this.wrapper);
            this.textAreas = $('select', this.wrapper);
            this.clones = this.textAreas.clone();
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
        it("only one arrow should be visible in the label", function() {
            var arrowContainers = $('div.quickselect div > label', this.wrapper);
            var counter = 0;
            $('span', arrowContainers).each(function () {
                if ($(this).css('display') === 'none') {
                    counter++;
                }
            });
            assert.strictEqual(counter, 3);
        });
        it("should set size on textarea to 10", function() {
            assert.strictEqual(this.textAreas.filter('[size=10]').length, this.textAreas.length);
        });
        it("should work without optgroup", function() {
            this.searchbox.val('abs');
            this.searchbox.trigger('keyup', [this.textAreas, this.clones]);
            assert.strictEqual($('option', this.textAreas).length, 1);
        });
        it("should work with several searchwords", function() {
            this.searchbox.val('absint alter');
            this.searchbox.trigger('keyup', [this.textAreas, this.clones]);
            assert.strictEqual($('option', this.textAreas).length, 2);
        });
        it("should work with several searchwords on several textareas", function() {
            this.searchbox.val('absint bergen');
            this.searchbox.trigger('keyup', [this.textAreas, this.clones]);
            assert.strictEqual($('option', this.textAreas).length, 2);
        });
        it("should work with optgroups", function() {
            this.searchbox.val('badeland tfoutrondheim');
            this.searchbox.trigger('keyup', [this.textAreas, this.clones]);
            assert.strictEqual($('option', this.textAreas).length, 2);
        });
        it("should work on optgroups", function() {
            this.searchbox.val('finland');
            this.searchbox.trigger('keyup', [this.textAreas, this.clones]);
            assert.strictEqual($('option', this.textAreas).length, 3);
        });
    });
});
