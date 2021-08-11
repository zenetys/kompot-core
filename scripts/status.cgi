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


function main() {
  while (getline line < NAGIOS_STATUS_FILE) {
    # printf("[DEBUG] line: %s\n", line) >> "/dev/stderr";
    if (substr(line, 1, 1) != "\t" && substr(line, length(line)-1, 2) == " {") {
      new = substr(line, 1, length(line)-2);
      block = 1;
      if (section == SERVICESTATUS && section != new)
        printf("\n%s}\n", L3);
      section = new;
      # printf("[DEBUG] start block(%s)\n", section);
    }
    else if (line == "\t}") {
      if (section == HOSTSTATUS)
        host_name = "";
      if (section == SERVICESTATUS && host_name)
        printf("\n%s}",L4);
      # printf("[DEBUG] end block(%s)\n", section);
      block = 0;
    }
    else if (block == 1 && substr(line, 1, 1) == "\t") {
      pval = index(line, "=");
      var = substr(line, 2, pval-2);
      val = substr(line, pval+1);
      # pass unwanted attributes
      if (!(var in REGISTER_S) && !(var in REGISTER_I)) continue;
      
      if (section == HOSTSTATUS && var == "host_name") {
        if (filter && filter != val) continue;
        host_name = val;
        # host_list[host_name] = 1;
        host_attrs[host_name, var] = val;
      }
      else if (section == HOSTSTATUS) {
        host_attrs[host_name, var] = val;
      }
      else if (section == SERVICESTATUS && var == "host_name") {

        # section change
        if (val != host_name) {
          if (filter && filter != val) {
             host_name = "";
             continue;
          }
          if (host_name) printf("%s},\n", L3);
          host_name = val;
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
      else if (section == SERVICESTATUS && host_name && var == "service_description") {
        printf("%s\"%s\": {\n", L4, val);
        printf("%s\"%s\": \"%s\",\n", L5, "host_name", host_name);
        printf("%s\"%s\": \"%s\"", L5, var, val);
      }
      else if (section == SERVICESTATUS && host_name) {
        if (var in REGISTER_S)
          printf(",\n%s\"%s\": \"%s\"", L5, var,
                 gensub("[\\\\\"]", "\\\\\\0", "g", val));
        else
          printf(",\n%s\"%s\": %s", L5, var, val);
      }
    }
  }
}

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
  
  split(QUERY_STRING, a, "&");
  for (ia in a) {
    # printf("DEBUG QS(%s)\n", a[ia]) > "/dev/stderr";
    if (substr(a[ia], 1, 9) == "hostname=") {
      filter = substr(a[ia], 10);
    }
    else if (substr(a[ia], 1, 6) == "query=") {
      query = substr(a[ia], 7);
    }
  }
  # printf("[DEBUG] filter=%s (QS=%s)\n", filter, QUERY_STRING) > "/dev/stderr";
  
  printf("{\n");
  printf("%s\"data\": {\n", L1);

  if (query == "servicelist") {
    printf("%s\"servicelist\": {\n", L2);
    main();
    printf("%s}\n", L2);
  }
  else if (query == "hostlist") {
    printf("%s\"servicelist\": {\n", L2);
    main();
    printf("%s}\n", L2);
  }

  printf("%s}\n", L1);
  printf("}\n");
  exit 0;
}


