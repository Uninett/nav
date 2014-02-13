define(['libs/jquery-ui-1.8.21.custom.min'], function () {
    /* Add navigation to jQuery ui tabs */
    function add_navigation(wrapper, parent) {
        var $wrapper = typeof(wrapper) === 'string' ? $(wrapper) : wrapper;
        var $parent;
        if (parent) {
            $parent = typeof(parent) === 'string' ? $(parent) : parent;
        }

        /* Mark selected tab on page load */
        init();

        /* Set hash mark with index when a tab is selected */
        $wrapper.bind('tabsselect', function (event, ui) {
            /* Check if this is the tabs we're hooked to */
            if (event.target.id === $wrapper.attr('id')) {
                var hashValue = ui.tab.hash;
                if (ui.index != 0 || window.location.hash) {
                    if (parent) {
                        var hashes = window.location.hash.split('!');
                        hashes[2] = hashValue.substring(1);
                        hashes[0] = '';  // Overwrite #
                        window.location.hash = hashes.join('!');
                    } else {
                        window.location.hash = '!' + hashValue.substring(1);
                    }
                }
                setTitle(hashValue);
            }
        });

        /* On hash change, navigate to the tab indicated in hash mark */
        $(window).bind('hashchange', function (event) {
            navigate();
        });

        /* Set title based on fragment. Remove other fragment */
        function setTitle(fragment) {
            if (fragment && fragment !== "#undefined") {
                var old = document.title;
                var hashIndex = old.lastIndexOf('#');
                if (hashIndex === -1) {
                    document.title = old + fragment;
                } else {
                    document.title = old.substring(0, hashIndex) + fragment;
                }
            }
        }

        /* Navigate to correct tab based on url hash mark */
        function navigate() {
            var hashes = window.location.hash.split('!');

            if (hashes.length === 1) {
                $wrapper.tabs().tabs('select', 0);
            } else if (hashes.length === 2) {  // Main tab selected
                var $element;
                if (parent) {
                    $element = $parent;
                } else {
                    $element = $wrapper;
                }
                $element.tabs().tabs('select', hashes[1]);
            } else if (hashes.length === 3) {  // Subtab selected
                if (parent) {
                    $parent.tabs().tabs('select', hashes[1]);
                }
                $wrapper.tabs().tabs('select', hashes[2]);
            }
        }

        /* Do some initial stuff */
        function init() {
            navigate();
            setTitle(getSelectedTabHash());
        }

        function getSelectedTab() {
            return $wrapper.children('.ui-tabs-panel:not(.ui-tabs-hide)');
        }

        function getSelectedTabHash() {
            return "#" + getSelectedTab().prop('id');
        }
    }

    return {
        add: add_navigation
    }
});
