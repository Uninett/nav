/* Copyright (C) 2008-2009, 2013-2015 Uninett AS
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

$(document).ready(function() {
    createTooltips();
});

function createTooltips() {
    /**
     * Create tooltips on the fly

     * This is necessary because of the way Foundation loops through each
     * element and creates dom-elements on page load, thus totally killing
     * performance when the number of tooltips grow large.
     *
     * This solution is bare bones. It does not handle any extra options
     * on the element. It does not handle touch devices. Thus it is only
     * functional for desktop users.
     */
    $('#device-history-search-results').on('mouseenter',
        '.fa-envelope, .netbox-sysname-tooltip', function (event) {

        var target = $(event.currentTarget);
        if (!target.data('selector')) {
            // selector data attribute is only there if create has been
            // run before
            Foundation.libs.tooltip.create(target);
            target.on('mouseleave', function (event) {
                Foundation.libs.tooltip.hide($(event.currentTarget));
            });
        }
        Foundation.libs.tooltip.showTip(target);

    });
}
