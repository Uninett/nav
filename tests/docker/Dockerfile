# Full integration test image for NAV
#
FROM mbrekkevold/debian-gosu:stretch

ENV DISTRO stretch
ENV DISPLAY :99
ENV ADMINPASSWORD omicronpersei8

### Installing packages
RUN apt-get update && \
    apt-get -y install --no-install-recommends \
      curl git \
      python python-dev python-pip build-essential \
      python3 python3-dev python3-pip

RUN echo "\n\
\
deb-src http://security.debian.org/ $DISTRO/updates main\n\
deb-src http://deb.debian.org/debian $DISTRO main contrib non-free\n\
deb-src http://deb.debian.org/debian $DISTRO-updates main contrib non-free\n\
\
deb http://dl.google.com/linux/chrome/deb/ stable main\n\
\
" > /etc/apt/sources.list.d/pkg-sources.list
RUN apt-key adv --no-tty --keyserver keyserver.ubuntu.com --recv-keys A040830F7FAC5991 1397BC53640DB551

RUN apt-get update && \
    apt-get -y --no-install-recommends build-dep \
	python-psycopg2 python-lxml python-imaging python-ldap

RUN apt-get update && \
    apt-get -y --no-install-recommends install \
	libsnmp30 \
	cron \
	python-cairo \
	postgresql postgresql-contrib postgresql-client \
	libxml2-dev libxslt1-dev \
	libwww-perl \
	firefox-esr xvfb \
	imagemagick \
	x11vnc google-chrome-stable cloc \
	cmake nbtscan python-gammu


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
ENV CHROMEDRIVERVERSION=2.35
RUN cd /tmp && \
    apt-get update && \
    apt-get -y --no-install-recommends install unzip && \
    wget http://chromedriver.storage.googleapis.com/$CHROMEDRIVERVERSION/chromedriver_linux64.zip && \
    unzip chromedriver_linux64.zip && \
    mv chromedriver /usr/local/bin/

# Install our primary test runner
RUN pip install tox snmpsim

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
