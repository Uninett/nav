define(['jquery-1.4.4.min'], function () {

    /*
     * Return a textstring representing the table as csv suitable for
     * import in spreadsheets
     */
    function create_csv(tables) {
        var content = [];

        $(tables).each(function (index, table) {
            $(table).find('tbody tr').each(function (index, row) {
                var rowdata = format_rowdata(row);
                content.push(rowdata.join(','));
            });
        });

        return content.join('\n');
    }

    /*
     * Grab the text from the cells and return it as elements of an array
     * NB: Special case for index 2, need rewrite to be generic
     */
    function format_rowdata(row) {
        var rowdata = [];
        $(row).find('td').each(function (index, cell) {
            if (index == 2) {
                rowdata.push($(cell).find('img').attr('alt'));
            } else {
                rowdata.push($(cell).text());
            }
        });
        return rowdata;
    }


    return {
        create_csv: create_csv,
        format_rowdata: format_rowdata
    };

});
