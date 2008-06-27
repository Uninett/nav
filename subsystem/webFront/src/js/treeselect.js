/* Treeselelct JavaScripts for NAV
 *
 * Copyright 2008 UNINETT AS
 *
 * This file is part of Network Administration Visualized (NAV)
 *
 * NAV is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * NAV is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with NAV; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 * 
 * Authors: Thomas Adamcik <thomas.adamcik@uninett.no>
 *
 */

$(function() {
    $('.treeselect select').each(function() {
        var select = $(this);
        var input = $('<input tyoe="text" style="width: 100%;"/>');

        input.keyup(function() {
            select.find("option:not(:contains('" + input.val() + "'))").hide();
            select.find("option:contains('" + input.val() + "')").show();
        });

        select.before(input);
    });
});
