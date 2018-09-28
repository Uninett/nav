# Full integration test image for NAV
#
# A more or less identical image exists for Python 3, don't forget to
# update also that one.
#
FROM debian:stretch

ENV DISTRO stretch
ENV DISPLAY :99
ENV ADMINPASSWORD omicronpersei8

### Installing packages
RUN apt-get update && \
    apt-get -y install --no-install-recommends \
      curl gnupg dirmngr \
      git \
      python python-dev python-pip build-essential

RUN echo "\n\
\
deb-src http://security.debian.org/ $DISTRO/updates main\n\
deb-src http://deb.debian.org/debian $DISTRO main contrib non-free\n\
deb-src http://deb.debian.org/debian $DISTRO-updates main contrib non-free\n\
\
deb http://dl.google.com/linux/chrome/deb/ stable main\n\
\
" > /etc/apt/sources.list.d/pkg-sources.list
RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys A040830F7FAC5991 1397BC53640DB551

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
	firefox-esr xvfb curl \
	imagemagick \
	x11vnc google-chrome-stable cloc \
	cmake nbtscan python-gammu

RUN gem install --version '3.3.9' sass

# Now install NodeJS and NPM for Javascript testing needs -
# Which incidentally includes Python2.7, so we need some selection magic
RUN curl -sL https://deb.nodesource.com/setup_8.x  | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    update-alternatives --install /usr/bin/python python /usr/bin/python2.7 2

# Build and install libtidy5
RUN cd /tmp && \
    git clone https://github.com/htacg/tidy-html5.git && \
    cd tidy-html5/build/cmake && \
    git checkout tags/5.2.0 && \
    cmake ../.. -DCMAKE_INSTALL_PREFIX=/usr -DBUILD_SHARED_LIB:BOOL=ON && \
    make && make install && echo tidy5 installed

# Install geckodriver to properly run Selenium tests in Firefox versions>=47
ENV GECKOVERSION=0.21.0
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
	&& rm -rf "$GNUPGHOME" /usr/local/bin/gosu.asc \
	&& chmod +sx /usr/local/bin/gosu \
	&& gosu nobody true

# Add a build user
RUN adduser --system --group --home=/home/build --shell=/bin/bash build

# Build and install Python requirements
COPY requirements.txt /runtime-requirements.txt
COPY requirements/ /requirements
COPY tests/requirements.txt /test-requirements.txt
RUN pip install --upgrade 'pip<10' wheel && \
    pip install -r /runtime-requirements.txt -r /test-requirements.txt


ENV WORKSPACE /source
ENV BUILDDIR /opt/nav
ENV HOME /home/build
COPY tests/docker/scripts/ /
WORKDIR /source
