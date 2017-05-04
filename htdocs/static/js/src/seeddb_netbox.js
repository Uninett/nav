require(['libs/select2.min'], function() {
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

        function checkFields() {
            if ($masterField.val()) {
                $instanceField.select2('enable', false);
            } else {
                $instanceField.select2('enable', true);
            }

            if ($instanceField.val() && !$masterField[0].disabled) {
                $masterField.select2('enable', false);
            } else {
                $masterField.select2('enable', true);
            }


        }

        $masterField.on('change', checkFields);
        $instanceField.on('change', checkFields);

    });
});
