define(['libs/jquery-ui-1.8.21.custom.min'], function () {
    /* Add navigation to jQuery ui tabs */
    function add_navigation(wrapper) {
        var $wrapper = typeof(wrapper) === 'string' ? $(wrapper) : wrapper;

        /* Mark selected tab on page load */
        init();

        /* Set hash mark with index when a tab is selected */
        $wrapper.bind('tabsselect', function (event, ui) {
            /* Check if this is the tabs we're hooked to */
            if (event.target.id === $wrapper.attr('id')) {
                var hashValue = ui.tab.hash;
                if (ui.index != 0 || window.location.hash) {
                    window.location.hash = '!' + hashValue.substring(1);
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
            var index = window.location.hash ? window.location.hash.substring(2) : 0;
            $wrapper.tabs().tabs('select', index);
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
