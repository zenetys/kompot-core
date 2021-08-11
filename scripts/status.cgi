#!/usr/bin/gawk -f
#
##
## Copyright (c) 2018-2019 Benoit DOLEZ - License MIT
##
## Permission is hereby granted, free of charge, to any person obtaining
## a copy of this software and associated documentation files (the
## "Software"), to deal in the Software without restriction, including
## without limitation the rights to use, copy, modify, merge, publish,
## distribute, sublicense, and/or sell copies of the Software, and to
## permit persons to whom the Software is furnished to do so, subject to
## the following conditions:
##
## The above copyright notice and this permission notice shall be
## included in all copies or substantial portions of the Software.
##
## THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
## EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
## MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
## NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
## LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
## OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
## WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
##
## Author: Benoit DOLEZ <bdolez@ant-computing.com>
## Author: Benoit DOLEZ <bdolez@zenetys.com>
## Version: 1.0
## Description: return nagios status
##
#

BEGIN {
  HOSTSTATUS = "hoststatus";

  while (getline line < NAGIOS_STATUS_FILE)) {
    if (match(line, "^([a-z]+) {", a)) {
      block = 1;
      section = a[1];
    }
    else if (match(line, "^}")) {
      block = 0;
    }
    else if (block == 1 && match(line, "^\t([^=]+)=(.*)", a) {
      # pass unwanted attributes
      if (!REGISTER[a[1]]) next;
      
      if (section == HOSTSTATUS && a[1] == "host_name") {
        host_name = a[2];
        host_list[host_name] = 1;
        host_attrs[host_name, a[1]] = a[2];
      }
      else if (section == HOSTSTATUS) {
        host_attrs[host_name, a[1]] = a[2];
      }
      else if (section == SERVICESTATUS && a[1] == "host_name") {
        host_name = a[2];
      }
      else if (section == SERVICESTATUS && a[1] == "service_description") {
        service_name = a[2];
        service_attrs[host_name, service_name, "host_name"] = host_name;
        service_attrs[host_name, service_name, a[1]] = a[2];
      }
      else if (section == SERVICESTATUS) {
        service_attrs[host_name, service_name, a[1]] = a[2];
      }
    }
  }
  exit 0;
}


