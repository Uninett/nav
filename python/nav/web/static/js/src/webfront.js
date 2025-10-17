require([
    'plugins/room_mapper',
    'plugins/navlets_controller',
    'plugins/sensors_controller',
    'plugins/fullscreen',
    'jquery-ui',
    'src/getting_started_wizard'
], function (RoomMapper, NavletsController, SensorsController, fullscreen, _, GettingStartedWizard) {
    'use strict';

    var $navletsContainer = $('#navlets');
    var $dashboardNavigator = $('#dashboard-nav');

    function createRoomMap(mapwrapper, room_map) {
        mapwrapper.show();
        new RoomMapper(room_map.get(0));
    }


    /**
     * Keyboard navigation to switch dashboards
     */
    function addDashboardKeyNavigation() {
        // Find available dashboards
        var $dashboardButtons = $dashboardNavigator.find('[data-dashboard]');
        var dashboards = $.map($dashboardButtons, function (element) {
            return $(element).data('dashboard');
        });
        var current = $dashboardNavigator.find('.current a').data('dashboard');
        var currentIndex = dashboards.indexOf(current);

        var fetchPreviousDashboard = function () {
            var previousId = dashboards[currentIndex === 0 ? dashboards.length - 1 : currentIndex - 1];
            $navletsContainer.css('position', 'relative').animate({'left': '4000px'}, function () {
                window.location = $dashboardButtons.filter('[data-dashboard="' + previousId + '"]').attr('href');
            });
        };
        var fetchNextDashboard = function () {
            var nextId = dashboards[currentIndex === dashboards.length - 1 ? 0 : currentIndex + 1];
            $navletsContainer.css('position', 'relative').animate({'right': '4000px'}, function () {
                window.location = $dashboardButtons.filter('[data-dashboard="' + nextId + '"]').attr('href');
            });
        };

        $(document).keydown(function (event) {
            var ignoreEvent = event.target.form || event.target.nodeName === 'INPUT' || dashboards.length <= 1;
            if (!ignoreEvent) {
                switch (event.which) {
                    case 37: // left
                        fetchPreviousDashboard();
                        break;
                    case 39: // right
                        fetchNextDashboard();
                        break;
                }
            }
        });

    }


    /**
     * Droppable dashboard targets
     */
    function addDroppableDashboardTargets() {
        var $dashboardButtons = $dashboardNavigator.find('[data-dashboard]');
        var timeoutId = 0;  // When dragging the widget between droptargets,
                            // we don't want to fade in and out all the time
        $dashboardButtons.not(function () {
            return $(this).closest('li').hasClass('current');
        }).droppable({
            activeClass: "drop-active",
            hoverClass: "drop-hover",
            tolerance: "pointer",
            drop: function (event, ui) {
                removeDropIndicator(event);
                var request = $.post(this.dataset.url, {'widget_id': ui.draggable.data('id')});
                request.done(function () {
                    // On successful request make it green and add text to indicate success
                    indicateSuccessMove(event, ui);
                    ui.draggable.fadeOut(function () {
                        $(this).remove();
                    });
                    setTimeout(function () {
                        removeDropIndicator(event);
                    }, 2000);
                });
                request.fail(function () {
                    indicateFailedMove(event, ui);
                });
            },
            over: function (event, ui) {
                // Tell the user he can drop the widget
                indicateDrop(event, ui);
                clearInterval(timeoutId);
                ui.draggable.fadeTo('fast', 0.5);
            },
            out: function (event, ui) {
                removeDropIndicator(event);
                timeoutId = setInterval(function () {
                    ui.draggable.fadeTo('fast', 1);
                }, 500);
            }
        });

        /* Returns the feedback element for this droptarget */
        function getDropFeedback(event) {
            return $(event.target).prev();
        }

        function getWidgetTitle(ui) {
            return ui.draggable.find('.navlet-title').text();
        }

        function getDashboardName(event) {
            return getDropFeedback(event).data('dashboardname');
        }

        function indicateDrop(event, ui) {
            var text = 'Move «' + getWidgetTitle(ui) + '» to «' + getDashboardName(event) + '»';
            getDropFeedback(event).addClass('warning').html(text).removeClass('hidden');
        }

        function removeDropIndicator(event) {
            getDropFeedback(event).addClass('hidden').removeClass('alert warning success');
        }

        function indicateSuccessMove(event, ui) {
            var text = '«' + getWidgetTitle(ui) + '» moved to «' + getDashboardName(event) + '»';
            getDropFeedback(event).addClass('success').html(text).removeClass('hidden');
        }

        function indicateFailedMove(event, ui) {
            var text = 'Failed to move «' + getWidgetTitle(ui) + '»';
            getDropFeedback(event).addClass('alert').html(text).removeClass('hidden');
        }

    }


    function createFeedbackElements() {
        var $dashboardSettingsPanel = $('#dashboard-settings-feedback');
        var errorElement = $('<small class="error">Name the dashboard</small>');

        function removeAlertbox() {
            $dashboardSettingsPanel.empty();
        }

        function addFeedback(text, klass) {
            klass = klass ? klass : 'success';
            $dashboardSettingsPanel.empty();
            $('<div class="alert-box">').addClass(klass).text(text).appendTo($dashboardSettingsPanel);
        }

        $dashboardSettingsPanel.on('closed', removeAlertbox);

        return {
            removeAlertbox: removeAlertbox,
            addFeedback: addFeedback,
            errorElement: errorElement
        };
    }


    /** Listnener to show fullscreen */
    function addFullscreenListener() {
        $('#widgets-show-fullscreen').on('click', function () {
            fullscreen.requestFullscreen($navletsContainer.get(0));
        });
    }


    /** Change display density for widgets and save it */
    function addDisplayDensityListener() {
        var preferenceData = {};
        $('#widgets-layout-compact').on('click', function (event) {
            $navletsContainer.find('> .row').addClass('collapse');
            $navletsContainer.addClass('compact');
            preferenceData[NAV.preference_keys.widget_display_density] = 'compact';
            $('.widgets-layout-toggler').toggleClass('hide');
            $.get(NAV.urls.set_account_preference, preferenceData);
        });
        $('#widgets-layout-normal').on('click', function (event) {
            $navletsContainer.find('> .row').removeClass('collapse');
            $navletsContainer.removeClass('compact');
            preferenceData[NAV.preference_keys.widget_display_density] = 'normal';
            $('.widgets-layout-toggler').toggleClass('hide');
            $.get(NAV.urls.set_account_preference, preferenceData);
        });
    }


    /** Change number of columns */
    function addColumnListener() {
        $('.column-chooser').click(function () {
            $navletsContainer.empty();
            const columns = $(this).data('columns');
            new NavletsController($navletsContainer, columns);
            // Save number of columns
            const url = $(this).closest('.button-group').data('url');
            const csrfToken = $('#update-columns-form input[name=csrfmiddlewaretoken]').val();
            const request = $.ajax({
                url,
                type: 'POST',
                data: {num_columns: columns},
                headers: {'X-CSRFToken': csrfToken}
            });
            request.done(function () {
                $navletsContainer.data('widget-columns', columns);
            });
        });
    }


    /** Functions for handling setting of default dashboard */
    function addDefaultDashboardListener(feedback) {
        var defaultDashboardContainer = $('#default-dashboard-container'),
            setDefaultDashboardForm = $('#form-set-default-dashboard'),
            isDefaultDashboardAlert = defaultDashboardContainer.find('.alert-box'),
            deleteDashboardForm = $('#form-delete-dashboard');

        if (defaultDashboardContainer.data('is-default-dashboard')) {
            setDefaultDashboardForm.hide();
        } else {
            isDefaultDashboardAlert.hide();
        }

        setDefaultDashboardForm.submit(function (event) {
            event.preventDefault();
            feedback.removeAlertbox();
            const request = $.post(
                this.getAttribute('action'),
                $(this).serialize()
            );
            request.done(function (responseText) {
                feedback.addFeedback(responseText);
                setDefaultDashboardForm.hide();
                isDefaultDashboardAlert.show();
                deleteDashboardForm.hide();
                $dashboardNavigator.find('.fa-star').addClass('hidden');
                $dashboardNavigator.find('.current .fa-star').removeClass('hidden');
            });
        });
    }


    /** Functions for creating a new dashboard */
    function addCreateDashboardListener(feedback) {
        $('#form-add-dashboard').submit(function (event) {
            event.preventDefault();

            // Validate dashboard name
            feedback.errorElement.detach();
            var nameElement = this.elements["dashboard-name"];
            if (nameElement.value.length === 0) {
                feedback.errorElement.insertAfter(nameElement);
                return;
            }

            var request = $.post(this.getAttribute('action'), $(this).serialize());
            request.done(function (response) {
                window.location = NAV.urls.dashboard_index + response.dashboard_id;
            });
        });
    }


    /** Functions for renaming a dashboard */
    function addRenameDashboardListener(feedback) {
        var $formRenameDashboard = $('#form-rename-dashboard');
        $formRenameDashboard.submit(function (event) {
            event.preventDefault();
            feedback.removeAlertbox();
            var self = this;
            var request = $.post(this.getAttribute('action'), $(this).serialize());
            request.done(function (responseText) {
                var newName = self.elements['dashboard-name'].value;

                // Alter name in tab title
                NAV.setTitle(newName);

                // Alter name in dashboard navigation
                $('#dashboard-nav').find('.current a span').text(newName);

                feedback.addFeedback(responseText);
            });
        });
    }


    /**
     * Load runner - runs on page load
     */
    $(function () {
        var numColumns = $navletsContainer.data('widget-columns');
        var controller = new NavletsController($navletsContainer, numColumns);
        controller.container.on('navlet-rendered', function (event, node) {
            var mapwrapper = node.find('.mapwrapper');
            var room_map = mapwrapper.find('#room_map');
            if (room_map.length > 0) {
                createRoomMap(mapwrapper, room_map);
            }


            if (node.hasClass('SensorWidget')) {
                var sensor = new SensorsController(node.find('.room-sensor'));
            }


        });


        /* Add click listener to joyride button */
        $navletsContainer.on('click', '#getting-started-wizard', function () {
            GettingStartedWizard.start();
        });

        /* Need some way of doing javascript stuff on widgets */
        $navletsContainer.on('click', '.watchdog-tests .label.alert', function (event) {
            $(event.target).closest('li').find('ul').toggle();
        });


        /**
         * DASHBOARD related stuff
         */

        addDashboardKeyNavigation();
        addDroppableDashboardTargets();

        /**
         * The following listeners are applied to buttons on the right hand side
         * when on the dashboard
         */
        addFullscreenListener();
        addDisplayDensityListener();

        /**
         * The following listeners apply to the dashboard controls, that is
         * changing dashboards, adding new ones and setting default
         */

        var feedback = createFeedbackElements();
        addColumnListener();
        addDefaultDashboardListener(feedback);
        addCreateDashboardListener(feedback);
        addRenameDashboardListener(feedback);
    });

});
