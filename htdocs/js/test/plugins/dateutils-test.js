define(['plugins/date_utils', 'libs/jquery'], function (DateUtils) {
    describe("DateUtils", function () {
        beforeEach(function() {
            this.dt = new DateUtils();
        });
        describe('zeropad', function () {
            it("should pad single number", function() {
                assert.strictEqual(this.dt.zeropad(9), '09');
            });
            it("zeropad should pad single string", function() {
                assert.strictEqual(this.dt.zeropad('1'), '01');
            });
            it("zeropad should not pad double string", function() {
                assert.strictEqual(this.dt.zeropad('11'), '11');
            });
            it("zeropad should not pad double number", function() {
                assert.strictEqual(this.dt.zeropad('11'), '11');
            });
        });
        describe('time since', function () {
            it("should return correct days", function () {
                var now = new Date('2012-01-03');
                var then = new Date('2012-01-01');
                assert.strictEqual(this.dt.timeSince(now, then), '2 days, 0:00:00 ago');
            });
            it("should return correct timestamp", function () {
                var now = new Date('2012', '01', '03', '12', '00', '00');
                var then = new Date('2012', '01', '03', '12', '01', '01');
                assert.strictEqual(this.dt.timeSince(now, then), '0:01:01 ago');
            });
            it("should return correct future", function () {
                var now = new Date('2012', '01', '03', '12', '00', '00');
                var then = new Date('2012', '01', '03', '12', '01', '01');
                assert.strictEqual(this.dt.timeSince(now, then), '0:01:01 ago');
            });
        });
    });
});
