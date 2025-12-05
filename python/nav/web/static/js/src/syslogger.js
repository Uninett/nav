require([
    "plugins/table_utils",
    "plugins/tab_navigation",
    "plugins/jquery_ui_helpers",
    "libs/spin.min",
    "jquery",
    "jquery-ui",
    "libs/datatables.min"
], function (TableUtil, TabNavigation, JUIHelpers, Spinner) {

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
        if ($(mainTabsSelector).length != 0) {
            addMainTabs();
        }
    });

    function addMainTabs() {
        var tabconfig = {
            beforeLoad: JUIHelpers.cacheRequest,
            load: eventLoadingComplete
        };
        var tabs = $(mainTabsSelector).tabs(tabconfig);
        tabs.show();
        TabNavigation.add(mainTabsSelector);
    }

    /* Enrich tables with dataTables module */
    function enrich_tables(tables, extra_opts) {
        var dt_config = {
            bAutoWidth: false,
            bFilter: true,
            bInfo: true,
            bLengthChange: false,
            bPaginate: false,
            bSort: true
        };
        if (extra_opts) {
            dt_config.update(extra_opts);
        }
        tables.dataTable(dt_config);
    }

    function stripDomainSuffixOrigin(dom, suffixes) {
        dom.each(function (index, option) {
            for (var i = 0; i < suffixes.length; i++) {
                var suffix = suffixes[i];

                if (option.value && option.value.indexOf(suffix) !== -1) {
                    $(option).text(option.value.slice(0, option.value.length-suffix.length));
                } else if (option.tagName.toLowerCase() == 'td' && option.innerHTML && option.innerHTML.indexOf(suffix) !== -1) {
                    $(option).html(option.innerHTML.slice(0, option.innerHTML.length-suffix.length));
                } else if (option.text && option.text.indexOf(suffix) !== -1) {
                    $(option).text(option.text.slice(0, option.text.length-suffix.length));
                }
            }
        });
    }

    function eventLoadingComplete(event, ui) {
        if ($(ui.tab).text().trim() === 'Search') {
            var suffixes = JSON.parse($('#domain_strip').text());
            stripDomainSuffixOrigin($('#id_origin option'), suffixes);
            updateFormFromRequestArguments();
            attachButtonListeners();
        }
    }

    function attachButtonListeners() {
        $('#syslog_search_form button').on('click', function (event) {
            event.preventDefault();
            searchSyslog($(this).data('target'));
        });
    }

    function checkDataAndUpdateSelection(dataTarget, data) {
        var update_target = $('#id_'+dataTarget+' option');
        for (var i = 0; i < update_target.length; i++) {
            var select_box = update_target[i];
            if (select_box.value === data) {
                $(select_box).attr('selected', 'selected');
                break;
            }
        }
    }

    function setSelectedOption(name, field) {
        var options = $('#id_'+name+' option');
        for (var i = 0; i < options.length; i++) {
            var option = options[i];
            if (option.value  && option.value.trim() === field.trim()) {
                $(option).prop('selected', 'selected');
                break;
            }
        }
    }

    function convertToBoolean(value) {
        if (!value || value === 'undefined') return false;

        if (typeof value === 'string') {
            switch (value.toLowerCase()) {
                case 'true':
                case 'yes':
                case '1':
                case 'on':
                    return true;
                case 'false':
                case 'no':
                case '0':
                case 'off':
                    return false;
            }
        }
        return Boolean(value);
    }

    function setSelectedValue(name, field) {
        $('#id_'+name).val(decodeURIComponent((field.trim()).replace(/\+/g, '%20')));
    }

    function setSelectedCheckbox(name, field) {
        if (convertToBoolean(field)) {
            $('#id_'+name).attr('checked', (field));
        }
    }

    function updateFormFromRequestArguments() {
        var request = {};
        var pairs = location.search.substring(1).split('&');
        for (var i = 0; i < pairs.length; i++) {
            var pair = pairs[i].split('=');
            request[pair[0]] = pair[1];
        }

        if (request.timestamp_from) { setSelectedValue('timestamp_from', request.timestamp_from); }
        if (request.timestamp_to) { setSelectedValue('timestamp_to', request.timestamp_to); }
        if (request.priority) { setSelectedOption('priority', request.priority); }
        if (request.facility) { setSelectedOption('facility', request.facility); }
        if (request.mnemonic) { setSelectedOption('mnemonic', request.mnemonic); }
        if (request.origin) { setSelectedOption('origin', request.origin); }
        if (request.category) { setSelectedOption('category', request.category); }
        if (request.show_log) { setSelectedCheckbox('show_log', request.show_log); }
    }

    function showLogIfEnoughFilteringEnabled() {
        var matches = {};
        $('#syslog_search_form select option:selected').each(function (index, value) {
            if ($(value).val()) {
                matches[$(value).parent().attr('name')] = true;
            }
        });

        if ((matches.facility && matches.priority && matches.mnemonic) ||
            (matches.origin && matches.priority)) {
            showLog();
        }
    }
    function showLog() {
        $("#id_show_log").attr('checked', 'checked');
    }

    function searchSyslog(target) {
        $("#syslog_loader").spin(opts);
        $.get(target, $("#syslog_search_form").serialize(), function (data) {
            $('#syslog_search').html(data);
            var suffixes = JSON.parse($('#domain_strip').text());
            stripDomainSuffixOrigin($('#id_origin option'), suffixes);
            stripDomainSuffixOrigin($('.syslog_origin'), suffixes);

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
                if (data.show_log) {
                    showLog();
                } else {
                    showLogIfEnoughFilteringEnabled();
                }
                searchSyslog(target);

            });
            attachButtonListeners();
        }).fail(function (data) {
                $('.results').html("<p>Failed to load search results, please try again</p>");
        }).always(function () {
                $("#syslog_loader").spin(false);
                enrich_tables($('.logger_search_results table.listtable.log'));
        });
    }
});
