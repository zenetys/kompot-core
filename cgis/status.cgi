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

function dump_attr_json(sp, var, val) {
        if (var == "active_checks_enabled") {
          printf(",\n%s\"%s\": %s", sp, "checks_enabled", val==0?"false":"true");
        }
        else if (var in REGISTER_S) {
          printf(",\n%s\"%s\": \"%s\"", sp, var,
                 gensub("[\\\\\"]", "\\\\\\0", "g", val));
        }
        else if (var in REGISTER_I) {
          printf(",\n%s\"%s\": %s", sp, var, val);
        }
        else if (var in REGISTER_B) {
          printf(",\n%s\"%s\": %s", sp, var, val==0?"false":"true");
        }
        else if (var in REGISTER_T) {
          printf(",\n%s\"%s\": %s", sp, var, val*1000);
        }
}

function hostlist() {
  while (getline line < NAGIOS_STATUS_FILE) {
    if (ERRNOR) exit(1);
    # printf("[DEBUG] line: %s\n", line) >> "/dev/stderr";
    if (substr(line, 1, 1) != "\t" && substr(line, length(line)-1, 2) == " {") {
      new = substr(line, 1, length(line)-2);
      if (section == HOSTSTATUS && section != new) {
        printf("\n%s}\n", L3);
      }
      block = 1;
      section = new;
      # printf("[DEBUG] start block(%s)\n", section);
    }
    else if (line == "\t}") {
      # printf("[DEBUG] end block(%s)\n", section);
      block = 0;
    }
    else if (block == 1 && substr(line, 1, 1) == "\t") {
      pval = index(line, "=");
      var = substr(line, 2, pval-2);
      val = substr(line, pval+1);
      # pass unwanted attributes
      if (!(var in REGISTER_S) &&
          !(var in REGISTER_I) &&
          !(var in REGISTER_T) &&
          !(var in REGISTER_B))
        continue;
      
      if (section == HOSTSTATUS && var == "host_name") {
        if (filter && filter != val) { host_name = ""; continue; }
        if (host_name) printf("\n%s},\n", L3);
        host_name = val;
        printf("%s\"%s\": {\n", L3, host_name);
        printf("%s\"%s\": \"%s\"", L4, "name", val);
      }
      else if (section == HOSTSTATUS && host_name && var == "current_state") {
        dump_attr_json(L4, "status", HOST_STATE[val]);
      }
      else if (section == HOSTSTATUS && host_name) {
        dump_attr_json(L4, var, val);
      }
    }
  }
}

function servicelist() {
  while (getline line < NAGIOS_STATUS_FILE) {
    if (ERRNOR) exit(1);
    # printf("[DEBUG] line: %s\n", line) >> "/dev/stderr";
    if (substr(line, 1, 1) != "\t" && substr(line, length(line)-1, 2) == " {") {
      new = substr(line, 1, length(line)-2);
      block = 1;
      if (section == SERVICESTATUS && section != new) {
        printf("\n%s}\n", L3);
      }
      section = new;
      # printf("[DEBUG] start block(%s)\n", section);
    }
    else if (line == "\t}") {
      if (section == HOSTSTATUS) {
        host_name = "";
      }
      else if (section == SERVICESTATUS && host_name) {
        printf("\n%s}",L4);
      }
      # printf("[DEBUG] end block(%s)\n", section);
      block = 0;
    }
    else if (block == 1 && substr(line, 1, 1) == "\t") {
      pval = index(line, "=");
      var = substr(line, 2, pval-2);
      val = substr(line, pval+1);
      # pass unwanted attributes
      if (!(var in REGISTER_S) &&
          !(var in REGISTER_I) &&
          !(var in REGISTER_T) &&
          !(var in REGISTER_B))
        continue;
      
      if (section == HOSTSTATUS && var == "host_name") {
        if (filter && filter != val) { host_name = ""; continue; }
        host_name = val;
        # host_list[host_name] = 1;
        host_attrs[host_name, var] = val;
      }
      else if (section == HOSTSTATUS && host_name) {
        host_attrs[host_name, var] = val;
      }
      else if (section == SERVICESTATUS && var == "host_name") {

        # section change
        if (val != host_name) {
          if (filter && filter != val) { host_name = ""; continue; }
          if (host_name) printf("\n%s},\n", L3);
          host_name = val;
          printf("%s\"%s\": {\n", L3, host_name);
          if (0) {
            printf("%s\"%s\": {\n", L4, "_HOST_");
            printf("%s\"%s\": \"%s\"", L5, "description", "_HOST_");
            if (!((host_name,attr) in host_attrs)) continue;
            dump_attr_json(L5, attr, host_attrs[host_name, attr]);
            printf("\n%s},\n", L4);
          }
        }
        else {
          printf(",\n");
        }
      }
      else if (section == SERVICESTATUS && host_name) {
        if (var == "service_description") {
          printf("%s\"%s\": {\n", L4, val);
          printf("%s\"%s\": \"%s\",\n", L5, "host_name", host_name);
          printf("%s\"%s\": \"%s\"", L5, "description", val);
        }
        else if (var == "current_state") {
          dump_attr_json(L5, "status", SERVICE_STATE[val]);
        }
        else if (section == SERVICESTATUS && host_name) {
          dump_attr_json(L5, var, val);
        }
      }
    }
  }
}

function hoststatus() {
  while (getline line < NAGIOS_STATUS_FILE) {
	if (ERRNO) exit(1);
    # printf("[DEBUG] line: %s\n", line) >> "/dev/stderr";
    if (substr(line, 1, 1) != "\t" && substr(line, length(line)-1, 2) == " {") {
      new = substr(line, 1, length(line)-2);
      block = 1;
      section = new;
      current_state = "";
      # printf("[DEBUG] start block(%s)\n", section);
    }
    else if (line == "\t}") {

      if (current_state > 0 && host_name && current_notif == 1) {
        if (state[host_name] < current_state) {
          state[host_name] = current_state;
        }
        if (current_state > 4) {
          output[host_name] = sprintf("%s<b>%s:%s</b>: %s<br>", output[host_name], host_name, current_service, current_output);
        }
      }

      if (section == HOSTSTATUS) {
        host_name = "";
      }

      # printf("[DEBUG] end block(%s)\n", section);
      block = 0;
    }
    else if (block == 1 && substr(line, 1, 1) == "\t") {
      pval = index(line, "=");
      var = substr(line, 2, pval-2);
      val = substr(line, pval+1);
      # pass unwanted attributes

      if (section == HOSTSTATUS && var == "host_name") {
        if (filter && filter != val) { host_name = ""; continue; }
        host_name = val;
      }
      else if (section == HOSTSTATUS && host_name) {
        if (var == "current_state") {
          state[host_name] = GLOBAL_STATE[100+val];;
        }
      }
      else if (section == SERVICESTATUS && var == "host_name") {
        # section change
        if (val != host_name) {
          if (filter && filter != val) { host_name = ""; continue; }
          host_name = val;
        }
      }
      else if (section == SERVICESTATUS && host_name) {
        if (var == "current_state") {
          current_state = GLOBAL_STATE[110+val];
        }
        else if (var == "service_description") {
          current_service = val;
        }
        else if (var == "plugin_output") {
          current_output = val;
        }
        else if (var == "notifications_enabled") {
          current_notif = val;
        }
      }
    }
  }
  cr = "";
  for (host_name in state) {
    printf("%s%s\"%s\": {\n", cr, L3, host_name);
    printf("%s\"%s\": \"%s\",\n", L4, "name", host_name);
    printf("%s\"%s\": \"%s\",\n", L4, "output", gensub("(\"|\\\\)", "\\\\\\1", "g", output[host_name]));
    printf("%s\"%s\": %s\n", L4, "state", state[host_name]);
    printf("%s}", L3);
    cr = ",\n";
    if (ENVIRON["DUMP_FULL_OUTPUT"]) {
      FULL_OUTPUT = FULL_OUTPUT output[host_name];
    }
  }
  if (length(state) > 0) printf("%s\n", L3);
}

BEGIN {
  NAGIOS_STATUS_FILE = ENVIRON["NAGIOS_STATUS_FILE"];
  QUERY_STRING = ENVIRON["QUERY_STRING"];

  L5 = " "( L4 = " "( L3 = " "( L2 = " "(L1 = " "))));

  HOSTSTATUS = "hoststatus";
  SERVICESTATUS = "servicestatus";
  
  REGISTER_S["host_name"] = 1;
  REGISTER_S["service_description"] = 1;
  REGISTER_S["display_name"] = 1;
  REGISTER_S["plugin_output"] = 1;
  REGISTER_S["__TRACK"] = 1;
  REGISTER_S["__AUTOTRACK"] = 1;
  REGISTER_I["status"] = 1;
  REGISTER_I["current_state"] = 1;
  REGISTER_I["current_attempt"] = 1;
  REGISTER_I["state_type"] = 1;
  REGISTER_I["check_type"] = 1;
  REGISTER_T["last_check"] = 1;
  REGISTER_T["last_state_change"] = 1;
  REGISTER_T["last_hard_state_change"] = 1;
  REGISTER_T["last_update"] = 1;
  REGISTER_B["notifications_enabled"] = 1;
  REGISTER_B["problem_has_been_acknowledged"] = 1;
  REGISTER_B["active_checks_enabled"] = 1;
  REGISTER_B["passive_checks_enabled"] = 1;
  REGISTER_B["is_flapping"] = 1;

  # 1 => SERVICE_PENDING
  SERVICE_STATE[0] = 2;  # OK
  SERVICE_STATE[1] = 4;  # WARNING
  SERVICE_STATE[2] = 16; # CRITICAL
  SERVICE_STATE[3] = 8;  # UNKNOWN

  # 1 => HOST_PENDING
  HOST_STATE[0] = 2;     # UP
  HOST_STATE[1] = 4;     # DOWN
  HOST_STATE[2] = 8;     # UNREACHABLE

  GLOBAL_STATE[100] = 4; # HOST+UP
  GLOBAL_STATE[101] = 9; # HOST+DOWN
  GLOBAL_STATE[102] = 7; # HOST+UNREACHABLE
  GLOBAL_STATE[110] = 3; # SERVICE+OK
  GLOBAL_STATE[111] = 5; # SERVICE+WARNING
  GLOBAL_STATE[112] = 8; # SERVICE+CRITICAL
  GLOBAL_STATE[113] = 6; # SERVICE+UNKNOWN

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

  if (substr(ENVIRON["REQUEST_URI"], 1, 5) == "/api/") {
    if (ENVIRON["SCRIPT_NAME"]) {
      printf("Status: 200\r\n");
      printf("Content-Type: application/json\r\n");
      printf("\r\n");
    }
  }
  else if (query == "servicelist" || query == "hostlist") {
    if (ENVIRON["SCRIPT_NAME"]) {
      printf("Status: 200\r\n");
      printf("Content-Type: application/json\r\n");
      printf("\r\n");
    }
  }
  else {
    ret = system(ENVIRON["NAGIOS_STATUSJSON_CGI"]);
    if (ret > 0 && ret <= 127) {
      printf("Status: 500\r\n");
      printf("\r\n");
      exit(0);
    }
    exit(0);
  }

  printf("{\n");
  printf("%s\"data\": {\n", L1);

  if (query == "servicelist") {
    printf("%s\"servicelist\": {\n", L2);
    servicelist();
    printf("%s}\n", L2);
  }
  else if (query == "hostlist") {
    printf("%s\"hostlist\": {\n", L2);
    hostlist();
    printf("%s}\n", L2);
  }
  else {
    printf("%s\"hosts\": {\n", L2);
    hoststatus();
    printf("%s}", L2);
    if (ENVIRON["DUMP_FULL_OUTPUT"]) {
      printf(",\n%s\"output\": \"%s\"", L2, gensub("(\"|\\\\)", "\\\\\\1", "g", FULL_OUTPUT));
    }
    printf("\n");
  }

  printf("%s}\n", L1);
  printf("}\n");
  exit 0;
}

