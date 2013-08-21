require(['plugins/date_utils', 'libs/jquery'], function (DateUtils) {
    buster.testCase("DateUtils", {
        setUp: function() {
            this.dt = new DateUtils();
        },
        "zeropad should pad single number": function() {
            assert.equals(this.dt.zeropad(9), '09');
        },
        "zeropad should pad single string": function() {
            assert.equals(this.dt.zeropad('1'), '01');
        },
        "zeropad should not pad double string": function() {
            assert.equals(this.dt.zeropad('11'), '11');
        },
        "zeropad should not pad double number": function() {
            assert.equals(this.dt.zeropad(11), '11');
        },
        "//time since should return correct days": function() {
            var now = new Date('2012-01-03');
            var then = new Date('2012-01-01');
            assert.equals(this.dt.timeSince(now, then), '2 days, 0:00:00 ago');
        },
        "//time since should return correct timestamp": function() {
            var now = new Date('2012-01-03 12:01:01');
            var then = new Date('2012-01-03 12:00:00');
            assert.equals(this.dt.timeSince(now, then), '0:01:01 ago');
        },
        "//time since should return correct future": function() {
            var now = new Date('2012-01-03 12:00:00');
            var then = new Date('2012-01-03 12:01:01');
            assert.equals(this.dt.timeSince(now, then), '0:01:01 ago');
        }
    });
});
