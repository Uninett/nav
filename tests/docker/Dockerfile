# Full integration test image for NAV
#
FROM mbrekkevold/ubuntu-gosu:bionic

ENV DISTRO buster
ENV DISPLAY :99
ENV ADMINPASSWORD omicronpersei8
ENV DEBIAN_FRONTEND noninteractive

### Installing packages
RUN apt-get update && \
    apt-get install -y software-properties-common

RUN add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get -y install --no-install-recommends \
      curl git build-essential \
      python3.7 python3.7-dev \
      python3.8 python3.8-dev \
      python3-pip

RUN echo "deb http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list
RUN apt-key adv --no-tty --keyserver keyserver.ubuntu.com --recv-keys A040830F7FAC5991 1397BC53640DB551

RUN apt-get update && \
    apt-get -y --no-install-recommends build-dep \
	python3-psycopg2 python3-lxml python3-pil python3-ldap

RUN apt-get update && \
    apt-get -y --no-install-recommends install \
	libsnmp30 \
	cron \
	libjpeg62 \
	postgresql postgresql-contrib postgresql-client \
	libxml2-dev libxslt1-dev \
	libwww-perl \
	firefox xvfb \
	imagemagick \
	x11vnc google-chrome-stable cloc \
	cmake nbtscan python-gammu


# Now install NodeJS and NPM for Javascript testing needs -
RUN curl -sL https://deb.nodesource.com/setup_8.x  | bash - && \
    apt-get install -y --no-install-recommends nodejs

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
ENV CHROMEDRIVERVERSION=2.35
RUN cd /tmp && \
    apt-get update && \
    apt-get -y --no-install-recommends install unzip && \
    wget http://chromedriver.storage.googleapis.com/$CHROMEDRIVERVERSION/chromedriver_linux64.zip && \
    unzip chromedriver_linux64.zip && \
    mv chromedriver /usr/local/bin/

# Install our primary test runner
RUN python3.7 -m pip install tox snmpsim 'virtualenv<20.0.0'

# Add a build user
RUN adduser --system --group --home=/source --shell=/bin/bash build && \
    mkdir -p /usr/share/nav/var/uploads && \
    chown -R build /usr/share/nav

ENV WORKSPACE /source
ENV HOME /source

COPY scripts/ /
WORKDIR /source
ENTRYPOINT ["/entrypoint.sh"]
RUN chmod 755 /*.sh
