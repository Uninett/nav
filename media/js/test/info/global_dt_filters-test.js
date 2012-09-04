require(['src/info/global_dt_filters', 'libs/jquery'], function (plugin) {
    buster.testCase("Global DT Filters", {
        setUp: function () {
            this.trunk_cell = '<span class="pointer" title="Allowed vlans: 21,40,130">Trunk</span>';
            this.vlan_cell = '130';
            this.last_seen_cell = '<td title="2012-06-11 18:19" class="numeric  ">51 days<span class="ui-helper-hidden" title="2012-06-11 18:19:30.491431"></span></td>'

        },
        "is trunk": {
            "should match trunk string": function () {
                assert(plugin.is_trunk(this.trunk_cell));
            },

            "should match case insensitive": function () {
                assert(plugin.is_trunk('trunk'));
            },

            "should not match not trunk string": function () {
                refute(plugin.is_trunk('trun'));
            }
        },

        "extract date": {
            "correctly from string": function () {
                var d = new Date('2008-02-04');
                assert.equals(plugin.extract_date('asdajkl2008-02-04 12:12:12').getTime(), d.getTime());
            },

            "with no date in string should return oldest date": function () {
                var d = new Date('1970-01-01');
                assert.equals(plugin.extract_date('asdajkl').getFullYear(), d.getFullYear());
            }
        },

        "day since": {
            "yesterday is 1 day since today": function () {
                var today = new Date();
                var yesterday = new Date(today.getTime() - 86400000);
                assert.equals(plugin.daysince(yesterday), 1);
            }
        },

        "filter": {
            setUp: function () {
                this.wrapper = document.createElement("div");
                document.body.appendChild(this.wrapper);
                this.wrapper.innerHTML = '' + '<input id="last_seen" type="text" size="3" />';
                this.input = this.wrapper.getElementsByTagName('input')[0];
                this.data = ['', '', '', this.vlan_cell, this.last_seen_cell, ''];
                plugin.add_filters(this.input, [], []);
            },
            "last seen": {
                "with no value should return true": function () {
                    assert(plugin.filter_last_seen('', this.data, ''));
                },
                "with value greater than cellvalue should return false": function () {
                    this.input.value = '$days:10000';
                    refute(plugin.filter_last_seen('', this.data, ''));
                },
                "with value less than cellvalue should return true": function () {
                    this.input.value = '$days:3';
                    assert(plugin.filter_last_seen('', this.data, ''));
                },
                "on trunk": {
                    setUp: function () {
                        this.data[3] = this.trunk_cell;
                    },
                    "with value should return false": function () {
                        this.input.value = '$days:3';
                        refute(plugin.filter_last_seen('', this.data, ''));
                    },
                    "without value should return true": function () {
                        this.input.value = '';
                        assert(plugin.filter_last_seen('', this.data, ''));
                    }
                }
            },
            "vlan": {
                "should not hit on missing vlan": function() {
                    this.input.value = '$vlan:as';
                    refute(plugin.filter_vlan('', this.data, ''));
                },
                "should hit basic vlan number": function () {
                    this.input.value = '$vlan:130';
                    assert(plugin.filter_vlan('', this.data, ''));
                },
                "should not hit substring match": function() {
                    this.input.value = '$vlan:13';
                    refute(plugin.filter_vlan('', this.data, ''));
                }
            }
        }
    });
});
