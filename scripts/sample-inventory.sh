#!/bin/env -S nagzen -f


service PING --template
service SNMP --template

host cred_snmp:credentials --template _SNMP_VERSION=3

host centos --template
service PING
service SNMP

host TEST1:centos --address=127.0.0.1 parent=SELF

host TEST1 --address=127.0.0.1 parent=SELF


