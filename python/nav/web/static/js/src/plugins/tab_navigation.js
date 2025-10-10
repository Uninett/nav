define(['jquery-ui'], function () {

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

    function add(selector, parent) {

        var $selector = typeof (selector) === 'string' ? $(selector) : selector;
        var $parent;
        if (parent) {
            $parent = typeof(parent) === 'string' ? $(parent) : parent;
        }

        /* Set hash fragment based on what tab was activated */
        $selector.bind('tabsactivate', function (event, ui) {
            //* Check if this is the tabs we're hooked to *//
            if (event.target.id === $selector.attr('id')) {
                var hashValue = '#' + ui.newPanel.attr('id');
                if (ui.newTab.index() != 0 || window.location.hash) {
                    var hashes = window.location.hash.split('!');
                    if (parent) {
                        hashes[2] = hashValue.substring(1);
                        hashes[0] = ''; // Overwrite #
                        window.location.hash = hashes.join('!');
                    } else {
                        window.location.hash = '!' + hashValue.substring(1);
                    }
                    setTitle(hashValue);
                }
            }
        });

        /* Runs on load of page only */
        function navigate() {
            var hashes = window.location.hash.split('!');
            var tabIndex = 0;
            var tabLabel = null;

            if (hashes.length === 1 && !parent) {
                $selector.tabs('option', 'active', tabIndex);
            } else if (hashes.length === 2 && !parent) {
                selectedTab = $selector.find('[aria-controls=' + hashes[1] + ']');
                $selector.tabs('option', 'active', selectedTab.index());
            } else if (hashes.length === 3 && parent) {
                selectedTab = $selector.find('[aria-controls=' + hashes[2] + ']');
                if (selectedTab.length > 0) {
                    selectedParentTab = $parent.find('[aria-controls=' + hashes[1] + ']');
                    $parent.tabs('option', 'active', selectedParentTab.index());
                    $selector.tabs('option', 'active', selectedTab.index());
                }
            }
        }

        navigate();

        var $selectedTab = $selector.children('.ui-tabs-panel:not(.ui-tabs-hide)');
        setTitle("#" + $selectedTab.prop('id'));
    }

    return {
        add: add
    };
});
