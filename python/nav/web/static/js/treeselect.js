/* Treeselelct JavaScripts for NAV
 *
 * Copyright (C) 2008 Uninett AS
 *
 * This file is part of Network Administration Visualized (NAV).
 *
 * NAV is free software: you can redistribute it and/or modify it under
 * the terms of the GNU General Public License version 3 as published by
 * the Free Software Foundation.
 *
 * This program is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
 * more details.  You should have received a copy of the GNU General Public
 * License along with NAV. If not, see <http://www.gnu.org/licenses/>.
 *
 */

$(function() {
    $('.treeselect').each(function() {
        var treeselect = $(this);
        var search = $('<label>Search <input tyoe="text" /></label>');

        search.find('input').keyup(function() {

            var keywords = $(this).val().split(/\s+/);

            if (keywords[0] == '') {
                // Show all options when our search is empty
                treeselect.find("option").show();

            } else {
                // Hide all options an show the ones that match our keywords.
                treeselect.find("option").hide();
                for (var i = 0; i < keywords.length; i++) {
                    if(keywords[i]) {
                        treeselect.find("option:contains('" + keywords[i] + "')").show();
                    }
                }
            }
        });

        // Add our search field :)
        treeselect.prepend(search);
    });
});
