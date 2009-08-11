/*
 * Copyright (C) 2009 UNINETT AS
 *
 * This file is part of Network Administration Visualized (NAV).
 *
 * NAV is free software: you can redistribute it and/or modify it under the
 * terms of the GNU General Public License version 2 as published by the Free
 * Software Foundation.
 *
 * This program is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
 * more details.  You should have received a copy of the GNU General Public
 * License along with NAV. If not, see <http://www.gnu.org/licenses/>.
 */

/*
 * OpenLayers control for reporting the position of the last mouse click.
 *
 * Reacts to mouse click events and writes the position (as
 * longitude/latitude and UTM) to the value property of two HTML
 * elements (these should probably be input elements of type text).
 */
PositionControl = OpenLayers.Class(OpenLayers.Control, {

    idPrefix: null,

    /*
     * Constructor.
     *
     * Arguments:
     *
     * idPrefix -- prefix of ids of HTML elements to be used. If
     * idPrefix='foo', the elements for lon/lat and UTM coordinates
     * should have id 'foo-clicked-lonlat' and 'foo-clicked-utm',
     * respectively.
     *
     * options -- arbitrary properties to set on the object
     */
    initialize: function(idPrefix, options) {
	OpenLayers.Control.prototype.initialize.apply(this, arguments);
	this.idPrefix = idPrefix;
	var callbacks = {
	    'click': this.click,
	};
	this.handler = new OpenLayers.Handler.Click(this, callbacks);
    },

    /*
     * Callback function for mouse click events.
     */
    click: function(event) {
	var lonlat = fromMapCoords(this.map.getLonLatFromPixel(event.xy),
				   this.map);
	var e;
	if (e = this.elem('clicked-lonlat'))
	    e.value = lonLatToStr(lonlat);
	if (e = this.elem('clicked-utm'))
	    e.value = utmToStr(lonLatToUtm(lonlat));
    },

    /*
     * Get a HTML element by id (without prefix).
     */
    elem: function(name) {
	var id = this.idPrefix + '-' + name;
	if (!id) return null;
	return document.getElementById(id);
    },

});

