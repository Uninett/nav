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
 * NetworkLayer.js: OpenLayers layer which shows network information.
 */

NetworkLayer = OpenLayers.Class(OpenLayers.Layer.Vector, {

    initialize: function(name, url, timeInterval, options) {

	var style = new OpenLayers.StyleMap({
	    pointRadius: 15,
	    strokeWidth: 10,
	    strokeOpacity: 0.4,
	    strokeLinecap: 'butt',
	    fillOpacity: 0.7,
	    fillColor: 'black',
	    strokeColor: 'red',
	    graphicZIndex: 1
	});

	style.addUniqueValueRules('default', 'type', {
	    node: {
		fillColor: '${color}',
		strokeColor: 'black',
		strokeWidth: 0,
		pointRadius: '${size}',
		graphicZIndex: 2
	    },
	    edge: {
		strokeColor: '${color}',
		strokeWidth: '${size}',
		graphicZIndex: 1
	    }
	});

	function formattedTime(timeFunc) {
	    return function() {
		return timeFunc().format('%H:%M %Y%m%d');
	    };
	}

	this.bboxStrategy = new OpenLayers.Strategy.BBOX({resFactor: 1.1});

	options = extend({
	    strategies: [this.bboxStrategy],
	    protocol: new MyHTTPProtocol({
		url: url,
		params: {
		    format: 'geojson',
		    limit: 30,
		},
		dynamicParams: {
		    viewportWidth:
		    {'function': encapsulate(this, function() {
			return this.map.getSize().w })},
		    viewportHeight:
		    {'function': encapsulate(this, function() {
			return this.map.getSize().h })},
		    timeStart:
		    {'function': formattedTime(timeInterval.start)},
		    timeEnd:
		    {'function': formattedTime(timeInterval.end)}
		},
		format: new OpenLayers.Format.GeoJSON()
	    }),
	    styleMap: style,
	    rendererOptions: {zIndexing: true},
	}, options);

	OpenLayers.Layer.Vector.prototype.initialize.apply(this,
							   [name, options]);
	    
	this.popupControl = new PopupControl(this);
    },

    update: function() {
	this.bboxStrategy.triggerRead();
    },

    onMapMove: function() {
	this.redraw();
    },

    setMap: function(map) {
	if (this.map)
	    this.map.removeControl(this.popupControl);
	OpenLayers.Layer.Vector.prototype.setMap.apply(this, arguments);
	map.events.register('move', this, this.onMapMove);
	map.addControl(this.popupControl);
	this.popupControl.activate();
    },

    CLASS_NAME: "NetworkLayer"

});
