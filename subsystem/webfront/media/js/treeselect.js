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
