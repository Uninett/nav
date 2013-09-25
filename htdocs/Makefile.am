nobase_webroot_DATA = $(wildcard images/*/*.gif \
				 images/*/*.png \
				 images/*/*.jpg \
				 images/*/*.ico \
				 js/*.js        \
				 js/extras/*    \
				 js/libs/*.js   \
				 js/resources/*.js \
				 js/resources/*/*.html \
				 js/resources/libs/*.js \
				 js/src/*.js   \
				 js/src/*/*.js   \
				 js/dt_plugins/*.js \
				 js/geomap/*.js \
				 js/geomap/*/*.js   \
				 js/src/netmap/*/*.js \
				 js/src/netmap/*/*/*.js \
				 js/src/netmap/*/*/*/*.js \
				 js/src/netmap/templates/*.html \
				 js/src/netmap/templates/*/*.html \
				 style/*.css        \
				 style/nivo/*.css   \
				 style/jqueryui/*.css \
				 style/jqueryui/images/*.png \
				 style/foundation_icon_fonts/stylesheets/*.css \
				 cricket/cricket.css \
				 static/css/*.css \
				 static/css/*/*.css \
				 */.htaccess)

nobase_webroot_SCRIPTS = cricket/index.cgi

.PHONY: sass

all: sass

sass:
	$(SASS) --update sass:static/css

clean-local:
	rm -rf static
