/*
 * Copyright (C) 2009, 2010 UNINETT AS
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

require(['libs/jquery'], function () {
    $(function () {
        var $timePanelToggler = $('#time-panel-toggler'),
            $icon = $timePanelToggler.find('i');
        $timePanelToggler.on('click', function () {
            $('#time-panel').slideToggle(function () {
                var $panel = $(this);
                if ($panel.is(':visible')) {
                    $icon.removeClass('fa-caret-down').addClass('fa-caret-up');
                } else {
                    $icon.removeClass('fa-caret-up').addClass('fa-caret-down');
                }
            });
        });
    });

    /* Start creating map when all content is rendered */
    $(window).load(function () {
        create_bounding_box();
    });

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
var nav = nav || {};
var getDataUrl = 'data';


function create_bounding_box() {
    /*
     * We're hacking away to make this work. This function must be called
     * instead of the original init function. Also, this function should
     * end by calling init
     */
    $.getJSON('/ajax/open/roommapper/rooms/', function (data) {
        var roomPosArray = [];
        for (var i=0, room; room = data.rooms[i]; i++) {
            roomPosArray.push(new OpenLayers.Geometry.Point(getLong(room.position), getLat(room.position)));
        }

        var roomPositions = new OpenLayers.Geometry.MultiPoint(roomPosArray);
        nav.geomapBBox = roomPositions.getBounds();

        init('map');
    });
}

function getLat(position) {
    return parseFloat(position.split(',')[0]);
}

function getLong(position) {
    return parseFloat(position.split(',')[1]);
}


    /*
     * Called when the web page which should show the map is loaded.
     *
     * Creates a map with the OpenStreetMap Mapnik base layer, as well as a layer
     * showing networks (with data from url).  The map is placed in the HTML
     * element with mapElementId as id.
     *
     * Arguments:
     *
     * mapElementId -- id of HTML element for map
     *
     */
    function init(mapElementId) {

        mapElemId = mapElementId;
        setMapSize();
        window.onresize = setMapSize;

        themap = new OpenLayers.Map(mapElementId, {
                controls: [
                    new OpenLayers.Control.Navigation(), new OpenLayers.Control.PanZoomBar(), //new OpenLayers.Control.NavToolbar(),
                    new OpenLayers.Control.Attribution(), new OpenLayers.Control.LayerSwitcher()
                ],
                displayProjection: new OpenLayers.Projection("EPSG:4326"),
                theme: NAV.cssPath + '/openlayers.css'
            });

        addLayers();
    }

    function addLayers() {
        var parameters = OpenLayers.Util.getParameters();
        timeNavigator = new TimeNavigator('time-navigation', function () {
                netLayer.update();
            });

        mapnikLayer = new OpenLayers.Layer.OSM("OpenStreetMap", NAV.proxyOsmUrl + '/${z}/${x}/${y}.png');
        mapnikLayer.tileOptions = {crossOriginKeyword: null};
        themap.addLayer(mapnikLayer);

        netLayer = new NetworkLayer('Networks', getDataUrl, {
                start: function () {
                    return timeNavigator.interval.beginning();
                },
                end: function () {
                    return timeNavigator.interval.end();
                }
            }, {
                eventListeners: {
                    loadstart: netLayerLoadStart,
                    loadend: netLayerLoadEnd,
                    loadcancel: netLayerLoadCancel
                }
            });
        themap.addLayer(netLayer);

        if (parameters.bbox) {
            var requestedBounds = OpenLayers.Bounds.fromArray(parameters.bbox);
            requestedBounds.transform(themap.displayProjection, themap.getProjectionObject());
            themap.zoomToExtent(requestedBounds);
        } else {
            nav.geomapBBox.transform(themap.displayProjection, themap.getProjectionObject());
            themap.zoomToExtent(nav.geomapBBox);
        }

        try {
            var permalink = new Permalink('permalink', themap, {
                    set time(t) {
                        timeNavigator.setInterval(new TimeInterval(t));
                    },
                    get time() {
                        return timeNavigator.interval.toReadableString();
                    }
                }, [timeNavigator.onChange]);
        } catch (e) {
            alert('Error parsing URL query string:\n' + e);
        }

    }

/*
 * Updating the displayed loading status:
 */
function netLayerLoadStart() {
//    document.getElementById('geomap-spinner').style.display = 'block';
    document.getElementsByClassName('navbody')[0].className = 'navbody loading';
}
function netLayerLoadEnd() {
//    document.getElementById('geomap-spinner').style.display = 'none';
    document.getElementsByClassName('navbody')[0].className = 'navbody';
}
function netLayerLoadCancel() {
//    document.getElementById('geomap-spinner').style.display = 'none';
    document.getElementsByClassName('navbody')[0].className = 'navbody';
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
    var mapE = document.getElementById(mapElemId);

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
        //var height = window.innerHeight - elemOffsetTop(mapE) - 4;
        var height = document.getElementById('map-container').innerHeight;
        var width = document.getElementById('map-container').innerWidth;

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


});
