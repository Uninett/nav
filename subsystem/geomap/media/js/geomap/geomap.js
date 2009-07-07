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
var bboxStrategy;
var netPopupControl;
var netLayerStyle;
var posControl;

var mapElemId;

var mapFullscreen = false;

/*
 * Called when the web page which should show the map is
 * loaded. Creates a map with two different OpenStreetMap base layers
 * (Mapnik and Osmarender), as well as a layer showing networks (with
 * data from url). The map is placed in the HTML element with
 * map_element_id as id.
 */
function init(map_element_id, url) {
    var parameters = OpenLayers.Util.getParameters();

    mapElemId = map_element_id;
    setMapSize();
    window.onresize = setMapSize;

    themap = new OpenLayers.Map(map_element_id, {
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

    bboxStrategy = new OpenLayers.Strategy.BBOX({resFactor: 1.1});

    netLayer = new OpenLayers.Layer.Vector('Networks', {
	strategies: [bboxStrategy],
		     //new OpenLayers.Strategy.Cluster()],
	protocol: new MyHTTPProtocol({
	    url: url,
	    params: {
		format: 'geojson',
		limit: 30,
		//timeStart: parameters['timeStart'],
		//timeEnd: parameters['timeEnd']
	    },
	    dynamicParams: {
		viewportWidth:
		{'function': function() { return themap.getSize().w }},
		viewportHeight:
		{'function': function() { return themap.getSize().h }},
		timeStart: {'function': getTimeIntervalStart},
		timeEnd: {'function': getTimeIntervalEnd}
	    },
	    format: new OpenLayers.Format.GeoJSON()
	}),
	styleMap: netLayerStyle,
	rendererOptions: {zIndexing: true},
	onMapMove: function() {
	    this.redraw();
	},
	setMap: function(map) {
	    OpenLayers.Layer.Vector.prototype.setMap.apply(this, arguments);
	    map.events.register('move', this, this.onMapMove);
	},
    });
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

    if (parameters.bbox) {
	var requestedBounds = OpenLayers.Bounds.fromArray(parameters.bbox);
	requestedBounds.transform(themap.displayProjection, themap.getProjectionObject());
	themap.zoomToExtent(requestedBounds);
    }

    setTimeIntervalFormListeners();
}


function updateNetData() {
    bboxStrategy.triggerRead();
}


function setMapSize() {
    var mapE = document.getElementById('map')

    if (mapFullscreen) {
	mapE.style.position = 'absolute';
	//mapE.style.zIndex = '1';
	mapE.style.top = '0';
	mapE.style.bottom = '0';
	mapE.style.left = '0';
	mapE.style.right = '0';
	mapE.style.height = 'auto';
    } else {
	var height;

	// several possibilities for preferred height:
	height =
	    window.innerHeight + mapE.clientHeight - document.body.clientHeight +
	    document.getElementById('footer').clientHeight;
	height =
	    window.innerHeight + mapE.clientHeight -
	    document.getElementById('footer').getBoundingClientRect().top;
	height =
	    window.innerHeight - mapE.getBoundingClientRect().top - 4;
	height =
	    window.innerHeight - mapE.offsetTop - 4;

	mapE.style.position = '';
	mapE.style.height = height + 'px';
	mapE.style.width = '100%';
    }
    if (themap)
	themap.updateSize();
}

function toggleFullscreen() {
    mapFullscreen = !mapFullscreen;
    setMapSize();
    setMapSize();
}


function getTimeIntervalStart() {
    var time = 'end-'+getTimeIntervalLength();
    /*
    if (!validate_rrd_time(time))
	alert('Invalid start time "' + time + '"');
    */
    return time;
}

function getTimeIntervalEnd() {
    var time = document.getElementById('id_endtime').value;
    if (!validate_rrd_time(time))
	alert('Invalid end time "' + time + '"');
    return time;
}

function getTimeIntervalLength() {
    return document.getElementById('id_interval_size').value;
}


function setTimeIntervalFormListeners() {
    document.getElementById('id_endtime').onchange = updateNetData;
    document.getElementById('id_interval_size').onchange = updateNetData;
}


function validate_rrd_time(time) {
    var re_time = 'midnight|noon|teatime|\\d\\d([:.]\\d\\d)?([ap]m)?';
    var re_day1 = 'yesterday|today|tomorrow';
    var re_day2 = '(January|February|March|April|May|June|July|August|' +
	'September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|' +
        'Aug|Sep|Oct|Nov|Dec) \\d\\d?( \\d\\d(\\d\\d)?)?';
    var re_day3 = '\\d\\d/\\d\\d/\\d\\d(\\d\\d)?';
    var re_day4 = '\\d\\d[.]\\d\\d[.]\\d\\d(\\d\\d)?';
    var re_day5 = '\\d\\d\\d\\d\\d\\d\\d\\d';
    var re_day6 = 'Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|' +
        'Mon|Tue|Wed|Thu|Fri|Sat|Sun';
    var re_day = format('(%s)|(%s)|(%s)|(%s)|(%s)|(%s)',
			re_day1, re_day2, re_day3, re_day4, re_day5, re_day6);
    re_ref = format('now|start|end|(((%s) )?(%s))', re_time, re_day);

    var re_offset_long = '(year|month|week|day|hour|minute|second)s?';
    var re_offset_short = 'mon|min|sec';
    var re_offset_single = 'y|m|w|d|h|s';
    var re_offset_no_sign =
	format('\\d+((%s)|(%s)|(%s))',
	       re_offset_long, re_offset_short, re_offset_single);
    re_offset =
	format('[+-](%s)([+-]?%s)*', re_offset_no_sign, re_offset_no_sign);

    re_total_str =
	format('^(%s)|((%s) ?(%s)?)$', re_offset, re_ref, re_offset);

    var re = new RegExp(re_total_str);

    return re.exec(time) != null;
}

