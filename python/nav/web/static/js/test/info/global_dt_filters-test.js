
define(['info/global_dt_filters', 'jquery'], function (plugin) {
    describe("Global DT Filters", function () {
        beforeEach(function () {
            this.trunk_cell = '<span class="pointer" title="Allowed vlans: 21,40,130">Trunk</span>';
            this.vlan_cell = '130';
            this.last_seen_cell = '<td title="2012-06-11 18:19" class="numeric  ">51 days<span class="ui-helper-hidden" title="2012-06-11 18:19:30.491431"></span></td>';

        });

        describe("add filters", function () {
            it("should throw error if no node to attach filters to", function () {
                assert.throw(plugin.add_filters, Error);
            });
        });

        describe("is_trunk", function () {
            it("should match trunk string", function () {
                assert.isTrue(plugin.is_trunk(this.trunk_cell));
            });

            it("should match case insensitive", function () {
                assert.isTrue(plugin.is_trunk('trunk'));
            });

            it("should not match not trunk string", function () {
                assert.isFalse(plugin.is_trunk('trun'));
            });
        });

        describe("extract_date", function () {
            it("correctly from string", function () {
                var d = new Date('2008-02-04');
                assert.deepEqual(plugin.extract_date('asdajkl2008-02-04 12:12:12').getTime(), d.getTime());
            });

            it("with no date in string should return oldest date", function () {
                var d = new Date('1970', '01', '01');
                assert.equal(plugin.extract_date('asdajkl').getFullYear(), d.getFullYear());
            });
        });

        describe("day_since", function () {
            it("yesterday is 1 day since today", function () {
                var today = new Date();
                var yesterday = new Date(today.getTime() - 86400000);
                assert.strictEqual(plugin.daysince(yesterday), 1);
            });
        });

        describe("remove keywords", function () {
            it("should remove one keyword from search", function () {
                assert.equal(
                    plugin.remove_keywords('this $is a test'),
                    'this a test'
                );
            });
            it("should remove several keyword from search", function () {
                assert.equal(
                    plugin.remove_keywords('this $is a $test sentence'),
                    'this a sentence'
                );
            });
        });

        describe("filter", function () {
            beforeEach(function () {
                this.wrapper = document.createElement("div");
                document.body.appendChild(this.wrapper);
                this.wrapper.innerHTML = '' + '<input id="last_seen" type="text" size="3" />';
                this.input = this.wrapper.getElementsByTagName('input')[0];
                this.data = ['', '', '', this.vlan_cell, this.last_seen_cell, ''];
                plugin.add_filters(this.input, [], []);
            });
            describe("last seen", function () {
                it("with no value should return true", function () {
                    assert.isTrue(plugin.filter_last_seen('', this.data, ''));
                });
                it("with value greater than cellvalue should return false", function () {
                    this.input.value = '$days:10000';
                    assert.isFalse(plugin.filter_last_seen('', this.data, ''));
                });
                it("with value less than cellvalue should return true", function () {
                    this.input.value = '$days:3';
                    assert.isTrue(plugin.filter_last_seen('', this.data, ''));
                });
                describe("on trunk", function () {
                    beforeEach(function () {
                        this.data[3] = this.trunk_cell;
                    });
                    it("with value should return false", function () {
                        this.input.value = '$days:3';
                        assert.isFalse(plugin.filter_last_seen('', this.data, ''));
                    });
                    it("without value should return true", function () {
                        this.input.value = '';
                        assert.isTrue(plugin.filter_last_seen('', this.data, ''));
                    });
                });
            });
            describe("vlan", function () {
                it("should not hit on missing vlan", function() {
                    this.input.value = '$vlan:as';
                    assert.isFalse(plugin.filter_vlan('', this.data, ''));
                });
                it("should hit basic vlan number", function () {
                    this.input.value = '$vlan:130';
                    assert.isTrue(plugin.filter_vlan('', this.data, ''));
                });
                it("should not hit substring match", function() {
                    this.input.value = '$vlan:13';
                    assert.isFalse(plugin.filter_vlan('', this.data, ''));
                });
                it("should return true on no vlan", function () {
                    this.input.value = '$vlan:';
                    assert.isTrue(plugin.filter_vlan('', this.data, ''));
                });
            });
        });
    });
});
