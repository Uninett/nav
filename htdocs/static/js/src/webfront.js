require([
    'plugins/room_mapper',
    'plugins/navlets_controller',
    'plugins/sensors_controller',
    'plugins/fullscreen',
    'libs/jquery-ui.min',
], function (RoomMapper, NavletsController, SensorsController, fullscreen) {
    'use strict';

    var $navletsContainer = $('#navlets');

    function createRoomMap(mapwrapper, room_map) {
        $.getJSON('/ajax/open/roommapper/rooms/', function (data) {
            if (data.rooms.length > 0) {
                mapwrapper.show();
                new RoomMapper(room_map.get(0), data.rooms).createMap();
            }
        });
    }

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
        $navletsContainer.on('click', '#joyrideme', function () {
            var menu = $('.toggle-topbar'),
                is_small_screen = menu.is(':visible');

            if (is_small_screen) {
                $('#joyride_for_desktop').remove();
            } else {
                $('#joyride_for_mobile').remove();
            }

            $(document).foundation('joyride', 'start');
        });

        /* Need some way of doing javascript stuff on widgets */
        $navletsContainer.on('click', '.watchdog-tests .label.alert', function (event) {
            $(event.target).closest('li').find('ul').toggle();
        });


        /**
         * Keyboard navigation to switch dashboards
         */
        var fetchPreviousDashboard = function() {
            $navletsContainer.css('position', 'relative').animate({'left': '4000px'}, function() {
                window.location = $('#link-previous-dashboard').attr('href');
            });
        };
        var fetchNextDashboard = function() {
            $navletsContainer.css('position', 'relative').animate({'right': '4000px'}, function() {
                window.location = $('#link-next-dashboard').attr('href');
            });
        };

        // $(document).on('swipeleft', fetchPreviousDashboard);
        // $(document).on('swiperight', fetchNextDashboard);

        $(document).keydown(function(event) {
            if (!event.target.form) {
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


        /**
         * Droppable dashboard targets
         */
        var $dashboardDrop = $('#widget-drop-targets');
        $navletsContainer.on('sortstart', function() {
            $dashboardDrop.fadeIn();
        });

        var fadeOutDrop = function() {
            $dashboardDrop.fadeOut();
        };
        $navletsContainer.on('sortstop', fadeOutDrop);

        $('.dashboard-drop').droppable({
            activeClass: "drop-active",
            hoverClass: "drop-hover",
            tolerance: "pointer",
            drop: function(event, ui) {
                // Stop listening to the widget events because we want to give
                // the user some time to read the feedback
                $navletsContainer.off('sortstop');

                var label = $('<span class="label">'+ ui.draggable.find('.navlet-title').text() +'</span>').appendTo(this);
                var request = $.post(this.dataset.url, {'widget_id': ui.draggable.data('id')});
                request.done(function() {
                    // On successful request make it green and add text to indicate success
                    label.addClass('success').text(label.text() + ' moved' );
                    ui.draggable.fadeOut(function() {
                        $(this).remove();
                    });
                    $navletsContainer.on('sortstop', fadeOutDrop);  // Reapply listener
                    setTimeout(function() {  // Give user time to read feedback
                        fadeOutDrop();
                    }, 2000);
                });
                request.fail(function() {
                    label.addClass('alert').text(label.text() + ' move failed' );
                });
            }
        });


        /**
         * The following listeners are applied to buttons on the right hand side
         * when on the dashboard
         */


        /* Listnener to show fullscreen */
        $('#widgets-show-fullscreen').on('click', function() {
            fullscreen.requestFullscreen($navletsContainer.get(0));
        });


        /* Change display density for widgets and save it */
        var preferenceData = {};
        $('#widgets-layout-compact').on('click', function(event) {
            $navletsContainer.find('> .row').addClass('collapse');
            $navletsContainer.addClass('compact');
            preferenceData[NAV.preference_keys.widget_display_density] = 'compact';
            $('.widgets-layout-toggler').toggleClass('hide');
            $.get(NAV.urls.set_account_preference, preferenceData);
        });
        $('#widgets-layout-normal').on('click', function(event) {
            $navletsContainer.find('> .row').removeClass('collapse');
            $navletsContainer.removeClass('compact');
            preferenceData[NAV.preference_keys.widget_display_density] = 'normal';
            $('.widgets-layout-toggler').toggleClass('hide');
            $.get(NAV.urls.set_account_preference, preferenceData);
        });


        /**
         * The following listeners apply to the dashboard controls, that is
         * changing dashboards, adding new ones and setting default
         */

        var $dashboardSettingsPanel = $('#dropdown-dashboard-settings');
        var $alertBox = $('<div class="alert-box">');
        // Error element for naming the dashboard
        var errorElement = $('<small class="error">Name the dashboard</small>');

        function removeAlertbox() {
            $alertBox.detach();
        }

        function addFeedback(text, klass) {
            klass = klass ? klass : 'success';
            $alertBox.attr('class', 'alert-box').addClass(klass).text(text).appendTo($dashboardSettingsPanel);
        }

        $dashboardSettingsPanel.on('closed', removeAlertbox);


        $('.column-chooser').click(function() {
            $navletsContainer.empty();
            var columns = $(this).data('columns');
            new NavletsController($navletsContainer, columns);
            // Save number of columns
            var url = $(this).closest('.button-group').data('url');
            var request = $.post(url, {num_columns: columns});
            request.done(function () {
                $navletsContainer.data('widget-columns', columns);
            });
        });


        var defaultDashboardContainer = $('#default-dashboard-container'),
            setDefaultDashboardForm = $('#form-set-default-dashboard'),
            isDefaultDashboardAlert = defaultDashboardContainer.find('.alert-box');

        if (defaultDashboardContainer.data('is-default-dashboard')) {
            setDefaultDashboardForm.hide();
        } else {
            isDefaultDashboardAlert.hide();
        }

        setDefaultDashboardForm.submit(function(event) {
            event.preventDefault();
            removeAlertbox();
            var request = $.post(this.getAttribute('action'));
            request.done(function(responseText) {
                addFeedback(responseText);
                setDefaultDashboardForm.hide();
                isDefaultDashboardAlert.show();
                $('#dashboard-header').find('.heading .fa').removeClass('hidden');
            });
        });

        $('#form-add-dashboard').submit(function(event) {
            event.preventDefault();

            // Validate dashboard name
            errorElement.detach();
            var nameElement = this.elements["dashboard-name"];
            if (nameElement.value.length === 0) {
                errorElement.insertAfter(nameElement);
                return;
            }

            var request = $.post(this.getAttribute('action'), $(this).serialize());
            request.done(function(response) {
                window.location = NAV.urls.dashboard_index + response.dashboard_id;
            });
        });

        var $formRenameDashboard = $('#form-rename-dashboard');
        $formRenameDashboard.submit(function(event) {
            event.preventDefault();
            removeAlertbox();
            var self = this;
            var request = $.post(this.getAttribute('action'), $(this).serialize());
            request.done(function(responseText) {
                var newName = self.elements['dashboard-name'].value;

                // Alter name in tab title
                NAV.setTitle(newName);

                // Alter name in dashboard heading
                $('#dashboard-header').find('.heading span').text(newName);

                addFeedback(responseText);
            });
        });


        $('#form-delete-dashboard').submit(function(event) {
            event.preventDefault();
            var $this = $(this);
            var doDelete = confirm('Really delete dashboard and all widgets on it?');
            if (doDelete) {
                var request = $.post(this.getAttribute('action'), $this.serialize());
                request.done(function(response) {
                    window.location = '/';
                });
                request.fail(function(response) {
                    addFeedback(response, 'error');
                });
            }
        });

    });

});
