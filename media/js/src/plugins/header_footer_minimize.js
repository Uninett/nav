/* Plugin for adding minimize support for header and footer
 *
 * Copyright (C) 2012 UNINETT AS
 *
 * This file is part of Network Administration Visualized (NAV).
 *
 * NAV is free software: you can redistribute it and/or modify it under
 * the terms of the GNU General Public License version 2 as published by
 * the Free Software Foundation.
 *
 * This program is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
 * more details.  You should have received a copy of the GNU General Public
 * License along with NAV. If not, see <http://www.gnu.org/licenses/>.
 *
 */
define(['libs/jquery'], function () {


    function header_footer_minimize() {
        //$(headerEl).
        var $headerEl = null;
        var $footerEl = null;

        var _headerDom = null;
        var _footerDom = null;

        var headerShowing = true;
        var footerShowing = true;


        var toggleHeader = function () {
            if (headerShowing) {
                $headerEl.fadeOut('fast', function () {
                    $headerEl.empty();
                });
            } else {
                $headerEl.html(_headerDom);
                $headerEl.fadeIn('fast');
            }
            headerShowing = !headerShowing;
        };
        var toggleFooter = function () {
            if (footerShowing) {
                $footerEl.fadeOut('fast', function () {
                    $footerEl.empty();
                });
            } else {
                $footerEl.html(_footerDom);
                $footerEl.fadeIn('fast');
            }
            footerShowing = !footerShowing;
        };


        var initialize = function (map) {
            $headerEl = $(map.header);
            $footerEl = $(map.footer);

            _headerDom = map.header;
            _footerDom = map.footer;
        };

        return {
            initialize: initialize,
            toggleHeader: toggleHeader,
            toggleFooter: toggleFooter,
            isHeaderShowing: function () { return  headerShowing; },
            isFooterShowing: function () { return  footerShowing; }
        };
    }


    return header_footer_minimize;


});