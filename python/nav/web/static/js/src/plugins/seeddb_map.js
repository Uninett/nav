define(['plugins/fullscreen', 'libs/OpenLayers'], function(fullscreen) {

    /**
     * Display map for editing room position in seedDB
     * @param {string} mapElementId The id of the map element
     * @param {string} positionFieldId The id of the form position field
     * @param {string} getLocationTrigger The id of the trigger for getting a
     * location
     */
    function SeedDBMap(mapElementId, positionFieldId, getLocationTrigger) {
        var map = initMap(mapElementId);
        var positionField = $('#' + positionFieldId);
        var marker = populateMap(map, positionField);
        $('#' + getLocationTrigger).on('click', function() {
            getAndSetLocation(map, marker, positionField);
        });
    }


    /**
     * Create the map and add the base layer
     * @param {string} mapElementId The id of the map container element
     * @returns {OpenLayers.Map}
     */
    function initMap(mapElementId) {
        OpenLayers.ImgPath = NAV.imagePath + '/openlayers/';
        var map = new OpenLayers.Map(mapElementId, {
            displayProjection: new OpenLayers.Projection("EPSG:4326"),
            controls: [
                new OpenLayers.Control.PanZoomBar(),
                new OpenLayers.Control.Navigation()
            ],
            theme: NAV.cssPath + '/openlayers.css'
        }),
            mapLayer = new OpenLayers.Layer.OSM(
                'OpenStreetMap', NAV.osmTileUrl + '/${z}/${x}/${y}.png');

        mapLayer.tileOptions = {crossOriginKeyword: null};
        map.addLayer(mapLayer);
        fullscreen.createFullscreenToggler(map.div, true);
        return map;
    }


    /**
     * Add marker, center map and initiate click control
     * @param {OpenLayers.Map} map
     * @param {jQueryDomElement} positionField
     * @returns {OpenLayers.Marker}
     */
    function populateMap(map, positionField) {
        var center = getCenter(map, positionField.val()),
            marker = addMarkerToLayer(center, addMarkerLayer(map));

        if (isDefaultPoint(center)) {
            // rooms is populated in the template
            if (rooms.length) {
                var bounds = new OpenLayers.Bounds();
                for (var i = 0; i < rooms.length; i++) {
                    bounds.extend(new OpenLayers.LonLat(rooms[i][1], rooms[i][0]));
                }
                map.zoomToExtent(bounds.transform(new OpenLayers.Projection("EPSG:4326"), new OpenLayers.Projection("EPSG:900913")));
            } else {
                map.zoomToMaxExtent();
            }
        } else {
            map.zoomTo(14);
            moveTo(center, map, marker);
        }
        initGetLonLatOnClickControl(map, marker, positionField);
        return marker;
    }


    /**
     * Get point given or default coords
     * @param {OpenLayers.Map} map
     * @param {string} positionValue The value from the form position field
     * @returns {OpenLayers.LonLat}
     */
    function getCenter(map, positionValue) {
        var center = getPoint(map, [0, 0]);
        if (positionValue) {
            try {
                var coords = parsePositionValue(positionValue.slice(1, -1));
                center = getPoint(map, coords);
            } catch (err) {
                console.error(err);
            }
        }

        return center;
    }

    /**
     * Parse a string to find longitude and latitude
     * @param {string} position The string to parse
     * @returns {OpenLayers.LonLat}
     */
    function parsePositionValue(position) {
        var re = /^(-?[0-9]*[.]?[0-9]+), *(-?[0-9]*[.]?[0-9]+)$/;
        var arr = re.exec(position);
        if (arr === null) {
            throw 'error: incorrectly formatted latitude, longitude string "' +
                position + '"';
        }
        return [arr[2], arr[1]];
    }

    /**
     * Create a LonLat object from coords and transform it to map projection
     * @param {OpenLayers.Map} map
     * @param {array} coords [longitude, latitude]
     * @returns {OpenLayers.LonLat}
     */
    function getPoint(map, coords) {
        var lonLat = new OpenLayers.LonLat(coords[0], coords[1]);
        lonLat.transform(map.displayProjection, map.getProjectionObject());
        return lonLat;
    }


    /**
     * Returns if the lonlat is default point. Because of rounding errors when
     * applying transformations we cannot simply check for 0.
     * @param {OpenLayers.LonLat} lonlat
     * @returns {boolean}
     */
    function isDefaultPoint(lonlat) {
        return Math.abs(lonlat.lon) < 1 && Math.abs(lonlat.lat) < 1;
    }


    function addMarkerLayer(map) {
        var markerLayer = new OpenLayers.Layer.Vector('MarkerLayer');
        markerLayer.setVisibility(false);
        map.addLayer(markerLayer);
        return markerLayer;
    }

    function addMarkerToLayer(lonlat, layer) {
        var geometry = new OpenLayers.Geometry.Point(lonlat.lon, lonlat.lat);
        var marker = new OpenLayers.Feature.Vector(geometry, null, {
            externalGraphic: NAV.imagePath + '/openlayers/marker-green.png',
            graphicHeight: 25,
            graphicYOffset: -25
        });
        layer.addFeatures([marker]);
        return marker;
    }

    /**
     * Define and activate the control for selecting a point from the map
     */
    function initGetLonLatOnClickControl(map, marker, position_input)
    {
        map.addControl(new OpenLayers.Control.MousePosition());

        OpenLayers.Control.Click = OpenLayers.Class(OpenLayers.Control, {
            defaultHandlerOptions: {
                'single': true,
                'double': false,
                'pixelTolerance': 0,
                'stopSingle': false,
                'stopDouble': false
            },

            initialize: function(options) {
                this.handlerOptions = OpenLayers.Util.extend(
                    {}, this.defaultHandlerOptions
                );
                OpenLayers.Control.prototype.initialize.apply(
                    this, arguments
                );
                this.handler = new OpenLayers.Handler.Click(
                    this, {
                        'click': this.trigger
                    }, this.handlerOptions
                );
            },

            trigger: function(event) {
                var lonlat = map.getLonLatFromPixel(event.xy);
                moveTo(lonlat, map, marker);
                updatePosition(position_input, lonlat, map);
            }
        });

        var click = new OpenLayers.Control.Click();
        map.addControl(click);
        click.activate();
    }

    /**
     * Set position in form
     * @param {jQueryDomElement} positionField A jQuery dom element
     * @param {OpenLayers.LonLat} lonlat A transformed lonlat
     * @param {OpenLayers.Map} map
     */
    function updatePosition(positionField, lonlat, map) {
        positionField.val(lonLatToStr(lonlat.transform(
            map.getProjectionObject(), map.displayProjection)));
    }

    /**
     * Create a string from a point suitable for the form position field
     * @param {OpenLayers.LonLat} lonlat
     * @returns {string}
     */
    function lonLatToStr(lonlat) {
        return '(' + [lonlat.lat, lonlat.lon].join() + ')';
    }

    /**
     * Get and set location using geolocation api.
     * @param {OpenLayers.Map} map
     * @param {OpenLayers.Feature.Vector} marker
     * @param {jQueryDomElement} positionField
     */
    function getAndSetLocation(map, marker, positionField) {
        function gotPosition(position) {
            var lonlat = getPoint(map, [
                position.coords.longitude,
                position.coords.latitude
            ]);
            moveTo(lonlat, map, marker);
            updatePosition(positionField, lonlat, map);
            map.zoomTo(12);
        }

        function errorGettingPosition(error) {
            console.log(error);
            alert(error.message);
        }

        if (navigator && "geolocation" in navigator) {
            navigator.geolocation.getCurrentPosition(
                gotPosition,
                errorGettingPosition,
                {timeout: 10000}  // Default is infinity, yay. No map for you.
            );
        } else {
            alert('Your browser does not support geolocation');
        }
    }


    /**
     * Move the map and marker to a point
     */
    function moveTo(point, map, marker) {
        map.setCenter(point);
        marker.move(point);
        getMarkerLayer(map).setVisibility(true);
    }


    /**
     * Get the layer containing the map marker
     * @param {OpenLayers.Map} map
     * @returns {OpenLayers.Layer.Vector}
     */
    function getMarkerLayer(map) {
        return map.getLayersByName('MarkerLayer')[0];
    }

    return SeedDBMap;
});
