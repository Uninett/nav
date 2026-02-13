/**
 * DataTables 2.x configuration for legacy class name compatibility.
 * This ensures existing CSS continues to work after upgrading from 1.x.
 */
define(['libs/datatables.min'], function () {
    const DataTable = $.fn.DataTable;

    // Configure legacy class names for CSS compatibility
    $.extend(true, DataTable.ext.classes, {
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
            disabled: 'disabled',
            nav: ''
        },
        // Use legacy layout classes (empty to avoid new grid system)
        layout: {
            row: '',
            cell: '',
            tableRow: '',
            tableCell: '',
            start: '',
            end: '',
            full: ''
        },
        // Sorting classes - these go under 'order' in 2.x
        order: {
            canAsc: 'sorting',
            canDesc: 'sorting',
            isAsc: 'sorting_asc',
            isDesc: 'sorting_desc',
            none: 'sorting_disabled',
            position: 'sorting_'
        },
        table: 'dataTable',
        thead: {
            cell: '',
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
});
