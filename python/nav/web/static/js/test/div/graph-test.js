/** Tests regarding Rickshaw and graphs */
define(['rickshaw-utils'], function (RickshawUtils) {

    describe("convertToRickshaw", function () {
        var timestamp = 1457425529;
        var value = 3;
        var datapoint = [value, timestamp];
        var result = RickshawUtils.convertToRickshaw(datapoint);

        it("should return an object with an x and y member", function () {
            assert.notStrictEqual(typeof result.x, 'undefined',
                'returned object has no x-member');
            assert.notStrictEqual(typeof result.y, 'undefined',
                'returned object has no y-member');
        });
        it("should set x to be the timestamp", function () {
            assert.strictEqual(result.x, timestamp);
        });
        it("should set y to be the value", function () {
            assert.strictEqual(result.y, value);
        });
    });

    describe("filterFunctionCalls", function () {
        var singleCall = "keepLastValue(nav.devices.buick_lab_uninett_no.ipdevpoll.1minstats.runtime)";
        var singleCallWithArguments = 'scale(nav.devices.buick_lab_uninett_no.system.sysuptime, 0.00000011574074074074)';
        var doubleCall = "alias(scale(nav.devices.buick_lab_uninett_no.system.sysuptime, 0.00000011574074074074), 'buick')";
        var singleCallWithTrend = "keepLastValue(nav.devices.buick_lab_uninett_no) (1 day ago)";
        var doubleCallWithTrend = "alias(scale(nav.devices.buick_lab_uninett_no.system.sysuptime, 0.00000011574074074074), 'buick') (1 week ago)";

        it("should remove a single function call", function () {
            var result = RickshawUtils.filterFunctionCalls(singleCall);
            assert.strictEqual(result, 'nav.devices.buick_lab_uninett_no.ipdevpoll.1minstats.runtime');
        });
        it("should remove a single function call with arguments", function () {
            var result = RickshawUtils.filterFunctionCalls(singleCallWithArguments);
            assert.strictEqual(result, 'nav.devices.buick_lab_uninett_no.system.sysuptime');
        });
        it("should remove a single function call with extra", function () {
            var result = RickshawUtils.filterFunctionCalls(singleCallWithTrend);
            assert.strictEqual(result, 'nav.devices.buick_lab_uninett_no (1 day ago)');
        });
        it("should remove a double function call", function () {
            var result = RickshawUtils.filterFunctionCalls(doubleCall);
            assert.strictEqual(result, 'nav.devices.buick_lab_uninett_no.system.sysuptime');
        });
        it("should remove a double function call", function () {
            var result = RickshawUtils.filterFunctionCalls(doubleCallWithTrend);
            assert.strictEqual(result, 'nav.devices.buick_lab_uninett_no.system.sysuptime (1 week ago)');
        });
        it("should not remove other stuff", function () {
            var result = RickshawUtils.filterFunctionCalls('buick');
            assert.strictEqual(result, 'buick');
        });
    });
});
