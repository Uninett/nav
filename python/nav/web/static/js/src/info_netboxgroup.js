require([
    'plugins/multiple_select',
    'libs/datatables.min',
    'src/dt_plugins/numeric_html',
    'src/dt_plugins/ip_address_sort',
    'src/dt_plugins/ip_address_typedetect',
    'src/dt_plugins/percent_sort',
],
function (MultipleSelect) {
    $(function () {
        new MultipleSelect();

        $('.netbox_availability_list').DataTable({
            'bPaginate': false,
            'bLengthChange': false,
            'bFilter': false,
            'bInfo': false,
            'aoColumns': [
                null,  // name
                null,  // ip-address
                null,  // category
                null,  // type
                null,  // organization
                {'sType': 'num-html'},  // swp
                {'sType': 'num-html'},  // gwp
                null,    // up
                {'sType': 'percent'},  // availability week
                {'sType': 'percent'}  // availability month
            ]
        });
    });
});
