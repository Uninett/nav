#!/bin/bash

for i in $(seq -w 1 60)
do
    wget -O EPSG326$i.js "http://spatialreference.org/ref/epsg/326$i/proj4js/"
    echo>>EPSG326$i.js
    wget -O EPSG327$i.js "http://spatialreference.org/ref/epsg/327$i/proj4js/"
    echo>>EPSG327$i.js
done

cat EPSG326*.js > EPSG326xx.js
cat EPSG327*.js > EPSG327xx.js
