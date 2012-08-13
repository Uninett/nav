define(['libs/OpenLayers', 'libs/jquery-1.4.4.min'], function () {

    function Mapper(node, rooms) {
        this.node = node;
        this.rooms = rooms;
        this.zoom = 17;
        this.imagePath = '/images/openlayers/';
        this.markerImg = '/images/openlayers/marker.png';
        this.options = {
            theme: '/style/openlayers.css'
        };
        // We use EPSG:4362 for coords. OSM uses EPSG:900913. Use this when
        // converting
        this.projection = new OpenLayers.Projection('EPSG:4326');

        OpenLayers.ImgPath = this.imagePath;
    }

    function roomClickHandler(feature) {
        var roomname = feature.attributes.name;
        window.location = '/info/room/' + roomname;

    }

    Mapper.prototype = {
        createMap: function () {
            this.map = new OpenLayers.Map(this.node, this.options);
            this.map.addLayer(new OpenLayers.Layer.OSM());
            this.addMarkers();
        },

        addControls: function () {
            this.map.addControl(new OpenLayers.Control.LayerSwitcher({'ascending': false}));
        },

        addMarkers: function () {
            this.markers = new OpenLayers.Layer.Vector('Markers');
            for (var i = 0; i < this.rooms.length; i++) {
                this.markers.addFeatures(this.createMarker(this.rooms[i]));
            }
            this.map.addLayer(this.markers);
            this.map.zoomToExtent(this.markers.getDataExtent());
            this.addMarkerControl();
        },

        addMarkerControl: function() {
            var selectControl = new OpenLayers.Control.SelectFeature(this.markers, {
                onSelect: roomClickHandler
            });
            this.map.addControl(selectControl);
            selectControl.activate();
        },

        createMarker: function (room) {
            var point = new OpenLayers.Geometry.Point(this.getLong(room.position), this.getLat(room.position));
            point.transform(this.projection, this.map.getProjectionObject());

            return new OpenLayers.Feature.Vector(point, {
                name: room.name
            }, {
                label: room.name,
                externalGraphic: this.markerImg,
                graphicHeight: 21,
                graphicWidth: 16,
                graphicYOffset: -28
            });
        },

        getLat: function (position) {
            return parseFloat(position.split(',')[0]);
        },

        getLong: function (position) {
            return parseFloat(position.split(',')[1]);
        }
    };

    return Mapper
});