define(['libs/jquery-ui.min'], function () {

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

        $selector.bind('tabsactivate', function (event, ui) {
            //* Check if this is the tabs we're hooked to *//
            if (event.target.id === $selector.attr('id')) {
                var hashValue = ui.newPanel.selector;
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

        function navigate() {
            var hashes = window.location.hash.split('!');
            var tabIndex = 0;

            if (hashes.length === 1 && !parent) {
                $selector.tabs('option', 'active', tabIndex);
            } else if (hashes.length === 2 && !parent) {
                tabIndex = $('#' + hashes[1], $selector).index() - 1;
                $selector.tabs('option', 'active', tabIndex);
            } else if (hashes.length === 3 && parent) {
                tabIndex = $('#' + hashes[2], $selector).index() - 1;
                if (tabIndex >= 0) {
                    var parentIndex = $('#' + hashes[1], $parent).index() - 1;
                    $parent.tabs('option', 'active', parentIndex);
                    $selector.tabs('option', 'active', tabIndex);
                }
            }
        }

        $(window).on('hashchange', function (e) {
            navigate();
        });

        navigate();

        var $selectedTab = $selector.children('.ui-tabs-panel:not(.ui-tabs-hide)');
        setTitle("#" + $selectedTab.prop('id'));
    }

    return {
        add: add
    };
});
