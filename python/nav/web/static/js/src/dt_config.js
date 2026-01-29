/**
 * DataTables 2.x configuration for legacy class name compatibility.
 * This ensures existing CSS continues to work after upgrading from 1.x.
 */
define(['libs/datatables.min'], function () {
    var DataTable = $.fn.DataTable;

    // Configure legacy class names for CSS compatibility
    $.extend(DataTable.ext.classes, {
        container: 'dataTables_wrapper',
        search: {
            container: 'dataTables_filter',
            input: ''
        },
        length: {
            container: 'dataTables_length',
            select: ''
        },
        info: {
            container: 'dataTables_info'
        },
        paging: {
            container: 'dataTables_paginate',
            button: 'paginate_button',
            active: 'current',
            disabled: 'disabled'
        },
        thead: {
            cell: 'sorting',
            row: ''
        },
        tbody: {
            cell: '',
            row: ''
        },
        tfoot: {
            cell: '',
            row: ''
        }
    });

    // Configure legacy ordering classes
    $.extend(DataTable.ext.classes.thead, {
        orderable: {
            asc: 'sorting_asc',
            desc: 'sorting_desc',
            none: 'sorting'
        }
    });
});
