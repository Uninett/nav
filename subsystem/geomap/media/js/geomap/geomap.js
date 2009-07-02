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

    var format = new OpenLayers.Format.GeoJSON({
	externalProjection: new OpenLayers.Projection('EPSG:4326'),
	internalProjection: themap.getProjectionObject()
    });

    netLayerStyle = new OpenLayers.StyleMap({
	pointRadius: 15,
	strokeWidth: 10,
	strokeOpacity: 0.4,
	strokeLinecap: 'butt',
	fillOpacity: 0.7,
	fillColor: 'black',
	strokeColor: 'red',
	graphicZIndex: 1
    });
    netLayerStyle.addUniqueValueRules('default', 'type', {
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
    });

    netLayer = new OpenLayers.Layer.Vector('Networks', {
	strategies: [new OpenLayers.Strategy.BBOX({resFactor: 1.1})],
		     //new OpenLayers.Strategy.Cluster()],
	protocol: new MyHTTPProtocol({
	    url: url,
	    params: {
		format: 'geojson',
		limit: 30
	    },
	    dynamicParams: {
		viewportWidth: {'function': function() { return themap.getSize().w }},
		viewportHeight: {'function': function() { return themap.getSize().h }}
	    },
	    format: new OpenLayers.Format.GeoJSON()
	}),
	styleMap: netLayerStyle,
	rendererOptions: {zIndexing: true}
    });
    themap.addLayer(netLayer);

    /*
    netLayer = new GeoJSONLayer('Networks', url);
    themap.addLayer(netLayer);
    */

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

