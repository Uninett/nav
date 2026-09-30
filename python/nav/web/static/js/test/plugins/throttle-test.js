define(['plugins/throttle'], function (throttle) {
    const WAIT = 50;  // ms

    describe("throttle", function () {
        it("should call the function immediately on the first call", function () {
            let calls = 0;
            const throttled = throttle(function () { calls++; }, WAIT);

            throttled();

            assert.equal(calls, 1);
        });

        it("should collapse calls during the wait into one trailing call with the latest arguments", function (done) {
            const received = [];
            const throttled = throttle(function (value) { received.push(value); }, WAIT);

            throttled(1);
            throttled(2);
            throttled(3);

            assert.deepEqual(received, [1]);
            setTimeout(function () {
                assert.deepEqual(received, [1, 3]);
                done();
            }, WAIT * 2);
        });

        it("should not call the function immediately when leading is false", function (done) {
            let calls = 0;
            const throttled = throttle(function () { calls++; }, WAIT, {leading: false});

            throttled();
            throttled();

            assert.equal(calls, 0);
            setTimeout(function () {
                assert.equal(calls, 1);
                done();
            }, WAIT * 2);
        });

        it("should call the function with the context of the last call", function (done) {
            let context = null;
            const throttled = throttle(function () { context = this; }, WAIT, {leading: false});
            const target = {name: 'target'};

            throttled.call(target);

            setTimeout(function () {
                assert.strictEqual(context, target);
                done();
            }, WAIT * 2);
        });
    });
});
