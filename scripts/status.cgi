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
  NAGIOS_STATUS_FILE = ENVIRON["NAGIOS_STATUS_FILE"];
  QUERY_STRING = ENVIRON["QUERY_STRING"];

  L5 = " "( L4 = " "( L3 = " "( L2 = " "(L1 = " "))));

  HOSTSTATUS = "hoststatus";
  SERVICESTATUS = "servicestatus";
  
  REGISTER_S["host_name"] = 1;
  REGISTER_S["service_description"] = 1;
  REGISTER_S["plugin_output"] = 1;
  REGISTER_I["current_state"] = 1;
  REGISTER_I["last_check"] = 1;
  REGISTER_I["current_attempt"] = 1;
  REGISTER_I["state_type"] = 1;
  REGISTER_I["last_state_change"] = 1;
  REGISTER_I["last_hard_state_change"] = 1;
  REGISTER_I["last_update"] = 1;
  REGISTER_I["notifications_enabled"] = 1;
  REGISTER_I["problem_has_been_acknowledged"] = 1;
  REGISTER_I["active_checks_enabled"] = 1;
  REGISTER_I["passive_checks_enabled"] = 1;
  REGISTER_I["is_flapping"] = 1;
  REGISTER_S["__TRACK"] = 1;
  REGISTER_S["__AUTOTRACK"] = 1;
  
  split(QUERY_STRING, a);
  for (attr in a) {
    if (substr(a, 1, 9) == "hostname=") {
      filter = substr(a, 10);
      break;
    }
  }
  
  printf("{\n");
  printf("%s\"data\": {\n", L1);
  printf("%s\"servicelist\": {\n", L2);

  while (getline line < NAGIOS_STATUS_FILE) {
    # printf("[DEBUG] line: %s\n", line) >> "/dev/stderr";
    if (match(line, "^([a-z]+) {", a)) {
      block = 1;
      if (section == SERVICESTATUS && section != a[1])
        printf("\n%s}\n",L3);
      section = a[1];
      # printf("[DEBUG] start block(%s)\n", section);
    }
    else if (match(line, "^\t}$")) {
      if (section == HOSTSTATUS)
        host_name = "";
      if (section == SERVICESTATUS)
        printf("\n%s}",L4);
      # printf("[DEBUG] end block(%s)\n", section);
      block = 0;
    }
    else if (block == 1 && match(line, "^\t([^=]+)=(.*)", a)) {
      # pass unwanted attributes
      if (!(a[1] in REGISTER_S) && !(a[1] in REGISTER_I)) continue;
      
      if (section == HOSTSTATUS && a[1] == "host_name") {
        host_name = a[2];
        host_list[host_name] = 1;
        host_attrs[host_name, a[1]] = a[2];
      }
      else if (section == HOSTSTATUS) {
        host_attrs[host_name, a[1]] = a[2];
      }
      else if (section == SERVICESTATUS && a[1] == "host_name") {
        # section change
        if (a[2] != host_name) {
          if (host_name) printf("%s},\n", L3);
          host_name = a[2];
          printf("%s\"%s\": {\n", L3, host_name);
          printf("%s\"%s\": {\n", L4, "_HOST_");
          host_attrs[host_name, "display_name"] = "_HOST_";
          printf("%s\"%s\": \"%s\"", L5, "service_description", "_HOST_");
          for (attr in REGISTER_S) {
            if (!((host_name,attr) in host_attrs)) continue;
            printf(",\n%s\"%s\": \"%s\"", L5, attr, host_attrs[host_name, attr]);
          }
          for (attr in REGISTER_I) {
            if (!((host_name, attr) in host_attrs)) continue;
            printf(",\n%s\"%s\": %s", L5, attr, host_attrs[host_name, attr]);
          }
          printf("\n%s},\n", L4);
        }
        else {
          printf(",\n");
        }
      }
      else if (section == SERVICESTATUS && a[1] == "service_description") {
        printf("%s\"%s\": {\n", L4, a[2]);
        printf("%s\"%s\": \"%s\",\n", L5, "host_name", host_name);
        printf("%s\"%s\": \"%s\"", L5, a[1], a[2]);
      }
      else if (section == SERVICESTATUS) {
        if (a[1] in REGISTER_S)
          printf(",\n%s\"%s\": \"%s\"", L5, a[1],
                 gensub("[\\\\\"]", "\\\\\\0", "g", a[2]));
        else
          printf(",\n%s\"%s\": %s", L5, a[1], a[2]);
      }
    }
  }
  
  printf("%s}\n", L2);
  printf("%s}\n", L1);
  printf("}\n");
  exit 0;
}


