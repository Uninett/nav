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
FROM --platform=linux/amd64 debian:bookworm

# We're using mount caches, so don't clean the apt cache after every apt command!
RUN rm -f /etc/apt/apt.conf.d/docker-clean; echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' > /etc/apt/apt.conf.d/keep-cache

#### Prepare the OS base setup ###

ENV DEBIAN_FRONTEND=noninteractive

RUN --mount=target=/var/lib/apt/lists,type=cache,sharing=locked \
    --mount=target=/var/cache/apt,type=cache,sharing=locked \
    apt-get update && \
    apt-get -y --no-install-recommends install \
            locales \
            python3-dbg python3-venv gdb \
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
ENV LANG=${LOCALE}
ENV LC_ALL=${LOCALE}
RUN echo "${TIMEZONE}" > /etc/timezone && cp /usr/share/zoneinfo/${TIMEZONE} /etc/localtime

#### Install various build and runtime requirements as Debian packages ####

RUN --mount=target=/var/lib/apt/lists,type=cache,sharing=locked \
    --mount=target=/var/cache/apt,type=cache,sharing=locked \
    apt-get update \
    && apt-get -y --no-install-recommends install \
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

# Make an unprivileged nav user that corresponds to the user building this image.
# Allow this user to run sudo commands and make a virtualenv for them to install NAV in
ARG UID
ARG GID
RUN groupadd --gid "$GID" nav ; adduser --home=/source --shell=/bin/bash --uid=$UID --gid=$GID nav
RUN echo "nav    ALL =(ALL: ALL) NOPASSWD: ALL" > /etc/sudoers.d/nav
# Ensure the virtualenv's bin directory is on everyone's PATH variable
RUN sed -e 's,^Defaults.*secure_path.*,Defaults        secure_path="/opt/venvs/nav/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",' -i /etc/sudoers
RUN sed -e 's,^ENV_SUPATH.*,ENV_SUPATH      PATH=/opt/venvs/nav/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",' -i /etc/login.defs
RUN sed -e 's,^ENV_PATH.*,ENV_PATH        PATH=/opt/venvs/nav/bin:/usr/local/bin:/usr/bin:/bin:/usr/local/games:/usr/games",' -i /etc/login.defs

RUN --mount=type=cache,target=/source/.cache,sharing=locked \
    mkdir -p /opt/venvs/nav && chown nav /opt/venvs/nav && \
    mkdir -p /etc/nav && chown nav /etc/nav && \
    chown -R nav /source/.cache
USER nav
ENV PATH=/opt/venvs/nav/bin:$PATH
RUN python3.11 -m venv /opt/venvs/nav
RUN --mount=type=cache,target=/source/.cache,sharing=locked \
    pip install --upgrade setuptools wheel pip-tools build

#################################################################################
### COPYing the requirements file to pip-install Python requirements may bust ###
### Docker's cache at this point, so everything expensive you want to keep in ###
### the cache should go before this.                                          ###
#################################################################################

COPY tools/docker/supervisord.conf /etc/supervisor/conf.d/nav.conf

# Make an initial install of all NAV requirements into the virtualenv, to make
# builds inside the container go faster
COPY requirements/ /requirements
COPY requirements.txt /
COPY constraints.txt /
COPY tests/requirements.txt /test-requirements.txt
COPY doc/requirements.txt /doc-requirements.txt
RUN --mount=type=cache,target=/source/.cache,sharing=locked \
    cd /opt/venvs/nav && \
    pip-compile --resolver=backtracking --output-file ./requirements.txt.lock -c /constraints.txt /requirements.txt /test-requirements.txt /doc-requirements.txt ; \
    pip install -r ./requirements.txt.lock

ARG CUSTOM_PIP=ipython
RUN --mount=type=cache,target=/source/.cache,sharing=locked \
    pip install ${CUSTOM_PIP}

COPY tools/docker/full-nav-restore.sh /usr/local/sbin/full-nav-restore.sh

VOLUME ["/source"]
ENV    DJANGO_SETTINGS_MODULE=nav.django.settings
EXPOSE 8080

CMD        ["/source/tools/docker/run.sh"]
