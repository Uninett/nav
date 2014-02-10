nobase_webroot_DATA = $(wildcard images/*/*.gif \
				 static/images/*/*.png \
				 static/images/*/*.jpg \
				 static/images/*/*.gif \
				 static/images/*/*.ico \
				 static/images/*/*.svg \
				 static/js/*.js        \
				 static/js/libs/*.js   \
				 static/js/resources/*.js \
				 static/js/resources/*/*.html \
				 static/js/resources/libs/*.js \
				 static/js/src/*.js   \
				 static/js/src/*/*.js   \
				 static/js/dt_plugins/*.js \
				 static/js/geomap/*.js \
				 static/js/geomap/*/*.js   \
				 static/js/src/netmap/*/*.js \
				 static/js/src/netmap/*/*/*.js \
				 static/js/src/netmap/*/*/*/*.js \
				 static/js/src/netmap/templates/*.html \
				 static/js/src/netmap/templates/*/*.html \
				 static/css/*.css \
				 static/css/*/*.css \
				 static/css/*/*/*.css \
				 static/fonts/*.* \
				 )

.PHONY: sass

all: sass

sass:
	$(SASS) --update sass:static/css

clean-local:
	rm -rf static/css
