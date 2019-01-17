# NAV web development container
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
# The NAV web interface is exposed through Apache/WSGI on port 80.
#
# REQUIREMENT: For the users inside the container to be able to access the
# source code mounted at /source, the directory and its files on the host must
# be world-readable!
#
#
FROM mbrekkevold/navbase-debian:jessie

#### Install various build and runtime requirements as Debian packages ####

RUN apt-get update \
    && apt-get -y --no-install-recommends build-dep \
       python-psycopg2 \
       python-lxml \
       python-imaging \
       python-ldap

RUN apt-get update \
    && apt-get -y --no-install-recommends install \
       git-core \
       libsnmp30 \
       cron \
       sudo \
       apache2 \
       libapache2-mod-wsgi \
       inotify-tools \
       postgresql-client \
       vim \
       less \
       nbtscan

RUN adduser --system --group --no-create-home --home=/source --shell=/bin/bash nav



#################################################################################
### ADDing the requirements file to pip-install Python requirements may bust  ###
### Docker's cache at this point, so everything you want to keep in the cache ###
### should go before this.                                                    ###
#################################################################################

ADD tools/docker/supervisord.conf /etc/supervisor/conf.d/nav.conf

COPY requirements/ /requirements
ADD requirements.txt /
ADD tests/requirements.txt /test-requirements.txt
RUN pip install --upgrade pip tox setuptools && \
    hash -r && \
    pip install -r /requirements.txt && \
    pip install -r /test-requirements.txt

ADD tools/docker/nav-apache-site.conf /etc/apache2/sites-available/nav-site.conf
RUN a2dissite 000-default; a2ensite nav-site

ADD tools/docker/full-nav-restore.sh /usr/local/sbin/full-nav-restore.sh

VOLUME ["/source"]
ENV    DJANGO_SETTINGS_MODULE nav.django.settings
EXPOSE 80

ENTRYPOINT ["/source/tools/docker/entrypoint.sh"]
CMD        ["/source/tools/docker/run.sh"]
