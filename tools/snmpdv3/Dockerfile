FROM polinux/snmpd
COPY snmpd.conf /etc/snmpd/snmpd.conf
EXPOSE 161:161/udp
CMD ["-c", "/etc/snmpd/snmpd.conf"]
