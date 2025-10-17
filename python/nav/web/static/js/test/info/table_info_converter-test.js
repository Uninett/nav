define(['info/table_info_converter', 'jquery'], function (converter) {
    describe("table info converter", function () {
        beforeEach(function () {
            this.wrapper = $('<div></div>');
            var table = $('<table><caption><a href=""> uninett-gw.uninett.no   \n</a> - blapp</caption><thead></thead><tbody></tbody></table>');
            $(this.wrapper).append(table);

            var row = $('<tr></tr>');
            var cell1 = $('<td></td>').html('1');
            var cell2 = $('<td></td>').html('2');
            var cell3 = $('<td></td>').html('<img alt="3"/>');
            var cell4 = $('<td></td>').html(' 4 ');
            var cell5 = $('<td></td>').html('5');
            $(row).append(cell1, cell2, cell3, cell4, cell5);

            $(table).find('tbody').append(row, row.clone());
        });
        describe("create csv", function () {
            it("should concatenate properly", function () {
                var tables = $(this.wrapper).find('table');
                var result = converter.create_csv(tables);
                assert.strictEqual(
                    result,
                    'uninett-gw.uninett.no;1;2;3;4;5\nuninett-gw.uninett.no;1;2;3;4;5'
                );
            });
        });
        describe("format rowdata", function () {
            it("should return a list of the cells values", function () {
                var row = $(this.wrapper).find('tbody tr')[0];
                var result = converter.format_rowdata(row);
                assert.deepEqual(result, ['1', '2', '3', '4', '5']);
            });
            it("should create own trim function if it does not exist", function () {
                String.prototype.trim = undefined;
                var row = $(this.wrapper).find('tbody tr')[0];
                var result = converter.format_rowdata(row);
                assert.deepEqual(result, ['1', '2', '3', '4', '5']);
            });
        });
        describe("find sysname", function () {
            it("should find correct sysname from caption", function () {
                var table = $(this.wrapper).find('table')[0];
                assert.strictEqual(converter.find_sysname($(table)), 'uninett-gw.uninett.no');
            });
        });
    });
});
