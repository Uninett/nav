define(['libs/OpenLayers', 'libs/jquery-1.4.4.min'], function () {

    function Mapper(node, positions) {
        this.node = node;
        this.positions = positions;
        this.zoom = 17;
        this.imagePath = '/images/openlayers/';
        this.markerImg = '/images/openlayers/marker.png';
        this.options = {
            theme: '/style/openlayers.css'
        };
        // We use EPSG:4362 for coords
        this.projection = new OpenLayers.Projection('EPSG:4326');

        OpenLayers.ImgPath = this.imagePath; // Needs to be set for non default paths
    }

    Mapper.prototype = {
        createMap: function () {
            this.map = new OpenLayers.Map(this.node, this.options);
            this.map.theme = this.themePath;
            this.map.addLayer(new OpenLayers.Layer.OSM());
            this.addMarkers();
        },
        addControls: function () {
            this.map.addControl(new OpenLayers.Control.LayerSwitcher({'ascending': false}));
        },
        addMarkers: function () {
            this.markers = new OpenLayers.Layer.Markers('Markers');
            this.map.addLayer(this.markers);
            for (var i = 0; i < this.positions.length; i++) {
                this.addMarker(this.calculatePosition(this.positions[i]));
            }
            this.map.zoomToExtent(this.markers.getDataExtent());
        },
        addMarker: function (position) {
            var icon = new OpenLayers.Icon(this.markerImg);
            this.markers.addMarker(new OpenLayers.Marker(position, icon));
        },
        calculatePosition: function (position) {
            var lonlat = new OpenLayers.LonLat(this.getLong(position),
                                               this.getLat(position));
            return lonlat.transform(this.projection,
                                    this.map.getProjectionObject());
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