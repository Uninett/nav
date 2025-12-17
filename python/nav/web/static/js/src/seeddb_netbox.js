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

        // Initialize profiles select with links to profile detail pages
        const $profilesField = $('#id_profiles');
        if ($profilesField.length && $profilesField.hasClass('profile-select-with-links')) {
            const urlPattern = $profilesField.data('profile-url-pattern');

            // Format dropdown items with "Open" links
            function formatProfileResult(item) {
                if (!item.id) {
                    return item.text;
                }

                const profileUrl = urlPattern.replace('{id}', item.id);
                const $container = $('<div class="profile-option-container"></div>');
                $container.append($('<span class="profile-name"></span>').text(item.text));
                $container.append(
                    $('<a class="profile-link" target="_blank" title="Open profile in new tab">Open</a>')
                        .attr('href', profileUrl)
                        .attr('data-profile-url', profileUrl)
                );
                return $container;
            }

            // Initialize Select2 with custom template
            $profilesField.select2({
                templateResult: formatProfileResult,
            });

            // Helper function to find closest profile link element
            function findProfileLink(element) {
                if (element.closest) {
                    return element.closest('.profile-link');
                }
                // Fallback for older browsers
                let current = element;
                while (current && current !== document.body) {
                    if (current.classList?.contains('profile-link')) {
                        return current;
                    }
                    current = current.parentElement;
                }
                return null;
            }

            // Intercept clicks on profile links using capture phase (fires before Select2)
            document.addEventListener('mousedown', function(e) {
                const linkElement = findProfileLink(e.target);
                if (linkElement) {
                    e.preventDefault();
                    e.stopPropagation();
                    e.stopImmediatePropagation();

                    const url = linkElement.dataset.profileUrl;
                    if (url) {
                        window.open(url, '_blank');
                    }
                }
            }, true);
        }
    });
});
