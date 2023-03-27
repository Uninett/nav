FROM debian:bullseye
RUN apt-get update && apt-get install -y openssh-server socat sudo tini
COPY snmp_forward.sh /
RUN echo '%adm ALL=NOPASSWD: /usr/bin/socat' > /etc/sudoers.d/socat
RUN chmod 0440 /etc/sudoers.d/socat
ARG USER
RUN useradd -g adm --no-create-home $USER
USER $USER

ENTRYPOINT ["tini", "/snmp_forward.sh"]
