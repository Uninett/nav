FROM python:2.7

ENV DISTRO jessie
ENV DISPLAY :99
ENV ADMINPASSWORD omicronpersei8
ENV MIRROR httpredir.debian.org

### Installing packages
RUN echo "\n\
\
deb http://security.debian.org/ $DISTRO/updates main\n\
deb-src http://security.debian.org/ $DISTRO/updates main\n\
deb http://$MIRROR/debian $DISTRO main contrib non-free\n\
deb-src http://$MIRROR/debian $DISTRO main contrib non-free\n\
deb http://$MIRROR/debian $DISTRO-updates main contrib non-free\n\
deb-src http://$MIRROR/debian $DISTRO-updates main contrib non-free\n\

deb http://dl.google.com/linux/chrome/deb/ stable main\n\
\
" > /etc/apt/sources.list
RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys A040830F7FAC5991 1397BC53640DB551

# TODO: Might not need all the dependencies
RUN apt-get update && \
    apt-get -y --no-install-recommends build-dep \
	python-psycopg2 python-lxml python-imaging python-ldap

RUN apt-get update && \
    apt-get -y --no-install-recommends install \
	libsnmp30 \
	cron \
	apache2 libapache2-mod-wsgi \
	rubygems \
	python-cairo \
	postgresql postgresql-contrib postgresql-client \
	libxml2-dev libxslt1-dev \
	libwww-perl \
	iceweasel xvfb nodejs-legacy curl \
	imagemagick \
	x11vnc google-chrome-stable cloc \
	cmake nbtscan python-gammu

RUN gem install --version '3.3.9' sass

# NPM for Javascript testing needs
#RUN curl -sS --insecure https://www.npmjs.com/install.sh | clean=no bash
RUN apt-get update && apt-get -y --no-install-recommends install npm

# Build and install libtidy5
RUN cd /tmp && \
    git clone https://github.com/htacg/tidy-html5.git && \
    cd tidy-html5/build/cmake && \
    cmake ../.. -DCMAKE_INSTALL_PREFIX=/usr -DBUILD_SHARED_LIB:BOOL=ON && \
    make && make install && echo tidy5 installed

# Add a build user
RUN adduser --system --group --home=/home/build --shell=/bin/bash build

# Build and install Python requirements
COPY requirements.txt /runtime-requirements.txt
COPY requirements/ /requirements
COPY tests/requirements.txt /test-requirements.txt
RUN pip install -r /runtime-requirements.txt -r /test-requirements.txt
RUN pip install whisper carbon==0.9.14 graphite-web==0.9.14 django-tagging

# Install geckodriver to properly run Selenium tests in Firefox versions>=47
ENV GECKOVERSION=0.11.1
RUN cd /tmp && \
    wget https://github.com/mozilla/geckodriver/releases/download/v$GECKOVERSION/geckodriver-v$GECKOVERSION-linux64.tar.gz && \
    tar xvzf geckodriver-v$GECKOVERSION-linux64.tar.gz && \
    mv geckodriver /usr/local/bin/

# Install chromedriver to properly run Selenium tests in Chrome, if need be
RUN cd /tmp && \
    apt-get update && \
    apt-get -y --no-install-recommends install unzip && \
    wget http://chromedriver.storage.googleapis.com/2.24/chromedriver_linux64.zip && \
    unzip chromedriver_linux64.zip && \
    mv chromedriver /usr/local/bin/

# GOSU for our root needs
ENV GOSU_VERSION 1.10
RUN set -x \
	&& apt-get update && apt-get install -y --no-install-recommends ca-certificates \
	&& dpkgArch="$(dpkg --print-architecture | awk -F- '{ print $NF }')" \
	&& wget -O /usr/local/bin/gosu "https://github.com/tianon/gosu/releases/download/$GOSU_VERSION/gosu-$dpkgArch" \
	&& wget -O /usr/local/bin/gosu.asc "https://github.com/tianon/gosu/releases/download/$GOSU_VERSION/gosu-$dpkgArch.asc" \
	&& export GNUPGHOME="$(mktemp -d)" \
	&& gpg --keyserver ha.pool.sks-keyservers.net --recv-keys B42F6819007F00F88E364FD4036A9C25BF357DD4 \
	&& gpg --batch --verify /usr/local/bin/gosu.asc /usr/local/bin/gosu \
	&& rm -r "$GNUPGHOME" /usr/local/bin/gosu.asc \
	&& chmod +x /usr/local/bin/gosu \
	&& gosu nobody true

RUN chmod +s /usr/local/bin/gosu

ENV WORKSPACE /source
ENV BUILDDIR /opt/nav
ENV HOME /home/build
COPY tests/docker/scripts/ /
WORKDIR /source
