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
        var dashboardIndex = NAV.dashboards.indexOf(NAV.dashboard_id);
        var fetchPreviousDashboard = function() {
            if (dashboardIndex === 0) {
                dashboardIndex = NAV.dashboards.length;
            }
            dashboardIndex -= 1;
            $navletsContainer.css('position', 'relative').animate({'left': '4000px'}, function() {
                window.location = '/?dashboard=' + NAV.dashboards[dashboardIndex];
            });
        };
        var fetchNextDashboard = function() {
            dashboardIndex += 1;
            dashboardIndex = dashboardIndex % NAV.dashboards.length;
            $navletsContainer.css('position', 'relative').animate({'right': '4000px'}, function() {
                window.location = '/?dashboard=' + NAV.dashboards[dashboardIndex];
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
                    }, 1000);
                });
                request.fail(function() {
                    label.addClass('alert').text(label.text() + ' move failed' );
                });
            }
        });

        /*
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
            $alertBox.attr('class', 'alert-box').addClass(klass).html(text).appendTo($dashboardSettingsPanel);
        }

        $dashboardSettingsPanel.on('closed', removeAlertbox);


        $('.column-chooser').click(function() {
            $navletsContainer.empty();
            var columns = $(this).data('columns');
            new NavletsController($navletsContainer, columns);
            // Save number of columns
            var url = $(this).closest('.button-group').data('url');
            var request = $.post(url, {num_columns: columns});
        });


        $('#form-set-default-dashboard').submit(function(event) {
            event.preventDefault();
            removeAlertbox();
            var self = this;
            var request = $.post(this.getAttribute('action'));
            request.done(function(responseText) {
                addFeedback(responseText);
            });
        });

        $('#form-choose-dashboard').on('change', function() {
            $(this).submit();
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
                window.location = '/?dashboard=' + response.dashboard_id;
            });
        });

        var $formRenameDashboard = $('#form-rename-dashboard');
        var $dashboardTitle = $dashboardSettingsPanel.find('.dashboard-title');
        $formRenameDashboard.hide();
        $dashboardTitle.on('click', function() {
            $dashboardTitle.hide();
            $formRenameDashboard.show();
        });

        $formRenameDashboard.submit(function(event) {
            event.preventDefault();
            removeAlertbox();
            var self = this;
            var request = $.post(this.getAttribute('action'), $(this).serialize());
            request.done(function(responseText) {
                // Alter name in dropdown
                var $option = $('#form-choose-dashboard').find('select option[value=' + self.dataset.dashboard + ']');
                var newName = self.elements['dashboard-name'].value;
                $option.text(newName);
                $dashboardTitle.text(newName);
                NAV.setTitle(newName);

                $dashboardTitle.show();
                $formRenameDashboard.hide();

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
