FROM debian:stretch
RUN /bin/bash -c 'apt-get update&&apt-get install -y openssh-server socat sudo'
ADD snmp_forward.sh /
RUN bash -c "echo '%adm ALL=NOPASSWD: /usr/bin/socat' > /etc/sudoers.d/socat"
RUN chmod 0440 /etc/sudoers.d/socat
ARG USER
RUN useradd -g adm --no-create-home $USER
USER $USER
