# NAV web development container
#
# This container aims at providing all the build- and runtime dependencies of
# NAV in a single container, and allowing for running them all directly off
# the code in your source code checkout.
#
# Run the container with your checked out NAV source code directory mounted on
# the '/source' volume and run the command /source/tools/docker/run.sh to
# build and run all the necessary components inside the container. This
# command will eventually run sass with the --watch option to watch the
# htdocs/sass directory and automatically compile stylesheets on every change
# that takes place.
#
# The NAV web interface is exposed through Apache/WSGI on port 80.
# The graphite web interface is exposed through Apache/WSGI on port 8080.
#
# REQUIREMENT: For the users inside the container to be able to access the
# source code mounted at /source, the directory and its files on the host must
# be world-readable!
# 
# TODO: Split this into separate containers for PostgreSQL, Graphite and NAV.
#
FROM tianon/debian:wheezy

#### Initialize apt repositories ####

RUN echo "\n\
\
deb http://security.debian.org/ wheezy/updates main\n\
deb-src http://security.debian.org/ wheezy/updates main\n\
deb http://ftp.no.debian.org/debian wheezy main contrib non-free\n\
deb-src http://ftp.no.debian.org/debian wheezy main contrib non-free\n\
deb http://ftp.no.debian.org/debian wheezy-updates main contrib non-free\n\
deb-src http://ftp.no.debian.org/debian wheezy-updates main contrib non-free\n\
\
" > /etc/apt/sources.list
RUN apt-get -y update

#### Install various build and runtime requirements as Debian packages ####

RUN apt-get -y --no-install-recommends build-dep \
  python-psycopg2 python-lxml librrd-dev python-imaging python-ldap

RUN apt-get -y --no-install-recommends install \
  locales mercurial subversion git-core python-virtualenv python-pip \
  build-essential librrd-dev python-dev autoconf automake libsnmp15 \
  cron sudo libapache2-mod-wsgi rubygems inotify-tools python-cairo \
  openssh-server

#### Ensure we have a UTF-8 locale before installing PostgreSQL ###

RUN echo 'en_US.UTF-8 UTF-8' > /etc/locale.gen
RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LC_ALL en_US.UTF-8
RUN apt-get -y --no-install-recommends install postgresql-9.1 postgresql-client

RUN gem install sass
RUN gem install --version '~> 0.9' rb-inotify

RUN pip install whisper carbon graphite-web django-tagging

RUN adduser --system --group --no-create-home --home=/source --shell=/bin/bash nav
RUN adduser --system --group --no-create-home --home=/opt/graphite --shell=/bin/bash graphite

RUN echo "import sys\nsys.path.append('/source/python')" > /etc/python2.7/sitecustomize.py

RUN apt-get clean

#################################################################################
### ADDing the requirements file to pip-install Python requirements will bust ###
### Docker's cache at this point, so everything you want to keep in the cache ###
### should go before this.                                                    ###
#################################################################################

ADD requirements.txt /
ADD tests/requirements.txt /test-requirements.txt
RUN pip install -r /requirements.txt
RUN pip install -r /test-requirements.txt

ADD etc/graphite /opt/graphite/conf
ADD tools/docker/carbon.conf /opt/graphite/conf/
RUN cp /opt/graphite/conf/graphite.wsgi.example /opt/graphite/conf/graphite.wsgi
RUN chown -R graphite:graphite /opt/graphite
RUN sudo -u graphite python /opt/graphite/webapp/graphite/manage.py syncdb --noinput

ADD tools/docker/nav-apache-site.conf /etc/apache2/sites-available/nav-site
RUN a2dissite 000-default; a2ensite nav-site

VOLUME ["/source"]
ENV PYTHONPATH /source/python
EXPOSE 22 80 8080
