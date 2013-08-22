require(['src/plugins/table_utils', 'libs/jquery'], function (TableUtil) {

    $(function () {
        $('.searchprovider').each(function (index, table) {
            new TableUtil(table, 20).addRowToggleTrigger();
        })
    })

});
