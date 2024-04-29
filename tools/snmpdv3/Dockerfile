FROM polinux/snmpd
COPY snmpd.conf /etc/snmp/snmpd.conf
EXPOSE 161:161/udp
CMD ["-c", "/etc/snmp/snmpd.conf"]
