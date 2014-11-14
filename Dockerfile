# NAV web development container
#
# This container aims at providing all the build- and runtime dependencies of
# NAV in a single container, and allowing for running them all directly off
# the code in your source code checkout.
#
# Run the container with your checked out NAV source code directory mounted on
# the '/source' volume to build and run all the necessary components inside
# the container. Changes to you SASS source files will be automatically
# detected and compiled, and any changes to files in the python directory will
# be immediately live in the web interface.
#
# The NAV web interface is exposed through Apache/WSGI on port 80.
# The graphite web interface is exposed through Apache/WSGI on port 8000.
#
# REQUIREMENT: For the users inside the container to be able to access the
# source code mounted at /source, the directory and its files on the host must
# be world-readable!
# 
# TODO: Possibly split this into separate containers for PostgreSQL, Graphite
# and NAV.
#
FROM mbrekkevold/wheezy-no

ENV DEBIAN_FRONTEND noninteractive

#### Install various build and runtime requirements as Debian packages ####

RUN apt-get update

RUN apt-get -y --no-install-recommends build-dep \
            python-psycopg2 python-lxml librrd-dev python-imaging python-ldap ;\
    \
    apt-get -y --no-install-recommends install \
            locales mercurial subversion git-core python-virtualenv python-pip \
            build-essential librrd-dev python-dev autoconf automake libsnmp15 \
            cron sudo libapache2-mod-wsgi rubygems inotify-tools python-cairo \
            postgresql-9.1 postgresql-contrib-9.1 postgresql-client openssh-server \
            supervisor

RUN pip install whisper carbon graphite-web django-tagging

RUN gem install --version '3.3.9' sass ;\
    gem install --version '~> 0.9' rb-inotify

RUN adduser --system --group --no-create-home --home=/source --shell=/bin/bash nav ;\
    adduser --system --group --no-create-home --home=/opt/graphite --shell=/bin/bash graphite

RUN echo "import sys\nsys.path.append('/source/python')" > /etc/python2.7/sitecustomize.py
RUN apt-get clean

RUN echo "export APACHE_ARGUMENTS='-DFOREGROUND'" >> /etc/apache2/envvars


#################################################################################
### ADDing the requirements file to pip-install Python requirements will bust ###
### Docker's cache at this point, so everything you want to keep in the cache ###
### should go before this.                                                    ###
#################################################################################

ADD tools/docker/supervisord.conf /etc/supervisor/conf.d/nav.conf

ADD requirements.txt /
ADD tests/requirements.txt /test-requirements.txt
RUN pip install -r /requirements.txt ; pip install -r /test-requirements.txt

ADD etc/graphite /opt/graphite/conf
ADD tools/docker/carbon.conf /opt/graphite/conf/
RUN cp /opt/graphite/conf/graphite.wsgi.example /opt/graphite/conf/graphite.wsgi ;\
    chown -R graphite:graphite /opt/graphite ;\
    sudo -u graphite python /opt/graphite/webapp/graphite/manage.py syncdb --noinput

ADD tools/docker/nav-apache-site.conf /etc/apache2/sites-available/nav-site
RUN a2dissite 000-default; a2ensite nav-site

RUN echo "root:password" | chpasswd

VOLUME ["/source"]
ENV    PYTHONPATH /source/python
ENV    PATH /source/bin:/usr/local/sbin:/usr/local/bin:/usr/bin:/usr/sbin:/sbin:/bin
RUN    echo "PATH=$PATH" > /etc/profile.d/navpath.sh
EXPOSE 22 80 8000
CMD    ["/source/tools/docker/run.sh"]
