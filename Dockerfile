# NAV development container. This is NOT SUITABLE for production use of NAV.
# For more production-oriented containerization, have a look at the separate
# project https://github.com/Uninett/nav-container
#
# This container aims at providing all the build- and runtime dependencies of
# NAV itself in a single container, and allowing for running them all directly
# off the code in your source code checkout. It is intended to be used as part
# of the docker-compose.yml file, where the PostgreSQL and Graphite services
# are defined in separate containers.
#
# Run the container with your checked out NAV source code directory mounted on
# the '/source' volume to build and run all the necessary components inside
# the container. Changes to you SASS source files will be automatically
# detected and compiled, and any changes to files in the python directory will
# be immediately live in the web interface.
#
# The NAV web interface is exposed through the Django development server on
# port 80.
#
# REQUIREMENT: For the users inside the container to be able to access the
# source code mounted at /source, the directory and its files on the host must
# be world-readable!
#
#
FROM --platform=linux/amd64 python:3.11-slim-bookworm

#### Prepare the OS base setup ###

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && \
    apt-get -y --no-install-recommends install \
            locales \
            python3-dbg gdb \
            sudo python3-dev python3-pip python3-virtualenv build-essential supervisor \
            debian-keyring debian-archive-keyring ca-certificates curl gpg

## Use deb.nodesource.com to fetch more modern versions of Node/NPM than Debian can provide
RUN curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /usr/share/keyrings/nodesource.gpg && \
    echo 'deb [arch=amd64 signed-by=/usr/share/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main' > /etc/apt/sources.list.d/nodesource.list && \
    apt-get update && \
    apt-get install -y nodejs

ARG TIMEZONE=Europe/Oslo
ARG LOCALE=en_US.UTF-8
ARG ENCODING=UTF-8
RUN echo "${LOCALE} ${ENCODING}" > /etc/locale.gen && locale-gen ${LOCALE} && update-locale LANG=${LOCALE} LC_ALL=${LOCALE}
ENV LANG ${LOCALE}
ENV LC_ALL ${LOCALE}
RUN echo "${TIMEZONE}" > /etc/timezone && cp /usr/share/zoneinfo/${TIMEZONE} /etc/localtime

#### Install various build and runtime requirements as Debian packages ####

RUN apt-get update \
    && apt-get -y --no-install-recommends install \
       build-essential \
       supervisor \
       git-core \
       libsnmp40 \
       cron \
       sudo \
       inotify-tools \
       postgresql-client \
       vim \
       less \
       nbtscan \
       # Python package build deps: \
       libpq-dev \
       libjpeg-dev \
       libz-dev \
       libldap2-dev \
       libsasl2-dev \
       # Useful tools for network debugging and SNMP querying: \
       dnsutils \
       iproute2 \
       iputils-ping \
       snmp

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN adduser --system --group --no-create-home --home=/source --shell=/bin/bash nav
RUN mkdir -p /source && echo "export PATH=$PATH" >> /source/.bashrc

RUN pip install --upgrade 'setuptools>=61' wheel && \
    pip install --upgrade pip pip-tools build

ARG CUSTOM_PIP=ipython
RUN pip install ${CUSTOM_PIP}

#################################################################################
### COPYing the requirements file to pip-install Python requirements may bust ###
### Docker's cache at this point, so everything expensive you want to keep in ###
### the cache should go before this.                                          ###
#################################################################################

COPY tools/docker/supervisord.conf /etc/supervisor/conf.d/nav.conf

COPY requirements/ /requirements
COPY requirements.txt /
COPY constraints.txt /
COPY tests/requirements.txt /test-requirements.txt
COPY doc/requirements.txt /doc-requirements.txt
RUN pip-compile --resolver=backtracking --output-file /requirements.txt.lock -c /constraints.txt /requirements.txt /test-requirements.txt /doc-requirements.txt
RUN pip install -r /requirements.txt.lock

COPY tools/docker/full-nav-restore.sh /usr/local/sbin/full-nav-restore.sh

# Set up for mounting live source code from git repo at /source
RUN    git config --global --add safe.directory /source
VOLUME ["/source"]
ENV    DJANGO_SETTINGS_MODULE nav.django.settings
EXPOSE 80

ENTRYPOINT ["/source/tools/docker/entrypoint.sh"]
CMD        ["/source/tools/docker/run.sh"]
