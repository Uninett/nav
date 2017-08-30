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
            var tabLabel = null;

            if (hashes.length === 1 && !parent) {
                $selector.tabs('option', 'active', tabIndex);
            } else if (hashes.length === 2 && !parent) {
                tabLabel = $('#' + hashes[1], $selector).attr('aria-labelledby');
                tabIndex = $('.ui-tabs-nav [aria-labelledby='+tabLabel+']', $selector).index();
                $selector.tabs('option', 'active', tabIndex);
            } else if (hashes.length === 3 && parent) {
                tabLabel = $('#' + hashes[2], $selector).attr('aria-labelledby');
                tabIndex = $('.ui-tabs-nav [aria-labelledby='+tabLabel+']', $selector).index();
                if (tabIndex >= 0) {
                    var parentLabel = $('#' + hashes[1], $parent).attr('aria-labelledby');
                    var parentIndex = $('.ui-tabs-nav [aria-labelledby='+parentLabel+']', $parent).index();
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
