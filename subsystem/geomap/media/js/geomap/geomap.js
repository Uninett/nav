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
 * geomap.js: Shows a map with a network information overlay.
 */

// Initial position and zoom level (if none provided in the URL):
var lat=63.4141131037476;
var lon=10.4059409151806;
var zoom=6;

// Variables holding the objects created by init:
var themap;
var mapnikLayer;
var osmaLayer;
var netLayer;
var posControl;
var timeNavigator;

// id attribute of the HTML element containing the map:
var mapElemId;

// Boolean variable determining whether the map should cover the whole
// viewport:
var mapFullscreen = false;


/*
 * Called when the web page which should show the map is loaded.
 *
 * Creates a map with two different OpenStreetMap base layers (Mapnik
 * and Osmarender), as well as a layer showing networks (with data
 * from url).  The map is placed in the HTML element with
 * mapElementId as id.
 *
 * Arguments:
 *
 * mapElementId -- id of HTML element for map
 *
 * url -- URL for network data requests
 */
function init(mapElementId, url) {
    var parameters = OpenLayers.Util.getParameters();

    mapElemId = mapElementId;
    setMapSize();
    window.onresize = setMapSize;

    timeNavigator = new TimeNavigator('time-navigation',
				      function() { netLayer.update(); });

    themap = new OpenLayers.Map(mapElementId, {
        controls:[
	    new OpenLayers.Control.Navigation(),
	    new OpenLayers.Control.PanZoomBar(),
	    //new OpenLayers.Control.NavToolbar(),
	    new OpenLayers.Control.Attribution(),
	    new OpenLayers.Control.LayerSwitcher()],
        displayProjection: new OpenLayers.Projection("EPSG:4326")
    } );

    mapnikLayer = new OpenLayers.Layer.OSM.Mapnik("Mapnik");
    themap.addLayer(mapnikLayer);
    osmaLayer = new OpenLayers.Layer.OSM.Osmarender("Osmarender");
    themap.addLayer(osmaLayer);

    netLayer = new NetworkLayer(
	'Networks', url,
	{start: function() { return timeNavigator.interval.beginning(); },
	 end: function() { return timeNavigator.interval.end(); }},
	{eventListeners: {
	    loadstart: netLayerLoadStart,
	    loadend: netLayerLoadEnd,
	    loadcancel: netLayerLoadCancel }
	});
    themap.addLayer(netLayer);

    posControl = new PositionControl('pos');
    themap.addControl(posControl);
    posControl.activate();

    var lonLat = new OpenLayers.LonLat(lon, lat).transform(themap.displayProjection, themap.getProjectionObject());
    themap.setCenter(lonLat, zoom, false);
    
    if (parameters.bbox) {
	var requestedBounds = OpenLayers.Bounds.fromArray(parameters.bbox);
	requestedBounds.transform(themap.displayProjection, themap.getProjectionObject());
	themap.zoomToExtent(requestedBounds);
    }

    try {
	var permalink = new Permalink(
	    'permalink', themap,
	    {set time(t) { timeNavigator.setInterval(new TimeInterval(t)); },
	     get time() { return timeNavigator.interval.toReadableString(); }},
	    [timeNavigator.onChange]);
    } catch (e) {
	alert('Error parsing URL query string:\n' + e);
    }
}


/*
 * Updating the displayed loading status:
 */
function netLayerLoadStart() {
    document.getElementById('geomap-heading').innerHTML = 'Geomap (<img src="/images/geomap/loading.gif" alt=""/> loading data ...)';
    document.getElementById('navbody').className = 'loading';
}
function netLayerLoadEnd() {
    document.getElementById('geomap-heading').innerHTML = "Geomap";
    document.getElementById('navbody').className = '';
}
function netLayerLoadCancel() {
    document.getElementById('geomap-heading').innerHTML = "Geomap";
    document.getElementById('navbody').className = '';
}

/*
 * Update the size of the map element according to the viewport size.
 *
 * It would be nicer to use only CSS for this, but we want the map
 * element to cover the whole viewport _except_ a certain amount at
 * the top and right (for the NAV header and the time selection,
 * respectively), which cannot be expressed in CSS (at least not in
 * version 2).
 */
function setMapSize() {
    var mapE = document.getElementById(mapElemId)

    if (mapFullscreen) {
	mapE.style.position = 'absolute';
	//mapE.style.zIndex = '1';
	mapE.style.top = '0';
	mapE.style.bottom = '0';
	mapE.style.left = '0';
	mapE.style.right = '0';
	mapE.style.height = 'auto';
	mapE.style.width = 'auto';
    } else {
	var height = window.innerHeight - elemOffsetTop(mapE) - 4;
	var width = window.innerWidth - 400;

	mapE.style.position = '';
	mapE.style.height = height + 'px';
	mapE.style.width = width + 'px';
    }
    if (themap)
	themap.updateSize();
}

/*
 * Distance from top of viewport to top of HTML element elem.
 *
 * (Helper function for setMapSize).
 */
function elemOffsetTop(elem) {
    var offset = elem.offsetTop;
    while (elem = elem.offsetParent)
	offset += elem.offsetTop;
    return offset;
}

/*
 * Switch between fullscreen mode and normal mode.
 */
function toggleFullscreen() {
    mapFullscreen = !mapFullscreen;
    setMapSize();
    setMapSize();
}


