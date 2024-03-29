#!/bin/bash

export LC_ALL=C

(( ${#BASH_SOURCE[@]} > 1 )) && return

_UNIXCAT=${_UNIXCAT:-unixcat}
LIVESOCKET=${LIVESOCKET:-/var/spool/nagios/cmd/live.sock}
ENABLE_CV_COLUMNS=${ENABLE_CV_COLUMNS:-1}

# <name> <mode>, with <mode> an integer described as follows:
# 1: value from the object, should it be an host or a service (default)
# 2: host value
# 3: service value
# 4: value from the service if set, otherwise from the host
# 5: merge both + unique as a list of words
CV_COLUMNS=(
  _TRACK 1
  _AUTOTRACK 1
  _PROCEDURE 4
  _TAGS 5
)

CV_FIELD=(
  -2 # host custom variables
  -1 # service custoom variables
)

IFS=$'\n'
TAB=$'\t'
LIVESEP=( 10 9 11 61 )

# <property> <option>, with <option> an integer described as follows:
# 1: string or number detection (default)
# 2: skip on empty
# 3: array according to livestatus 3rd separator
# 4: key-value object, for custom_variables
JSON_FORMAT=(
  description 2
  groups 3
  host_custom_variables 4
  custom_variables 4
  _TAGS 3
)

# https://docs.checkmk.com/latest/en/livestatus_references.html

COMMON_COLUMNS=(
    # accept_passive_checks                 # Whether passive host checks are accepted (0/1)
    acknowledged                          # Whether the current host problem has been acknowledged (0/1)
    acknowledgement_type                  # Type of acknowledgement (0: none, 1: normal, 2: stick)
    # action_url                            # An optional URL to custom actions or information about this host
    # action_url_expanded                   # The same as action_url, but with the most important macros expanded
    active_checks_enabled                 # Whether active checks are enabled for the host (0/1)
    check_command                         # Nagios command for active host check of this host
    # check_command_expanded                # Nagios command for active host check of this host with the macros expanded
    # check_freshness                       # Whether freshness checks are activated (0/1)
    check_interval                        # Number of basic interval lengths between two scheduled checks of the host
    # check_options                         # The current check option, forced, normal, freshness... (0-2)
    # check_period                          # Time period in which this host will be checked. If empty then the host will always be checked.
    check_type                            # Type of check (0: active, 1: passive)
    checks_enabled                        # Whether checks of the host are enabled (0/1)
    # comments                              # A list of the ids of all comments of this host
    # comments_with_extra_info              # A list of all comments of the host with id, author, comment, entry type and entry time
    # comments_with_info                    # A list of all comments of the host with id, author and comment
    # contact_groups                        # A list of all contact groups this host is in
    # contacts                              # A list of all contacts of this host, either direct or via a contact group
    current_attempt                       # Number of the current check attempts
    # current_notification_number           # Number of the current notification
    # custom_variable_names                 # A list of the names of the custom variables
    # custom_variable_values                # A list of the values of the custom variables
    # custom_variables                      # A dictionary of the custom variables
    # display_name                          # Optional display name of the host - not used by Nagios' web interface
    # downtimes                             # A list of the ids of all scheduled downtimes of this host
    # downtimes_with_extra_info             # A list of the scheduled downtimes(...) recurring and is_pending
    # downtimes_with_info                   # A list of the scheduled downtimes of the host with id, author and comment
    # event_handler                         # Nagios command used as event handler
    # event_handler_enabled                 # Whether event handling is enabled (0/1)
    # execution_time                        # Time the host check needed for execution
    # first_notification_delay              # Delay before the first notification
    # flap_detection_enabled                # Whether flap detection is enabled (0/1)
    groups                                # A list of all host groups this host is in
    hard_state                            # The effective hard state of the host (eliminates a problem in hard_state)
    # high_flap_threshold                   # High threshold of flap detection
    icon_image                            # The name of an image file to be used in the web pages
    # icon_image_alt                        # Alternative text for the icon_image
    # icon_image_expanded                   # The same as icon_image, but with the most important macros expanded
    # in_check_period                       # Whether this host is currently in its check period (0/1)
    # in_notification_period                # Whether this host is currently in its notification period (0/1)
    # in_service_period                     # Whether this host is currently in its service period (0/1)
    # initial_state                         # Initial host state
    # is_executing                          # is there a host check currently running... (0/1)
    is_flapping                           # Whether the host state is flapping (0/1)
    # label_names                           # A list of the names of the labels
    # label_source_names                    # A list of the names of the label sources
    # label_source_values                   # A list of the values of the label sources
    # label_sources                         # A dictionary of the label sources
    # label_values                          # A list of the values of the labels
    # labels                                # A dictionary of the labels
    last_check                            # Time of the last check (Unix timestamp)
    last_hard_state                       # Last hard state
    last_hard_state_change                # Time of the last hard state change (Unix timestamp)
    # last_notification                     # Time of the last notification (Unix timestamp)
    last_state                            # State before last state change
    # latency                               # Time difference between scheduled check time and actual check time
    # long_plugin_output                    # Complete output from check plugin
    # low_flap_threshold                    # Low threshold of flap detection
    # max_check_attempts                    # Max check attempts for active host checks
    # metrics                               # A dummy column in order to be compatible with Check_MK Multisite
    # modified_attributes                   # A bitmask specifying which attributes have been modified
    # modified_attributes_list              # A list of all modified attributes
    # next_check                            # Scheduled time for the next check (Unix timestamp)
    # next_notification                     # Time of the next notification (Unix timestamp)
    # no_more_notifications                 # Whether to stop sending notifications (0/1)
    notes                                 # Optional notes for this host
    # notes_expanded                        # The same as notes, but with the most important macros expanded
    # notes_url                             # An optional URL with further information about the host
    # notes_url_expanded                    # Same es notes_url, but with the most important macros expanded
    # notification_interval                 # Interval of periodic notification or 0 if its off
    # notification_period                   # Time period in which problems of this host will be notified. If empty then notification will be always
    # percent_state_change                  # Percent state change
    # perf_data                             # Optional performance data of the last host check
    plugin_output                         # Output of the last host check
    # pnpgraph_present                      # Whether there is a PNP4Nagios graph present for this host (-1/0/1)
    # process_performance_data              # Whether processing of performance data is enabled (0/1)
    # retry_interval                        # Number of basic interval lengths between checks when retrying after a soft error
    # scheduled_downtime_depth              # The number of downtimes this host is currently in
    # service_period                        # The name of the service period of the host
    # staleness                             # Staleness indicator for this host
    # tag_names                             # A list of the names of the tags
    # tag_values                            # A list of the values of the tags
    # tags                                  # A dictionary of the tags
  )

COLUMNS_SVC=(
    host_name                                  # Host name
    description                                # Description of the service (also used as key)
    host_address                               # IP address
    host_state                                 # The current state of the host (0: up, 1: down, 2: unreachable)
    state                                      # The current state of the service (0: ok, 1: warning, 2: critical, 3: unknown)
    state_type                                 # Type of the current state (0: soft, 1: hard)
    last_state_change                     # Time of the last state change - soft or hard (Unix timestamp)
    notifications_enabled                 # Whether notifications of the host are enabled (0/1)
    has_been_checked                      # Whether the host has already been checked (0/1)

    # host_*                                     # all host values
    # cache_interval                             #
    # cached_at                                  #
    # last_time_ok                               # The last time the host was DOWN (Unix timestamp)
    # last_time_critical                         # The last time the host was UNREACHABLE (Unix timestamp)
    # last_time_unknown                          # The last time the host was UP (Unix timestamp)
    # last_time_warning                          # The last time the host was UP (Unix timestamp)
    # obsess_over_service                        # The current obsess_over_service setting... (0/1)

    "${COMMON_COLUMNS[@]}"
    host_custom_variables                        # A dictionary of the custom variables (host)
    custom_variables                             # A dictionary of the custom variables (service)
)

COLUMNS_HST=(
    host_name                             # Host name
    description                           # Empty on host
    host_address                          # IP address
    host_state                            # The current state of the host (0: up, 1: down, 2: unreachable)
    state                                 # The current state of the host (0: up, 1: down, 2: unreachable)
    state_type                            # Type of the current state (0: soft, 1: hard)
    last_state_change                     # Time of the last state change - soft or hard (Unix timestamp)
    notifications_enabled                 # Whether notifications of the host are enabled (0/1)
    has_been_checked                      # Whether the host has already been checked (0/1)

    # last_time_down                        # The last time the host was DOWN (Unix timestamp)
    # last_time_unreachable                 # The last time the host was UNREACHABLE (Unix timestamp)
    # last_time_up                          # The last time the host was UP (Unix timestamp)
    # obsess_over_host                      # The current obsess_over_host setting... (0/1)

    # check_flapping_recovery_notification  # Whether to check to send a recovery notification when flapping stops (0/1)
    # childs                                # A list of all direct childs of the host
    # filename                              # The value of the custom variable FILENAME
    # mk_inventory                          # The file content of the Check_MK HW/SW-Inventory
    # mk_inventory_gz                       # The gzipped file content of the Check_MK HW/SW-Inventory
    # mk_inventory_last                     # The timestamp of the last Check_MK HW/SW-Inventory for this host. 0 means that no inventory data is present
    # mk_logwatch_files                     # This list of logfiles with problems fetched via mk_logwatch
    # num_services                          # The total number of services of the host
    # num_services_crit                     # The number of the host's services with the soft state CRIT
    # num_services_hard_crit                # The number of the host's services with the hard state CRIT
    # num_services_hard_ok                  # The number of the host's services with the hard state OK
    # num_services_hard_unknown             # The number of the host's services with the hard state UNKNOWN
    # num_services_hard_warn                # The number of the host's services with the hard state WARN
    # num_services_ok                       # The number of the host's services with the soft state OK
    # num_services_pending                  # The number of the host's services which have not been checked yet (pending)
    # num_services_unknown                  # The number of the host's services with the soft state UNKNOWN
    # num_services_warn                     # The number of the host's services with the soft state WARN
    # obsess_over_host                      # The current obsess_over_host setting... (0/1)
    # parents                               # A list of all direct parents of the host
    # pending_flex_downtime                 # Number of pending flexible downtimes
    # services                              # A list of all services of the host
    # services_with_fullstate               # A list of all services including full state information. The list of entries can grow in future versions.
    # services_with_info                    # A list of all services including detailed information about each service
    # services_with_state                   # A list of all services of the host together with state and has_been_checked
    # statusmap_image                       # The name of in image file for the status map
    # structured_status                     # The file content of the structured status of the Check_MK HW/SW-Inventory
    # total_services                        # The total number of services of the host
    # worst_service_hard_state              # The worst hard state of all of the host's services (OK <= WARN <= UNKNOWN <= CRIT)
    # worst_service_state                   # The worst soft state of all of the host's services (OK <= WARN <= UNKNOWN <= CRIT)
    # x_3d                                  # 3D-Coordinates: X
    # y_3d                                  # 3D-Coordinates: Y
    # z_3d                                  # 3D-Coordinates: Z

    "${COMMON_COLUMNS[@]}"
    custom_variables                        # A dictionary of the custom variables (host)
    dummy                                   # Align with service custom variables
)

function debug() {
  local IFS=','
  echo "[DEBUG]${*/#/ }" >&2
}

function fatal() {
  local IFS=','
  echo "[FATAL]${*/#/ }" >&2
}

function tsv2json() {
  local IFS=,
  local index
  [[ $1 == --indexed-by-first-column ]] && index=1
  [[ $1 == --indexed-by-2columns ]] && index=2
  [[ $1 == --dual-indexed ]] && index=3
  awk -v "INDEX=$index" \
      -v "JSON_FORMAT_ENV=${JSON_FORMAT[*]}" \
      -v "ARRAYSEP=${LIVESEP[2]}" \
  '
    BEGIN {
      FS="\t";
      RS="\n";
      OFS="";
      ARRAYSEP = sprintf("%c", ARRAYSEP);
      for (i=1; i<=split(JSON_FORMAT_ENV, json_format, ","); i+=2)
        JSON_FORMAT[json_format[i]] = json_format[i+1];
      for (i=1; i<=127; i++)
        JESC[sprintf("%c", i)] = sprintf("\\u%04x", i);
      delete headers;
      printf("%s\n", ( INDEX ? "{" : "[" ));
    }
    function key(v) {
      return tolower((gensub("[^A-Za-z0-9]", "_", "g", v)));
    }
    function json(value) {
      if (match(value, "^-?[0-9]+(\\.[0-9]+)?$"))
        return value;
      buf = "\"";
      while (match(value, /[\x1-\x1f\\"\x7f]/)) {
        buf = buf substr(value, 1, RSTART-1) JESC[substr(value, RSTART, RLENGTH)];
        value = substr(value, RSTART+RLENGTH);
      }
      return buf value "\"";
    }
    function json_property(key, value, format            ,buf,i,a,n,p,jkv) {
      if (format <= 2) {
        if (format == 2 && value == "")
          return "";
        return "\""key"\": " json(value);
      }
      if (format == 3) {
        buf = "\""key"\": [";
        for (i=1; i<=split(value, a, ARRAYSEP); i++)
          buf = buf (i>1?",":"") json(a[i]);
        return buf "]";
      }
      if (format == 4) {
        buf = "";
        split(value, a, ARRAYSEP);
        for (i in a) {
          p = index(a[i], "=");
          if (p > 1) {
            jkv = json_property(substr(a[i], 1, p-1), substr(a[i], p+1), 1);
            if (jkv)
              buf = buf (buf?", ":"{ ") jkv;
          }
        }
        return (buf=="") ? "" : ("\""key"\": " buf " }");
      }
      return "";
    }
    {
      if (length(headers) == 0) {
        for (i=1;i<=NF;i++)
          headers[length(headers)+1] = ($i);
        next;
      }
      if (INDEX == 1) {
        printf("%s \"%s\": {",((NR>2)?",\n ":" "), key($2));
      }
      else if (INDEX == 2) {
        printf("%s\"%s\": {",((NR>2)?",\n ":" "), key($2)":"key($3));
      }
      else if (INDEX == 3) {
        printf("%s \"%s\": { \"%s\": {", ((NR>2)?",\n ":" "), key($2), key($3));
      }
      else {
        printf("%s {",((NR>2)?",\n":" "));
      }
      nprops = 0;
      for (i=1;i<=length(headers);i++) {
        jkv = json_property(headers[i], $i, JSON_FORMAT[headers[i]]);
        if (jkv) {
          printf("%s  %s", ((nprops>0)?",\n":"\n"), jkv);
          nprops++;
        }
      }
      if (INDEX == 3) {
        printf("\n } }");
      }
      else {
        printf("\n }");
      }
    }
    END {
      printf("\n%s\n", ( INDEX ? "}" : "]" ));
    }
  '
}

function livestatus() {
   local table=$1; shift
   local columnheaders=${COLUMNHEADERS:-on}
   local headers=( "$@" )
   local request=(
     "GET $table"
     "${headers[@]}"
     "Separators: ${LIVESEP[*]}"
     "ColumnHeaders: $columnheaders"
     ${OUTPUT_JSON:+OutputFormat: json}
   )
   # do not add limit with external order-by request
   [[ $ORDER ]] || request+=( ${LIMIT:+"Limit: $LIMIT"} )

   local IFS=$'\n'
   [[ -n $FAKE ]] && cat "$FAKE-$table.tsv" && return
   (( $DEBUG )) && echo "${request[*]}" >> /tmp/${0##*/}.debug
   $_UNIXCAT $LIVESOCKET <<<"${request[*]}"
}

function order() {
  # add priority column before order
  COLUMNS_SVC=( priority:float "${COLUMNS_SVC[@]}" )
  # add custom variables columns after others
  COLUMNS_SVC+=( ${CV_COLUMNS[@]} )
  # change cat command to apply limit
  if [[ $LIMIT ]]; then
    function cat() {
      head -n $LIMIT
    }
  fi
  if [[ $ORDER ]]; then
    local sortopts=()
    local col
    # if ORDER start with '-', reverse the order
    [[ ${ORDER:0:1} == - ]] && sortopts+=( -r )
    for ((col=0;col<${#COLUMNS_SVC[@]};col++)); do
      [[ ${COLUMNS_SVC[col]%%:*} == ${ORDER#-} ]] && break
    done
    if [[ $col < ${#COLUMNS_SVC[@]} ]]; then
      local type=${COLUMNS_SVC[col]#*:}
      if [[ $type == float || $type == int ]]; then
        sortopts+=( -n )
      else
        sortopts+=( -sfid )
      fi
      ( read ; echo "$REPLY" ; sort "${sortopts[@]}" -k $((col+1)) ) | cat
    else
      cat
    fi
  else
    cat
  fi
  unset -f cat
}

function computed_columns() {
  local IFS=","

  # compute priority and add CustomVariable columns
  awk -v "ENABLE_CV_COLUMNS=$ENABLE_CV_COLUMNS" \
      -v "CV_COLUMNS_ENV=${CV_COLUMNS[*]}" \
      -v "CV_FIELD_ENV=${CV_FIELD[*]}" \
      -v "ARRAYSEP=${LIVESEP[2]}" \
  '
      BEGIN {
        NOW = systime();
        split(CV_FIELD_ENV, CV_FIELD, ",");
        for (i=1; i<=split(CV_COLUMNS_ENV, cv_columns, ","); i+=2) {
          CV_COLUMNS[int((i+1)/2)] = cv_columns[i];
          CV_MODE[cv_columns[i]] = cv_columns[i+1];
        }
        FS = "\t";
        OFS = "\t";
        ARRAYSEP = sprintf("%c", ARRAYSEP);
      }
      function compute_priority() {
        # $2: description, empty on hosts
        # $4: host_state
        # $5: state, same as host_state on hosts
        # $7: last_state_change
        # $8: notifications_enabled
        # $9: has_been_checked

        # printf("%s/%s, host_state=%s, state=%s, last_state_change=%s, notifications_enabled=%s, \
        #   has_been_checked=%s\n", $1, $2, $4, $5, $7, $8, $9) >> "/dev/stderr";

        if ($8 == 0) # notification disabled
          return 0;
        if ($2 == "") { # host
          if ($9 == 0) # host pending
            return 2;
          if ($4 == 0) # host up
            return 4;
          if ($4 == 2) # host unreachable
            return 7;
          if ($4 == 1) # host down
            return 9;
        }
        else if ($9 == 0) # service pending
          return 1;
        else if ($5 == 0) # service ok
          return 4;
        else if ($5 == 1) # service warning
          return 5;
        else if ($5 == 3) # service unknown
          return 6;
        else if ($5 == 2) # service critical
          return 8;
        # default
        return -1;
      }
      function parse_cv(field, out_ref) {
        split($(field), kva, ARRAYSEP);
        for (kvi in kva) {
          key = substr(kva[kvi],1,index(kva[kvi],"=")-1);
          if (CV_MODE[key])
            out_ref[key] = substr(kva[kvi],length(key)+2);
        }
      }
      function get_cv(key, type) {
        if (CV_MODE[key] <= 1)
          return (type == 0) ? CVH[key] : CVS[key];
        if (CV_MODE[key] == 2)
          return CVH[key];
        if (CV_MODE[key] == 3)
          return CVS[key];
        if (CV_MODE[key] == 4)
          return CVS[key] == "" ? CVH[key] : CVS[key];
        if (CV_MODE[key] == 5) {
          out = "";
          delete seen; delete cva;
          cva_len = split(CVH[key]","CVS[key], cva, /[[:blank:],]+/);
          for (i = 1; i <= cva_len; i++) {
            if (cva[i] != "" && !seen[cva[i]]) {
              out = out (out==""?"":ARRAYSEP) (cva[i]);
              seen[cva[i]] = 1;
            }
          }
          return out;
        }
        return "";
      }
      {
        if (NR == 1) {
          priority = "priority";
          # CV fields: [1] hosts, [2] services
          for (i in CV_FIELD) {
            if (CV_FIELD[i] < 0)
              CV_FIELD[i] = NF + 1 + CV_FIELD[i];
          }
        }
        else {
          priority = sprintf("%.9lf", compute_priority() + ($7 / NOW));
        }
        if (ENABLE_CV_COLUMNS && NR > 1) {
          delete CVH; delete CVS;
          parse_cv(CV_FIELD[1], CVH); parse_cv(CV_FIELD[2], CVS);
          $(CV_FIELD[1]) = "..."; $(CV_FIELD[2]) = "...";
        }
        printf("%s%s%s", priority, FS, $0);
        if (ENABLE_CV_COLUMNS) {
          for (cvi in CV_COLUMNS) {
            printf("%s%s", FS, ((NR==1)?CV_COLUMNS[cvi]:get_cv(CV_COLUMNS[cvi], ($2?1:0))));
          }
        }
        printf("\n");
      }
  '
}

function do_GET() {
  livestatus "$@"
}

function do_tables() {
  livestatus columns "Columns: name description" "$@"
}

function do_services() {
  local IFS=' '
  local opts=(
    "Columns: ${COLUMNS_SVC[*]}"
    "${PRE_FILTER_SVC[@]}"
    "${FILTER[@]}"
  )
  livestatus services "${opts[@]}" "$@"
}

function do_hosts() {
  local IFS=' '
  local opts=(
    "Columns: ${COLUMNS_HST[*]}"
    "${PRE_FILTER_HST[@]}"
    "${FILTER[@]}"
  )

  livestatus hosts "${opts[@]}" "$@"
}

function do_combined() {
  ( do_services "$@" ; COLUMNHEADERS=off do_hosts "$@" )
}

function prepare_request() {
  LIMIT=${LIMIT:-200}
  (( LIMIT == 0 )) && unset LIMIT

  PRE_FILTER_HST=( )
  PRE_FILTER_SVC=( )
  FILTER_AND=0

  if [[ $QUERY ]]; then
    local subqueries=( ${QUERY// /$IFS} )
    local subquery not
    for subquery in "${subqueries[@]}"; do
      if [[ ${subquery:0:1} == '!' ]]; then
        subquery=${subquery:1}
        not=1
      else
        not=
      fi
      PRE_FILTER_HST+=( "Filter: host_name ~~ $subquery" )
      PRE_FILTER_HST+=( "Filter: host_address ~~ $subquery" )
      PRE_FILTER_HST+=( "Filter: plugin_output ~~ $subquery" )
      PRE_FILTER_HST+=( "Filter: host_custom_variables ~~ _TAGS $subquery" )
      PRE_FILTER_HST+=( "Or: 4" )
      PRE_FILTER_SVC+=( "Filter: host_name ~~ $subquery" )
      PRE_FILTER_SVC+=( "Filter: host_address ~~ $subquery" )
      PRE_FILTER_SVC+=( "Filter: description ~~ $subquery" )
      PRE_FILTER_SVC+=( "Filter: plugin_output ~~ $subquery" )
      PRE_FILTER_SVC+=( "Filter: host_custom_variables ~~ _TAGS $subquery" )
      PRE_FILTER_SVC+=( "Filter: custom_variables ~~ _TAGS $subquery" )
      PRE_FILTER_SVC+=( "Or: 6" )
      if [[ -n $not ]]; then
        PRE_FILTER_HST+=( "Negate:" )
        PRE_FILTER_SVC+=( "Negate:" )
      fi
    done
    if (( ${#subqueries[@]} > 1 )); then
      PRE_FILTER_HST+=( "And: ${#subqueries[@]}" )
      PRE_FILTER_SVC+=( "And: ${#subqueries[@]}" )
    fi
    (( FILTER_AND++ ))
  fi

  if [[ $LEVEL ]]; then
    LEVEL_AND=0
    if [[ $LEVEL == 0 ]]; then
      # only CRITICAL
      PRE_FILTER_SVC+=( "Filter: host_state = 0" )
      PRE_FILTER_SVC+=( "Filter: state = 2" )
      PRE_FILTER_SVC+=( "And: 2" )
      PRE_FILTER_HST+=( "Filter: state = 1" )
      (( LEVEL_AND++ ))
    elif [[ $LEVEL < 4 ]]; then
      # only non-OK
      PRE_FILTER_SVC+=( "Filter: host_state = 0" )
      PRE_FILTER_SVC+=( "Filter: state != 0" )
      PRE_FILTER_SVC+=( "And: 2" )
      PRE_FILTER_HST+=( "Filter: state = 1" )
      (( LEVEL_AND++ ))
    elif [[ $LEVEL < 5 ]]; then
      # regard-less of OUTAGE
      PRE_FILTER_SVC+=( "Filter: state != 0" )
      PRE_FILTER_HST+=( "Filter: state != 0" )
      (( LEVEL_AND++ ))
    fi
    if [[ $LEVEL < 2 ]]; then
      # only HARD-STATE
      FILTER+=( "Filter: state_type = 1" )
      (( LEVEL_AND++ ))
    fi
    if [[ $LEVEL < 3 ]]; then
      # only non-known issues
      FILTER+=( "Filter: acknowledged = 0" )
      FILTER+=( "Filter: notifications_enabled = 1" )
      (( LEVEL_AND+=2 ))
    fi

    if (( LEVEL_AND > 1 )); then
      # combine previous filters
      FILTER+=( "And: $LEVEL_AND" )
    fi

    if (( TRACK && LEVEL_AND > 0 )); then
      FILTER+=( 'Filter: custom_variables != _TRACK ' )
      FILTER+=( 'Filter: custom_variables != _TRACK 0' )
      FILTER+=( 'And: 2' )
      FILTER+=( 'Filter: custom_variables != _AUTOTRACK ' )
      FILTER+=( 'Filter: custom_variables != _AUTOTRACK 0' )
      FILTER+=( 'And: 2' )
      # OR tracked
      FILTER+=( 'Or: 3' )
    fi

    if (( LEVEL_AND > 0 )); then
      (( FILTER_AND++ ))
    fi
  fi

  if (( $SINCE )); then
    FILTER+=( "Filter: last_check >= $SINCE" )
    (( FILTER_AND++ ))
  fi

  if (( FILTER_AND > 1 )); then
    # prepare PRE_FILTER_(HST|SVC) & FILTER
    FILTER+=( "And: $FILTER_AND" )
  fi
}

if [[ $GATEWAY_INTERFACE ]]; then
  source ./lib.cgi

  header "Status: 200"
  header "Content-type: application/json"
  header --send
  ACTION=${_GET_action//[^0-9a-zA-Z\-]}
  LEVEL=${_GET_level//[^0-9]}
  QUERY=${_GET_query//[^0-9a-zA-Z_. @:#!+-]}
  ORDER=${_GET_order//[^0-9a-zA-Z_-]}
  LIMIT=${_GET_limit//[^0-9]}
  SINCE=${_GET_since//[^0-9]}
  TRACK=${_GET_track//[^0-9]}

  declare -f do_$ACTION > /dev/null ||
    fatal "undefine action '$ACTION'"

  prepare_request

  do_$ACTION | computed_columns | order | tsv2json --indexed-by-2columns

  exit 0
fi

while (( $# > 0 )); do
  case "$1" in
    ## -h, --help: This help
    -h|--help) usage && exit 0 ;;
    ## -V, --version: Show version
    -V|--version) version && exit 0 ;;
    ## --x-debug: Enable bash debug mode
    --x-debug)    XDEBUG=1 ;;
    ## -v, --verbose: Define verbose level (must be repeat)
    -v|--verbose) ((VERBOSE++)) ;;
    ## -q, --quiet: Set verbose level to 0
    -q|--quiet) ((VERBOSE=0)) ;;
    ## -F, --fake: Do not query livestatus, use <fake>-<table>.tsv
    -F|--fake) FAKE=$2; shift ;;
    ## --tsv: Output as TSV
    --tsv) ((TSV=1)) ;;
    ## --json: Output as JSON
    --json) ((JSON=1)) ;;
    ## --text: Output as TEXT
    --text) ((TEXT=1)) ;;
    -*) usage "Unknown parameter '$1'" && exit 1 ;;
    *) ARGS+=( "$1" ) ;;
  esac
  shift
done

(( XDEBUG )) && set -x

[[ -z ${ARGS[@]} ]] &&
  fatal --usage "need ACTION"

ACTION=${ARGS[0]}; ARGS=( ${ARGS[@]:1} )

declare -f do_$ACTION > /dev/null ||
  fatal "undefine action '$ACTION'"

prepare_request

if (( TSV )); then
  do_$ACTION "${ARGS[@]}" | computed_columns | order
elif (( JSON )); then
  do_$ACTION "${ARGS[@]}" | computed_columns | order | tsv2json --indexed-by-2columns
else
  do_$ACTION "${ARGS[@]}" | computed_columns | order | column -t -s $TAB
fi

exit 0
