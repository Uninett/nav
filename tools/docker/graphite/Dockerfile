FROM debian:bookworm

#### Prepare the OS base setup ###

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get -y --no-install-recommends install \
            locales \
            sudo python3 supervisor \
	        gnupg debian-keyring debian-archive-keyring ca-certificates

ARG TIMEZONE=Europe/Oslo
ARG LOCALE=en_US.UTF-8
ARG ENCODING=UTF-8
RUN echo "${LOCALE} ${ENCODING}" > /etc/locale.gen && locale-gen ${LOCALE} && update-locale LANG=${LOCALE} LC_ALL=${LOCALE}
ENV LANG=${LOCALE}
ENV LC_ALL=${LOCALE}
RUN echo "${TIMEZONE}" > /etc/timezone && cp /usr/share/zoneinfo/${TIMEZONE} /etc/localtime

RUN apt-get update \
   && apt-get -y install graphite-carbon graphite-web

COPY carbon.conf /etc/carbon/
COPY supervisord.conf /etc/supervisor/conf.d/graphite.conf

RUN echo "TIME_ZONE = 'Europe/Oslo'" >> /etc/graphite/local_settings.py && \
    echo "SECRET_KEY = '$(gpg -a --gen-random 1 51)'" >> /etc/graphite/local_settings.py && \
    echo "DEBUG=True" >> /etc/graphite/local_settings.py
USER _graphite
ENV DJANGO_SETTINGS_MODULE=graphite.settings
RUN django-admin migrate auth --noinput --settings=graphite.settings \
    && django-admin migrate --run-syncdb --noinput --settings=graphite.settings
USER root

EXPOSE 2003/udp 2003 2004 8000
CMD    ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]
