FROM mbrekkevold/navbase-debian:stretch

RUN apt-get update \
   && apt-get -y install \
      python-dev python-pip gpg build-essential \
      libcairo2-dev libffi-dev

RUN adduser --system --group --no-create-home --home=/opt/graphite --shell=/bin/bash graphite

ENV PYTHONPATH =/opt/graphite/lib/:/opt/graphite/webapp/
RUN pip install --no-binary=:all: whisper
RUN pip install --no-binary=:all: carbon
RUN pip install --no-binary=:all: graphite-web

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
