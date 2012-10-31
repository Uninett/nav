require([
    "plugins/table_utils", "plugins/tab_navigation", "libs/spin.min", "libs/jquery", "libs/jquery-ui-1.8.21.custom.min"
], function (TableUtil, TabNavigation) {

    var mainTabsSelector = '#loggerinfotabs';

    var opts = {
        lines: 9, // The number of lines to draw
        length: 16, // The length of each line
        width: 9, // The line thickness
        radius: 21, // The radius of the inner circle
        corners: 1, // Corner roundness (0..1)
        rotate: 0, // The rotation offset
        color: '#000', // #rgb or #rrggbb
        speed: 1, // Rounds per second
        trail: 60, // Afterglow percentage
        shadow: true, // Whether to render a shadow
        hwaccel: true, // Whether to use hardware acceleration
        className: 'spinner', // The CSS class to assign to the spinner
        zIndex: 2e9, // The z-index (defaults to 2000000000)
        top: 'auto', // Top position relative to parent in px
        left: 'auto' // Left position relative to parent in px
    };

    $.fn.spin = function(opts) {
        this.each(function() {
            var $this = $(this),
                data = $this.data();

            if (data.spinner) {
                data.spinner.stop();
                delete data.spinner;
            }
            if (opts !== false) {
                data.spinner = new Spinner($.extend({color: $this.css('color')}, opts)).spin(this);
            }
        });
        return this;
    };

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
        $("#syslog_loader").spin(opts);
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
        }).complete(function () {
                $("#syslog_loader").spin(false);
        });
    }
});
