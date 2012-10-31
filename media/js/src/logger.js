require([
    "plugins/table_utils", "plugins/tab_navigation", "libs/jquery", "libs/jquery-ui-1.8.21.custom.min"
], function (TableUtil, TabNavigation) {

    var mainTabsSelector = '#loggerinfotabs';

    $(document).ready(function () {
        // Plug row toggler on datasources
        //new TableUtil($('#hostinfo')).addRowToggleTrigger();

        NAV.addGlobalAjaxHandlers();
        if ($(mainTabsSelector).length != 0) {
            addMainTabs();
        }
    });

    function addMainTabs() {
        var tabconfig = {
            cache: true, // cache loaded pages
            spinner: '<img src="/images/main/process-working.gif">',
            load: eventLoadingComplete
        };
        var tabs = $(mainTabsSelector).tabs(tabconfig);
        tabs.show();
        TabNavigation.add(mainTabsSelector);
    }

    function eventLoadingComplete(event, ui) {
        if (ui.tab.text.trim() === 'Direct Search' || ui.tab.text.trim() === 'Group Search') {
            attachButtonListeners()
        }
    }

    function attachButtonListeners() {
        $('#syslog_search_form button').on('click', function (event) {
            event.preventDefault();
            searchSyslog($(this).data('target'));
        });
    }

    function checkDataAndUpdateSelection(dataTarget, data) {
        var update_target = $('select#id_'+dataTarget+' option');
        for (var i = 0; i < update_target.length; i++) {
            var select_box = update_target[i];
            if (select_box.value === data) {
                $(select_box).attr('selected', 'selected');
                break;
            }
        }
    }

    function showLogIfEnoughFilteringEnabled(target) {
        var matches = {}
        $('#syslog_search_form select option:selected').each(function (index, value) {
            if ($(value).val()) {
                matches[$(value).parent().attr('name')] = true;
            }
        });

        if ((matches.facility && matches.priority && matches.mnemonic) ||
            (matches.origin && matches.priority)) {
            $("#id_show_log").attr('checked', 'checked');
            searchSyslog(target);
        }
    }

    function searchSyslog(target) {
        $.get(target, $("#syslog_search_form").serialize(), function (data) {
            // todo: need error checking.
            $('#syslog_search').html(data);

            $('.logger_search_results a').on('click', function (event) {
                event.preventDefault();
                var eventTarget = event.target;
                var update_target;
                var data = $(eventTarget).data();

                if (data.origin) {
                    checkDataAndUpdateSelection('origin', data.origin);
                }
                if (data.facility) {
                    checkDataAndUpdateSelection('facility', data.facility);
                }
                if (data.mnemonic) {
                    checkDataAndUpdateSelection('mnemonic', data.mnemonic);
                }
                if (data.priority) {
                    checkDataAndUpdateSelection('priority', data.priority);
                }

                showLogIfEnoughFilteringEnabled(target);
                searchSyslog(target);

            });
            attachButtonListeners()
        }).error(function (data) {
                $('.results').html("<p>Failed to load search results, please try again</p>");
        });
    }
});
