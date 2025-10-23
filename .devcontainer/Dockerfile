ARG DEBIAN_VERSION=bookworm
ARG MAIN_PYTHON_VERSION=3.11

FROM mcr.microsoft.com/devcontainers/python:1-${MAIN_PYTHON_VERSION}-${DEBIAN_VERSION}
ARG DEBIAN_VERSION
ARG MAIN_PYTHON_VERSION

ENV PYTHONUNBUFFERED=1

# [Optional] If your requirements rarely change, uncomment this section to add them to the image.
# COPY requirements.txt /tmp/pip-tmp/
# RUN pip3 --disable-pip-version-check --no-cache-dir install -r /tmp/pip-tmp/requirements.txt \
#    && rm -rf /tmp/pip-tmp

# We're using mount caches, so don't clean the apt cache after every apt command!
RUN rm -f /etc/apt/apt.conf.d/docker-clean; echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' > /etc/apt/apt.conf.d/keep-cache

## Use deb.nodesource.com to fetch more modern versions of Node/NPM than Debian can provide
ARG TIMEZONE=Europe/Oslo
ARG LOCALE=en_US.UTF-8
ARG ENCODING=UTF-8
RUN echo "${LOCALE} ${ENCODING}" > /etc/locale.gen && locale-gen ${LOCALE} && update-locale LANG=${LOCALE} LC_ALL=${LOCALE}
ENV LANG=${LOCALE}
ENV LC_ALL=${LOCALE}
RUN echo "${TIMEZONE}" > /etc/timezone && cp /usr/share/zoneinfo/${TIMEZONE} /etc/localtime

### Install various build and runtime requirements, as well as useful command line tools for development

RUN --mount=target=/var/lib/apt/lists,type=cache,sharing=locked \
    --mount=target=/var/cache/apt,type=cache,sharing=locked \
    apt-get update \
    && apt-get -y --no-install-recommends install \
       python3-dev \
       git \
       libsnmp40 \
       cron \
       inotify-tools \
       vim \
       less \
       nbtscan \
       # Python package build deps: \
       libpq-dev \
       libjpeg-dev \
       libz-dev \
       libldap2-dev \
       libsasl2-dev \
       # Necessary to run LDAP authentication: \
       libldap-common \
       # Useful tools for network debugging and SNMP querying: \
       dnsutils \
       iproute2 \
       iputils-ping \
       snmp \
       netcat-openbsd

ENV UV_PROJECT_ENVIRONMENT=/home/vscode/.venv
ENV UV_PYTHON=${MAIN_PYTHON_VERSION}
ENV PATH="${UV_PROJECT_ENVIRONMENT}/bin:${PATH}"

RUN echo "This is the original base image for NAV devcontainer" > /README.TXT
