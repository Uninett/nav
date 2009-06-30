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

GeoJSONLayer = OpenLayers.Class(OpenLayers.Layer.Vector, {

    format: null,

    baseUrl: null,

    ongoingRequest: null,
    nextRequest: null,

    initialize: function(name, baseUrl, style, typeStyles, options) {
	style = extend(GeoJSONLayer.defaultStyle, style);
	typeStyles = extend(GeoJSONLayer.defaultTypeStyles, typeStyles);
	var styleMap = new OpenLayers.StyleMap(style);
	styleMap.addUniqueValueRules('default', 'type', typeStyles);
	var rendererOptions = {zIndexing: true};

	options = extend(options,
			 {styleMap:styleMap,
			  rendererOptions:rendererOptions});
	OpenLayers.Layer.Vector.prototype.initialize.apply(this, [name, options]);

	this.baseUrl = baseUrl;
	this.format = new OpenLayers.Format.GeoJSON();
	this.format.externalProjection = new OpenLayers.Projection('EPSG:4326');
	this.popups = {};
    },

    loadContent: function() {
	var url = this.makeUrl();
	if (this.ongoingRequest) {
	    this.nextRequest = url;
	} else {
	    this.sendRequest(url);
	}
    },

    sendNextRequest: function() {
	this.ongoingRequest = null;
	var url = this.nextRequest;
	if (url) {
	    this.nextRequest = null;
	    this.sendRequest(url);
	}
    },

    sendRequest: function(url) {
	this.ongoingRequest = url;
	OpenLayers.loadURL(url, null, this,
			   this.handleContent, this.loadContentFailure);
    },

    makeUrl:
    function() {
	var bounds = this.getMapBounds();
	var size = this.map.getSize();
	var url = this.baseUrl +
	    '?format=geojson' +
	    '&minLon=' + bounds.minLon + '&maxLon=' + bounds.maxLon +
	    '&minLat=' + bounds.minLat + '&maxLat=' + bounds.maxLat +
	    '&viewportWidth=' + size.w + '&viewportHeight=' + size.h +
	    '&limit=' + 30;
	return url;
    },

    /*
     * Find the bounds of the map area displayed currently. Returns an
     * object with properties minLon, minLat, maxLon, maxLat.
     */
    getMapBounds:
    function() {
	var p = OpenLayers.Geometry.Point;
	var extent = this.map.getExtent();
	var bottomLeft = new p(extent.left, extent.bottom);
	var topRight = new p(extent.right, extent.top);
	bottomLeft.transform(this.map.getProjectionObject(),
			     this.map.displayProjection);
	topRight.transform(this.map.getProjectionObject(),
			   this.map.displayProjection);
	var bounds = {
	    'minLon': min(bottomLeft.x, topRight.x),
	    'minLat': min(bottomLeft.y, topRight.y),
	    'maxLon': max(bottomLeft.x, topRight.x),
	    'maxLat': max(bottomLeft.y, topRight.y)
	};
	return bounds;
    },

    handleContent:
    function(request) {
	this.sendNextRequest();
	var features = this.format.read(request.responseText);

	if (features) {
	    this.removeAllFeatures();
	    this.addFeatures(features);
	} else {
	    throw 'no features -- what went wrong?';
	}
    },

    loadContentFailure:
    function(request) {
	this.sendNextRequest();
	// TODO
    },

    /*
     * Function called after a map movement (panning or zooming)
     * is finished.
     */
    onMapMoveEnd:
    function() {
	this.loadContent();
    },

    onMapMove:
    function() {
	this.redraw();
    },

    /*
     * Override setMap to register our onMapMoveEnd function on
     * the map's 'moveend' event.
     */
    setMap:
    function(map) {
	OpenLayers.Layer.Vector.prototype.setMap.apply(this,
						       arguments);
	map.events.register('moveend', this, this.onMapMoveEnd);
	map.events.register('move', this, this.onMapMove);

	this.format.internalProjection = this.map.getProjectionObject();
    },

    /*
     * Remove all the features (points, lines, etc.) in the layer.
     */
    removeAllFeatures:
    function() {
	this.removeFeatures(this.features);
    },


    CLASS_NAME: "GeoJSONLayer" 

});


GeoJSONLayer.defaultStyle = {
    pointRadius: 15,
    strokeWidth: 10,
    strokeOpacity: 0.4,
    fillOpacity: 0.7,
    fillColor: 'black'
};

GeoJSONLayer.defaultTypeStyles = {
    node: {
	fillColor: '${color}',//'#ee9900',
	strokeColor: 'black',
	strokeWidth: 0,
	pointRadius: '${size}',
	graphicZIndex: 2
    },
    edge: {
	strokeColor: '${color}',//'#333399',
	strokeWidth: '${size}',
	graphicZIndex: 1
    }
};
