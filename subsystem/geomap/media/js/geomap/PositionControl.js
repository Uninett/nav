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

PositionControl = OpenLayers.Class(OpenLayers.Control, {

    idPrefix: null,

    projection: new OpenLayers.Projection('EPSG:4326'),

    initialize: function(idPrefix, options) {
	OpenLayers.Control.prototype.initialize.apply(this, arguments);
	this.idPrefix = idPrefix;
	var callbacks = {
	    'click': this.click,
	};
	this.handler = new OpenLayers.Handler.Click(this, callbacks);
    },

    click: function(event) {
	var lonlat = fromMapCoords(this.map.getLonLatFromPixel(event.xy),
				   this.map);
	var e;
	if (e = this.elem('clicked-lonlat'))
	    e.value = lonLatToStr(lonlat);
	if (e = this.elem('clicked-utm'))
	    e.value = utmToStr(lonLatToUtm(lonlat));
    },

    elem: function(name) {
	var id = this.idPrefix + '-' + name;
	if (!id) return null;
	return document.getElementById(id);
    },

});

