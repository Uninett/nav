(function(info){
    buster.testCase("Info", {
        setUp: function(){
            this.trunk_cell =
                '<td class="numeric ">' +
                '<span class="pointer" title="Allowed vlans: 21,40,130">Trunk</span>' +
                '</td>';
            this.vlan_cell = '<td class="numeric ">130</td>';
            this.last_seen_cell = '<td title="2012-06-11 18:19" class="numeric  ">51 days<span class="ui-helper-hidden" title="2012-06-11 18:19:30.491431"></span></td>'

        },
        "is trunk": {
            "should match trunk string": function() {
                assert(info.is_trunk(this.trunk_cell));
            },

            "should match case insensitive": function() {
                assert(info.is_trunk('trunk'));
            },

            "should not match not trunk string": function() {
                refute(info.is_trunk('trun'));
            }
        },

        "extract date": {
            "correctly from string": function() {
                var d = new Date('2008-02-04');
                assert.equals(
                    info.extract_date('asdajkl2008-02-04 12:12:12').getTime(),
                    d.getTime());
            },

            "with no date in string should return oldest date": function() {
                var d = new Date('1970-01-01');
                assert.equals(
                    info.extract_date('asdajkl').getFullYear(),
                    d.getFullYear());
            }
        },

        "day since": {
            "yesterday is 1 day since today": function() {
                var today = new Date();
                var yesterday = new Date(today.getTime() - 86400000);
                assert.equals(info.daysince(yesterday), 1);
            }
        },

        "filter last seen": {
            setUp: function() {
                this.last_seen_input = document.createElement("div");
                document.body.appendChild(this.last_seen_input);
                this.last_seen_input.innerHTML = '' +
                    '<input id="last-seen" type="text" size="3" />';
                this.input = this.last_seen_input.getElementsByTagName('input')[0];
                this.data = ['', '', '',
                    this.vlan_cell,
                    this.last_seen_cell,
                    '']
            },
            "with no value should return true": function() {
                assert(info.filter_last_seen('', this.data, ''));
            },
            "with value greater than cellvalue should return false": function() {
                this.input.value = 10000;
                refute(info.filter_last_seen('', this.data, ''));
            },
            "with value less than cellvalue should return true": function() {
                this.input.value = 3;
                assert(info.filter_last_seen('', this.data, ''));
            },
            "on trunk": {
                setUp: function() {
                    this.data[3] = this.trunk_cell;
                },
                "with value should return false": function() {
                    this.input.value = 3;
                    refute(info.filter_last_seen('', this.data, ''));
                },
                "without value should return true": function() {
                    this.input.value = '';
                    assert(info.filter_last_seen('', this.data, ''));
                }
            }
        }

    });
})(NAV.info);
