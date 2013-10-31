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
define(['libs/jquery', 'libs/underscore', 'libs/backbone', 'libs/backbone-eventbroker'], function () {


    function header_footer_minimize() {

        var HeaderFooterMinimizeView = Backbone.View.extend({
            broker: Backbone.EventBroker,
            initialize: function () {
                this.isShowing = true;

                if (this.options.hotkey !== undefined) {
                    _.bindAll(this, 'onKeypress');
                    $(document).bind('keypress', this.onKeypress);
                }


            },
            toggle:     function () {
                var self = this;
                if (this.isShowing) {
                    this.$el.fadeOut('fast', function () {
                        self.broker.trigger('headerFooterMinimize:trigger', {'name': self.options.name, 'isShowing': self.isShowing});
                    });
                } else {
                    this.$el.fadeIn('fast', function () {
                        self.broker.trigger('headerFooterMinimize:trigger', {'name': self.options.name, 'isShowing': self.isShowing});
                    });
                }
                this.isShowing = !this.isShowing;
            },
            onKeypress: function (e) {
                if (e.charCode === this.options.hotkey.charCode &&
                    e.altKey === this.options.hotkey.altKey &&
                    e.ctrlKey === this.options.hotkey.ctrlKey &&
                    e.shiftKey === this.options.hotkey.shiftKey) {

                    this.toggle();
                }

            },
            render:     function () {

            },
            close: function () {
                $(document).unbind('keypress', 'onKeypress');
                $(this.el).unbind();
                $(this.el).remove();
            }
        });

        var initialize = function (map) {
            this.headerView = new HeaderFooterMinimizeView({name: 'header', el: map.header.el, hotkey: map.header.hotkey});
            this.footerView = new HeaderFooterMinimizeView({name: 'footer', el: map.footer.el, hotkey: map.footer.hotkey});
        };

        var close = function () {
            this.headerView.close();
            this.footerView.close();
        };

        return {
            initialize:      initialize,
            close: close,
            toggleHeader:    function () {
                return this.headerView.toggle();
            },
            toggleFooter:    function () {
                return this.footerView.toggle();
            },
            isHeaderShowing: function () {
                return this.headerView.isShowing;
            },
            isFooterShowing: function () {
                return this.footerView.isShowing;
            }
        };
    }


    return header_footer_minimize;


});
