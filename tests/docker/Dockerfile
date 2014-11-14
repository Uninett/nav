FROM mbrekkevold/wheezy-no

ENV DEBIAN_FRONTEND noninteractive
ENV DISPLAY :99
ENV ADMINPASSWORD omicronpersei8

### Installing packages
RUN echo "deb http://ftp.no.debian.org/debian wheezy-backports main" >> /etc/apt/sources.list
RUN echo "deb-src http://ftp.no.debian.org/debian wheezy-backports main" >> /etc/apt/sources.list
RUN echo "deb http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list
RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys A040830F7FAC5991

# TODO: Might not need all the dependencies
RUN apt-get update && \
    apt-get -y --no-install-recommends build-dep \
	python-psycopg2 python-lxml librrd-dev python-imaging python-ldap

RUN apt-get update && \
    apt-get -y --no-install-recommends install \
	locales mercurial subversion git-core python-virtualenv python-pip \
	build-essential librrd-dev python-dev autoconf automake libsnmp15 \
	cron sudo libapache2-mod-wsgi rubygems inotify-tools python-cairo \
	postgresql-9.1 postgresql-contrib-9.1 postgresql-client \
	ruby1.8-dev libxml2-dev libxslt1-dev net-tools \
	postgresql-server-dev-9.1 libpq-dev libwww-perl python-rrdtool \
	python-utidylib iceweasel xvfb nodejs-legacy curl \
	python-iso8601 imagemagick x11vnc google-chrome-stable rrdtool

RUN apt-get clean

RUN pip install whisper carbon graphite-web django-tagging

RUN gem install --version '3.3.9' sass ; \
    gem install --version '~> 0.9' rb-inotify

# Build and install Python requirements
ADD runtime-requirements.txt /runtime-requirements.txt
ADD test-requirements.txt /test-requirements.txt
RUN pip install -r /runtime-requirements.txt -r /test-requirements.txt

# NPM for Javascript testing needs
RUN curl --insecure https://www.npmjs.org/install.sh | clean=no bash

RUN adduser --system --group --home=/build --shell=/bin/bash build
RUN echo "build    ALL=NOPASSWD: ALL" >> /etc/sudoers

# This does not make files in source accessible for RUN-commands
VOLUME ["/source"]

ENTRYPOINT ["/source/tests/docker/bootstrap.sh"]
