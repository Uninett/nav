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

var lat=63.4141131037476;
var lon=10.4059409151806;
var zoom=6;

var themap;
var mapnikLayer;
var osmaLayer;
var netLayer;
var netPopupControl;
var netLayerStyle;
var posControl;

/*
 * Called when the web page which should show the map is
 * loaded. Creates a map with two different OpenStreetMap base layers
 * (Mapnik and Osmarender), as well as a layer showing networks (with
 * data from url). The map is placed in the HTML element with
 * map_element_id as id.
 */
function init(map_element_id, url) {
    themap = new OpenLayers.Map (map_element_id, {
        controls:[
	    new OpenLayers.Control.Navigation(),
	    new OpenLayers.Control.PanZoomBar(),
	    new OpenLayers.Control.Attribution(),
	    new OpenLayers.Control.LayerSwitcher()],
        displayProjection: new OpenLayers.Projection("EPSG:4326")
    } );

    mapnikLayer = new OpenLayers.Layer.OSM.Mapnik("Mapnik");
    themap.addLayer(mapnikLayer);
    osmaLayer = new OpenLayers.Layer.OSM.Osmarender("Osmarender");
    themap.addLayer(osmaLayer);

    netLayer = new GeoJSONLayer('Networks', url);
    themap.addLayer(netLayer);

    netPopupControl = new PopupControl(netLayer);
    themap.addControl(netPopupControl);
    netPopupControl.activate();

    posControl = new PositionControl();
    themap.addControl(posControl);
    posControl.activate();

    var lonLat = new OpenLayers.LonLat(lon, lat).transform(themap.displayProjection, themap.getProjectionObject());
    themap.setCenter(lonLat, zoom, false);
    
    var permalinkControl = new OpenLayers.Control.Permalink();
    var argsControl = new permalinkControl.argParserClass();
    themap.addControl(permalinkControl);
    themap.addControl(argsControl);
}

