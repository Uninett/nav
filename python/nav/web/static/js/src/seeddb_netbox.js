require(['select2'], function() {
    $(function() {
        var toggleTrigger = $('.advanced-toggle'),
            fa = toggleTrigger.find('.fa'),
            advanced = $('.advanced'),
            storageKey = 'NAV.seeddb.advanced.show';

        function isHidden(element) {
            return element.offsetParent === null;
        }

        function toggle() {
            advanced.slideToggle(function(){
                if (isHidden(this)) {
                    console.log('Setting storagekey to ', 0);
                    localStorage.setItem(storageKey, '0');
                } else {
                    console.log('Setting storagekey to ', 1);
                    localStorage.setItem(storageKey, '1');
                }
            });
            fa.toggleClass('fa-caret-square-o-right fa-caret-square-o-down');
        }

        toggleTrigger.on('click', function(event) {
            event.preventDefault();
            toggle();
        });

        // Show element if localstorage says so
        if (+localStorage.getItem(storageKey) === 1) {
            advanced.show();
            fa.toggleClass('fa-caret-square-o-right fa-caret-square-o-down');
        }


        // Master- and instancefield are mutually exclusive. Try to enforce that.
        var $masterField = $('#id_master').select2();
        var $instanceField = $('#id_virtual_instance').select2();

        function hasValue($field) {
            const val = $field.val();
            // Check for actual value - empty options have "", null, undefined, or [] for multi-select
            if (val == null || val === '') {
                return false;
            }
            // Handle multi-select which returns an array
            if (Array.isArray(val)) {
                return val.length > 0;
            }
            return true;
        }

        function checkFields() {
            const masterHasValue = hasValue($masterField);
            const instanceHasValue = hasValue($instanceField);

            // If master has a value, disable instance field
            // If instance has a value, disable master field
            // If neither has a value, enable both
            $instanceField.prop('disabled', masterHasValue);
            $masterField.prop('disabled', instanceHasValue);
        }

        $masterField.on('change', checkFields);
        $instanceField.on('change', checkFields);

        // Run on page load to set initial state (after Select2 finishes initializing)
        setTimeout(checkFields, 0);
    });
});
