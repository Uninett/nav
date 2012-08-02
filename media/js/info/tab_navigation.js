var NAV = this.NAV || {};

(function(){

    /* Add navigation to jQuery ui tabs */
    function add_navigation(wrapper) {
        /* Mark selected tab on page load */
        select_tab_on_load();

        /* Set hash mark with index when a tab is selected */
        $(wrapper).bind('tabsselect', function(event, ui) {
            if (ui.index != 0 || window.location.hash) {
                window.location.hash = ui.index;
            }
        });

        /* On hash change, navigate to the tab indicated in hash mark */
        $(window).bind('hashchange', function(event) {
            navigate();
        });

        /* Mark selected tab on page load */
        function select_tab_on_load() {
            navigate();
        }

        /* Navigate to correct tab based on url hash mark */
        function navigate() {
            var $tabs = $(wrapper).tabs();
            var index = 0;
            if (window.location.hash) {
                index = parseInt(window.location.hash.substring(1));
            }

            if (index != $tabs.tabs('option', 'selected')) {
                $tabs.tabs('select', index);
            }
        }
    }


    NAV.tab_navigation = {
        add: add_navigation
    }

})();