FROM mbrekkevold/navbase-debian:jessie
ADD sources.list /etc/apt/sources.list
ADD apt.conf /etc/apt/apt.conf

RUN apt-get update \
   && apt-get -y --no-install-recommends install \
      python-django \
      python-cairo

RUN adduser --system --group --no-create-home --home=/opt/graphite --shell=/bin/bash graphite
RUN pip install whisper carbon graphite-web==0.9.14 django-tagging==0.3.4 pytz

ADD carbon.conf /opt/graphite/conf/
ADD supervisord.conf /etc/supervisor/conf.d/graphite.conf

RUN echo "TIME_ZONE = 'Europe/Oslo'" > /opt/graphite/webapp/graphite/local_settings.py && \
    echo "SECRET_KEY = '$(gpg -a --gen-random 1 51)'" >> /opt/graphite/webapp/graphite/local_settings.py
RUN cp /opt/graphite/conf/storage-schemas.conf.example /opt/graphite/conf/storage-schemas.conf && \
    cp /opt/graphite/conf/storage-aggregation.conf.example /opt/graphite/conf/storage-aggregation.conf
RUN chown -R graphite:graphite /opt/graphite ;\
    su -c 'python /opt/graphite/webapp/graphite/manage.py syncdb --noinput' graphite


ENV    PYTHONPATH /source/python:/opt/graphite/webapp
EXPOSE 2003/udp 2003 2004 8000
CMD    ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]
