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

        // Initialize profiles select with links to profile detail pages
        const $profilesField = $('#id_profiles');
        if ($profilesField.length && $profilesField.hasClass('profile-select-with-links')) {
            const urlPattern = $profilesField.data('profile-url-pattern');

            // Format dropdown items with "View" links
            function formatProfileResult(item) {
                if (!item.id) {
                    return item.text;
                }

                const profileUrl = urlPattern.replace('{id}', item.id);
                return `
                    <div class="profile-option-container">
                        <span class="profile-name">${item.text}</span>
                        <a href="${profileUrl}"
                           target="_blank"
                           class="profile-link"
                           title="Open profile in new tab"
                           data-profile-url="${profileUrl}">
                            Open
                        </a>
                    </div>
                `;
            }

            // Initialize Select2 with custom formatters
            $profilesField.select2({
                formatResult: formatProfileResult,
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
