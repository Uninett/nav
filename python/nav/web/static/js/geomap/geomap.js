/*
 * Copyright (C) 2009, 2010, 2015 Uninett AS
 *
 * This file is part of Network Administration Visualized (NAV).
 *
 * NAV is free software: you can redistribute it and/or modify it under the
 * terms of the GNU General Public License version 3 as published by the Free
 * Software Foundation.
 *
 * This program is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
 * more details.  You should have received a copy of the GNU General Public
 * License along with NAV. If not, see <http://www.gnu.org/licenses/>.
 */

/*
 * geomap.js: Shows a map with a network information overlay.
 */

require(['geomap/GeomapPlugin'], function (geomap) {
    $(function () {
        var $timePanelToggler = $('#time-panel-toggler'),
            $icon = $timePanelToggler.find('i');
        $timePanelToggler.on('click', function () {
            $('#time-panel').slideToggle(function () {
                var $panel = $(this);
                if ($panel.is(':visible')) {
                    $icon.removeClass('fa-caret-down').addClass('fa-caret-up');
                } else {
                    $icon.removeClass('fa-caret-up').addClass('fa-caret-down');
                }
            });
        });
    });

    /* Start creating map when all content is rendered */
    $(window).on('load', function () {
        geomap();
    });


});
