FROM debian:buster

#### Prepare the OS base setup ###

ENV DEBIAN_FRONTEND noninteractive

RUN echo 'deb-src http://deb.debian.org/debian buster main' >> /etc/apt/sources.list.d/srcpkg.list && \
    echo 'deb-src http://security.debian.org/debian-security buster/updates main' >> /etc/apt/sources.list.d/srcpkg.list && \
    echo 'deb-src http://deb.debian.org/debian buster-updates main' >> /etc/apt/sources.list.d/srcpkg.list

RUN apt-get update && \
    apt-get -y --no-install-recommends install \
            locales \
            sudo python3-dev python3-pip python3-virtualenv build-essential supervisor \
	    debian-keyring debian-archive-keyring ca-certificates

ARG TIMEZONE=Europe/Oslo
ARG LOCALE=en_US.UTF-8
ARG ENCODING=UTF-8
RUN echo "${LOCALE} ${ENCODING}" > /etc/locale.gen && locale-gen ${LOCALE} && update-locale LANG=${LOCALE} LC_ALL=${LOCALE}
ENV LANG ${LOCALE}
ENV LC_ALL ${LOCALE}
RUN echo "${TIMEZONE}" > /etc/timezone && cp /usr/share/zoneinfo/${TIMEZONE} /etc/localtime

RUN apt-get update \
   && apt-get -y install \
      libcairo2-dev libffi-dev python3-setuptools gnupg

RUN adduser --system --group --no-create-home --home=/opt/graphite --shell=/bin/bash graphite

ENV PYTHONPATH =/opt/graphite/lib/:/opt/graphite/webapp/
RUN pip3 install --no-binary=:all: whisper
RUN pip3 install --no-binary=:all: carbon
RUN pip3 install --no-binary=:all: graphite-web

ADD carbon.conf /opt/graphite/conf/
ADD supervisord.conf /etc/supervisor/conf.d/graphite.conf

RUN echo "TIME_ZONE = 'Europe/Oslo'" > /opt/graphite/webapp/graphite/local_settings.py && \
    echo "SECRET_KEY = '$(gpg -a --gen-random 1 51)'" >> /opt/graphite/webapp/graphite/local_settings.py && \
    echo "DEBUG=True" >> /opt/graphite/webapp/graphite/local_settings.py
RUN cp /opt/graphite/conf/storage-schemas.conf.example /opt/graphite/conf/storage-schemas.conf && \
    cp /opt/graphite/conf/storage-aggregation.conf.example /opt/graphite/conf/storage-aggregation.conf
RUN chown -R graphite:graphite /opt/graphite \
    && su -c 'django-admin migrate auth --noinput --settings=graphite.settings' graphite \
    && su -c 'django-admin migrate --run-syncdb --noinput --settings=graphite.settings' graphite

EXPOSE 2003/udp 2003 2004 8000
CMD    ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]
