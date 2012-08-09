define(['libs/OpenLayers', 'libs/jquery-1.4.4.min'], function () {

    function Mapper(node, position) {
        this.node = node;
        this.long = this.getLong(position);
        this.lat = this.getLat(position);
        this.position = this.calculatePosition();
        this.zoom = 17;
        this.imagePath = '/images/openlayers/';
        this.markerImg = '/images/openlayers/marker.png';
        this.options = {
            theme: '/style/openlayers.css'
        };

        OpenLayers.ImgPath = this.imagePath; // Needs to be set for non default paths
    }

    Mapper.prototype = {
        createMap: function () {
            this.map = new OpenLayers.Map(this.node, this.options);
            this.map.theme = this.themePath;
            this.map.addLayer(new OpenLayers.Layer.OSM());
            this.map.setCenter(this.position, this.zoom);
            //            this.addControls();
            this.addMarkers();
        },
        calculatePosition: function () {
            var proj4326 = new OpenLayers.Projection("EPSG:4326");
            var projmerc = new OpenLayers.Projection("EPSG:900913");
            return new OpenLayers.LonLat(this.long, this.lat).transform(proj4326, projmerc)
        },
        addControls: function () {
            this.map.addControl(new OpenLayers.Control.LayerSwitcher({'ascending': false}));
        },
        addMarkers: function () {
            this.markers = new OpenLayers.Layer.Markers('Markers');
            this.map.addLayer(this.markers);
            this.addMarker(this.position);
        },
        addMarker: function (position) {
            var icon = new OpenLayers.Icon(this.markerImg);
            this.markers.addMarker(new OpenLayers.Marker(position, icon));
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