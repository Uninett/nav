define([], function () {
    describe("toFixed", function () {
        it("returns a string", function() {
            assert.strictEqual(Number('0.200').toFixed(2), '0.20');
        });
    });
    describe("Numbers", function() {
        it("removes padding zeroes", function() {
            assert.strictEqual(+'0.1000', 0.1);
        });
        it("type is 'number'", function() {
            assert.equal(typeof +'1', 'number');
        });
        it("combines with toFixed for removing padding zeroes", function() {
            var number = +'0.2200';
            assert.strictEqual(+(number.toFixed(3)), 0.22);
        });
        it("with input 'null' is 0", function() {
            assert.strictEqual(Number(null), 0);
        });
    });
});
