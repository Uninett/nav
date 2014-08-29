#!/bin/bash

docker build --rm=true -t testus tests/
docker run -privileged -v /home/jenkins/workspace/eivinly-dockerize-this:/source testus
