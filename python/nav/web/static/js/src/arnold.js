require(['src/libs/tablesort_extensions'], function (tablesort) {
    const profileForm = document.querySelector('form.profileDetentionForm');
    if (profileForm) {
        addVlanToggler(document.getElementById('id_detention_type'));
    }

    const manualForm = document.querySelector('form.manualDetentionForm');
    if (manualForm) {
        addVlanToggler(document.getElementById('id_method'));
    }

    // Add tablesorter to history table
    const historyTable = document.querySelector('.arnold-history');
    if (historyTable?.querySelector('tbody')) {
        tablesort.init(historyTable, {
            headers: {
                0: { sorter: 'ip-address' },
                7: { sorter: 'iso-datetime' },
                8: { sorter: false }
            }
        });
    }

    // Add tablesorter to detained ports table
    const detainedTable = document.querySelector('.arnold-detainedports');
    if (detainedTable?.querySelector('tbody')) {
        tablesort.init(detainedTable, {
            headers: {
                0: { sorter: 'ip-address' },
                6: { sorter: 'iso-datetime' },
                7: { sorter: false },
                8: { sorter: false }
            }
        });
    }

    function addVlanToggler(selectNode) {
        const row = document.querySelector('.qvlanrow');
        if (!row || !selectNode) return;

        if (selectNode.value !== 'quarantine') {
            row.classList.add('hidetrick');
        }

        selectNode.addEventListener('change', function () {
            if (this.value === 'quarantine') {
                row.classList.remove('hidetrick');
            } else {
                row.classList.add('hidetrick');
            }
        });
    }
});
