

FROM debian:wheezy

ENV DEBIAN_FRONTEND noninteractive
ENV DISPLAY :99
ENV ADMINPASSWORD omicronpersei8

### Installing packages
RUN echo "deb http://ftp.us.debian.org/debian wheezy-backports main" >> /etc/apt/sources.list

# TODO: Might not need all the dependencies
RUN apt-get update && \
    \
    apt-get -y --no-install-recommends build-dep \
	python-psycopg2 python-lxml librrd-dev python-imaging python-ldap ;\
	\
    apt-get -y --no-install-recommends install \
	locales mercurial subversion git-core python-virtualenv python-pip \
	build-essential librrd-dev python-dev autoconf automake libsnmp15 \
	cron sudo libapache2-mod-wsgi rubygems inotify-tools python-cairo \
	postgresql-9.1 postgresql-contrib-9.1 postgresql-client openssh-server \
	supervisor ruby1.8-dev libxml2-dev libxslt1-dev net-tools \
	postgresql-server-dev-9.1 libpq-dev libwww-perl python-rrdtool \
	python-utidylib iceweasel xvfb nodejs-legacy curl chromium \
	python-iso8601

RUN pip install whisper carbon graphite-web django-tagging

RUN gem install sass ; \
    gem install --version '~> 0.9' rb-inotify

RUN apt-get clean

RUN adduser --system --group --no-create-home --home=/source --shell=/bin/bash navcron

# This requirements file is not the complete nav requirements
ADD requirements.txt /test-requirements.txt
RUN pip install -r /test-requirements.txt

# This does not make files in source accessible for RUN-commands
VOLUME ["/source"]

# Just a message to make me feel better when the build fails
RUN echo "Hello from container you handsome devil ;)"

CMD ["/source/tests/test.sh"]
