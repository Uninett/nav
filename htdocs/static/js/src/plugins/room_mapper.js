define(['libs/OpenLayers', 'libs/jquery'], function () {

    /*
     * Mapper creates an OpenStreetMap on the node given rooms from NAV
     * A room needs a name, position and status
     */
    function RoomMapper(node, rooms) {
        this.node = node;
        this.rooms = rooms;
        this.proxyurl = NAV.proxyOsmUrl + '${z}/${x}/${y}.png';
        this.imagePath = NAV.imagePath + '/openlayers/';
        this.markerImages = {
            faulty: this.imagePath + 'marker.png',
            ok: this.imagePath + 'marker-green.png'
        };
        this.options = {
            theme: NAV.cssPath + '/openlayers.css'
        };

        OpenLayers.ImgPath = this.imagePath;
    }

    RoomMapper.prototype = {
        createMap: function () {
            if (this.rooms.length <= 0) {
                console.log('Mapper: No rooms to put on map');
                return;
            }
            this.map = new OpenLayers.Map(this.node, this.options);
            var mapLayer = new OpenLayers.Layer.OSM("OpenStreetMap", this.proxyurl);
            mapLayer.tileOptions = {'crossOriginKeyword': null};
            this.map.addLayer(mapLayer);
            var markers = addMarkers(this.rooms, this.map, this.markerImages);
            addMarkerControl(markers, this.map);
            addCoordinatePicker(this.map);
        }
    };

    function addMarkers(rooms, map, images) {
        var styleMap = new OpenLayers.StyleMap({
            label: '${name}',
            externalGraphic: '${image}',
            graphicHeight: 21,
            graphicWidth: 16,
            graphicYOffset: -28
        });
        var markers = new OpenLayers.Layer.Vector('Rooms', {styleMap: styleMap});

        for (var i = 0; i < rooms.length; i++) {
            if (!(rooms[i].position && rooms[i].name && rooms[i].status)) {
                console.log('Room does not have needed members [position, name, status]')
            }
            markers.addFeatures(createMarker(rooms[i], images));
        }

        map.addLayer(markers);
        map.zoomToExtent(markers.getDataExtent());

        return markers;
    }

    function createMarker(room, images) {
        var point = new OpenLayers.Geometry.Point(getLong(room.position), getLat(room.position));
        transform(point);

        return new OpenLayers.Feature.Vector(point,
            {
                name: room.name,
                image: images[room.status]
            }
        );
    }

    function addMarkerControl(markers, map) {
        var selectControl = new OpenLayers.Control.SelectFeature(markers, {
            onSelect: roomClickHandler
        });
        map.addControl(selectControl);
        selectControl.activate();
    }

    function addCoordinatePicker(map, inputnode) {
        var node = inputnode || $('#coordinates');
        if (node.length > 0) {
            map.events.register('click', map, function (event) {
                var lonlat = map.getLonLatFromViewPortPx(event.xy);
                transform(lonlat, true);
                node.html(lonlat.lat + ',' + lonlat.lon);
            });
            node.click(function(){
                window.prompt('Ctrl-c + Enter', node.html());
            });
        }
    }

    function getLat(position) {
        return parseFloat(position.split(',')[0]);
    }

    function getLong(position) {
        return parseFloat(position.split(',')[1]);
    }

    function roomClickHandler(feature) {
        var roomname = feature.attributes.name;
        window.location = '/search/room/' + roomname;
    }

    function transform(obj, reverse) {
        reverse = (typeof reverse !== "undefined");
        // We use EPSG:4362 for coords. OSM uses EPSG:900913.
        var EPSG4326 = new OpenLayers.Projection('EPSG:4326');
        var EPSGMERC = new OpenLayers.Projection('EPSG:900913');
        return reverse ? obj.transform(EPSGMERC, EPSG4326) : obj.transform(EPSG4326, EPSGMERC);
    }

    return RoomMapper;

});
