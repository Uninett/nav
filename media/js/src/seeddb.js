require([
    'plugins/checkbox_selector',
    'plugins/quickselect',
    'libs/jquery',
    'libs/OpenLayers'
], function(CheckboxSelector, QuickSelect){

    $(function() {
        new CheckboxSelector('#select', '.selector').add();
        new QuickSelect('.quickselect');

        // Mapstuff
        if ($('#map').length) {

            // Get coordinates if room exists
            var center;
            var position_input = $('#id_position');
            var position = position_input.val();
            if (position === '') {
                center = new OpenLayers.LonLat(10.396054, 63.426257);
            }
            else {
                center = parseLonLat(position.slice(1, -1));
            }

            var map = new OpenLayers.Map('map', {
                displayProjection: new OpenLayers.Projection("EPSG:4326"),
                theme: '/style/openlayers.css'
            });

            map.addLayer(new OpenLayers.Layer.OSM(
                'OpenStreetMap',
                '/info/osm_map_redirect/${z}/${x}/${y}.png')
            );

            var displayProjection = map.displayProjection;
            var inputProjection = map.getProjectionObject();

            center.transform(displayProjection, inputProjection);
            map.setCenter(center, 14);

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

                trigger: function(e) {
                    var lonlat = map.getLonLatFromPixel(e.xy).transform(
                        inputProjection,
                        displayProjection
                    );
                    position_input.val(lonLatToStr(lonlat));
                }
            });

            var click = new OpenLayers.Control.Click();
            map.addControl(click);
            click.activate();

        }
    });

    function lonLatToStr(lonlat) {
        return [lonlat.lon, lonlat.lat].join();
    }

    function parseLonLat(llStr) {
        var re = /^([0-9]*[.]?[0-9]+), *([0-9]*[.]?[0-9]+)$/;
        var arr = re.exec(llStr);
        if (arr === null) {
            throw 'error: incorrectly formatted latitude, longitude string "' +
            llStr + '"';
        }
        return new OpenLayers.LonLat(arr[2], arr[1]);
    }
});
