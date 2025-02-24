# Full integration test image for NAV
#
FROM ubuntu:24.04
# We're using mount caches, so don't clean the apt cache after every apt command!
RUN rm -f /etc/apt/apt.conf.d/docker-clean; echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' > /etc/apt/apt.conf.d/keep-cache


ENV DISPLAY=:99
ENV ADMINPASSWORD=omicronpersei8
ENV DEBIAN_FRONTEND=noninteractive

### Installing packages
RUN sed -i 's/^Types: deb$/Types: deb deb-src/' /etc/apt/sources.list.d/ubuntu.sources  # Enable source repos
RUN --mount=target=/var/lib/apt/lists,type=cache,sharing=locked \
    --mount=target=/var/cache/apt,type=cache,sharing=locked \
    rm -f /etc/apt/apt.conf.d/docker-clean && \
    apt-get update && \
    apt-get install -y software-properties-common gosu sudo unzip

RUN echo "build   ALL =(ALL: ALL) NOPASSWD: ALL" > /etc/sudoers.d/navbuild


RUN --mount=target=/var/lib/apt/lists,type=cache,sharing=locked \
    --mount=target=/var/cache/apt,type=cache,sharing=locked \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get -y install --no-install-recommends \
      curl git build-essential \
      python3.9-dbg python3.9-dev python3.9-venv \
      python3.10-dbg python3.10-dev python3.10-venv \
      python3.11-dbg python3.11-dev python3.11-venv \
      python3-pip

RUN echo "deb http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list
# 78BD65473CB3BD13 Google signing key for chrome (for selenium, functional tests)
RUN apt-key adv --no-tty --keyserver keyserver.ubuntu.com --recv-keys 78BD65473CB3BD13

RUN --mount=target=/var/lib/apt/lists,type=cache,sharing=locked \
    --mount=target=/var/cache/apt,type=cache,sharing=locked \
    apt-get update && \
    apt-get -y --no-install-recommends build-dep \
	python3-psycopg2 python3-lxml python3-pil python3-ldap

RUN --mount=target=/var/lib/apt/lists,type=cache,sharing=locked \
    --mount=target=/var/cache/apt,type=cache,sharing=locked \
    apt-get update && \
    apt-get -y --no-install-recommends install \
	libsnmp40 \
	cron \
	libjpeg62 \
	postgresql postgresql-contrib postgresql-client \
	libxml2-dev libxslt1-dev \
	libwww-perl \
	firefox xvfb \
	imagemagick \
	x11vnc google-chrome-stable cloc \
        cmake nbtscan libtidy5deb1


# Now install NodeJS and NPM for Javascript testing needs -
RUN --mount=target=/var/lib/apt/lists,type=cache,sharing=locked \
    --mount=target=/var/cache/apt,type=cache,sharing=locked \
    curl -sL https://deb.nodesource.com/setup_18.x  | bash - && \
    apt-get install -y --no-install-recommends nodejs

# Install geckodriver to properly run Selenium tests in Firefox versions>=47
ENV GECKOVERSION=0.35.0
RUN cd /tmp && \
    wget https://github.com/mozilla/geckodriver/releases/download/v$GECKOVERSION/geckodriver-v$GECKOVERSION-linux64.tar.gz && \
    tar xvzf geckodriver-v$GECKOVERSION-linux64.tar.gz && \
    mv geckodriver /usr/local/bin/

# Install chromedriver to properly run Selenium tests in Chrome, if need be
# Ref: https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json
ENV CHROMEDRIVERVERSION=131.0.6778.69
RUN cd /tmp && \
    wget https://storage.googleapis.com/chrome-for-testing-public/$CHROMEDRIVERVERSION/linux64/chromedriver-linux64.zip && \
    unzip chromedriver-linux64.zip && \
    mv chromedriver-linux64/chromedriver /usr/local/bin/

# Install required Python tools in a virtualenv, as required by Ubuntu
ENV PATH=/opt/venvs/nav/bin:$PATH
RUN python3.9 -m venv /opt/venvs/nav && \
    /opt/venvs/nav/bin/pip install --upgrade pip setuptools tox

# Add a build user
ENV USER=build
RUN adduser --system --group --home=/source --shell=/bin/bash $USER && \
    mkdir -p /usr/share/nav/var/uploads && \
    chown -R $USER /usr/share/nav

ENV WORKSPACE=/source
ENV HOME=/source

COPY scripts/ /
WORKDIR /source
ENTRYPOINT ["/entrypoint.sh"]
RUN chmod 755 /*.sh
