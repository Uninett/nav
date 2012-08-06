require(['src/info/table_info_converter'], function (converter) {
    buster.testCase("table info converter", {
        setUp:function () {
            this.wrapper = $('<div></div>');
            var table = $('<table><thead></thead><tbody></tbody></table>');
            $(this.wrapper).append(table);

            var row = $('<tr></tr>');
            var cell1 = $('<td></td>').html('1');
            var cell2 = $('<td></td>').html('2');
            var cell3 = $('<td></td>').html('<img alt="3"/>');
            var cell4 = $('<td></td>').html(' 4 ');
            var cell5 = $('<td></td>').html('5');
            $(row).append(cell1, cell2, cell3, cell4, cell5);

            $(table).find('tbody').append(row, row.clone());
        },
        "create csv should concatenate properly":function () {
            var tables = $(this.wrapper).find('table');
            var result = converter.create_csv(tables);
            assert.equals(result, '1,2,3,4,5\n1,2,3,4,5');
        },
        "format rowdata should return a list of the cells values":function () {
            var row = $(this.wrapper).find('tbody tr')[0];
            var result = converter.format_rowdata(row);
            assert.equals(result, [1, 2, 3, 4, 5]);
        }
    });
});

