#!/bin/env ./lib.cgi


function nagios_extcmd() {
  [[ $NAGIOS_EXTERNAL_COMMAND_FILE ]] || return
  printf "[%ld] %s\n" $NOW "$1" >> "$NAGIOS_EXTERNAL_COMMAND_FILE"
}

function do_alarm_off() {
  local host=${1%%:*}
  local svc=${1#*:}; svc=${svc,,}
  local author="$2"
  local comment="$3"
  
  if [[ $svc == _host_ ]]; then
    nagios_extcmd "DISABLE_HOST_NOTIFICATIONS;$host"
  else
    nagios_extcmd "DISABLE_SVC_NOTIFICATIONS;$host;$svc"
  fi
}

function do_ack() {
  local host=${1%%:*}
  local svc=${1#*:}; svc=${svc,,}
  local author="$2"
  local comment="$3"

  if [[ $svc == _host_ ]]; then
    nagios_extcmd "ACKNOWLEDGE_HOST_PROBLEM;$host;2;1;1;$author;$comment"
  else
    nagios_extcmd "ACKNOWLEDGE_SVC_PROBLEM;$host;$svc;2;1;1;$author;$comment"
  fi
}

function do_recharge() {
  local host=${1%%:*}
  local svc=${1#*:}; svc=${svc,,}
  local author="$2"
  local comment="$3"
  
  if [[ $svc == _host_ ]]; then
    nagios_extcmd "SCHEDULE_FORCED_HOST_SVC_CHECKS;$host;$NOW"
    nagios_extcmd "SCHEDULE_FORCED_HOST_CHECK;$host;$NOW"
  else
    nagios_extcmd "SCHEDULE_FORCED_SVC_CHECK;$host;$svc;$NOW"
  fi
}

function do_reset_state() {
  local host=${1%%:*}
  local svc=${1#*:}; svc=${svc,,}
  local author="$2"
  local comment="$3"
  
  if [[ $svc == _host_ ]]; then
    nagios_extcmd "DEL_ALL_HOST_COMMENTS;$host"
    nagios_extcmd "REMOVE_HOST_ACKNOWLEDGEMENT;$host"
    nagios_extcmd "CHANGE_CUSTOM_HOST_VAR;$host;_TRACK;"
  else
    nagios_extcmd "DEL_ALL_SVC_COMMENTS;$host;$svc"
    nagios_extcmd "REMOVE_SVC_ACKNOWLEDGEMENT;$host;$svc"
    nagios_extcmd "CHANGE_CUSTOM_SVC_VAR;$host;$svc;_TRACK;"
  fi
}

function do_comment() {
  local host=${1%%:*}
  local svc=${1#*:}; svc=${svc,,}
  local author="$2"
  local comment="$3"
  
  if [[ $svc == _host_ ]]; then
    nagios_extcmd "ADD_HOST_COMMENT;$host;1;$author;$comment"
  else
    nagios_extcmd "ADD_SVC_COMMENT;$host;$svc;1;$author;$comment"
  fi
}

function do_track() {
  local host=${1%%:*}
  local svc=${1#*:}; svc=${svc,,}
  local author="$2"
  local comment="$3"

  if [[ $svc == _host_ ]]; then
    nagios_extcmd "CHANGE_CUSTOM_HOST_VAR;$host;_TRACK;$author:$comment"
  else
    nagios_extcmd "CHANGE_CUSTOM_SVC_VAR;$host;$svc;_TRACK;$author:$comment"
  fi
}

if [[ -z $_TEMP_CONTENT_DATA || ! -s $_TEMP_CONTENT_DATA ]]; then
  # empty or bad POST
  fatal "error in data"
fi

ACTION=$(jq -r .order < $_TEMP_CONTENT_DATA)
COMMENT=$(jq -r .comment < $_TEMP_CONTENT_DATA)
AUTHOR="${REMOTE_USER:-anonymous} via ACTION.CGI"

[[ -n $ACTION && -z ${ACTION//[a-zA-Z0-9-_]} ]] ||
  fatal "bad action '$ACTION'"
  
[[ $COMMENT ]] ||
  fatal "empty comment"

header "Status: 200"
header "Content-Type: application/json"
header --send

DO_ACTION="do_${ACTION//[^a-zA-Z0-9_]/_}"

declare -f  >/dev/null ||
  fatal "unknown action '$ACTION' ($DO_ACTION)"

while read; do
  echo "ACTION: $DO_ACTION on $REPLY" >&2
  # ID+=( "$REPLY" )
  $DO_ACTION "$REPLY" "$COMMENT"
done < <(jq -r '.data[]|.id' < $_TEMP_CONTENT_DATA)

printf '{"status": "ok", "action": "%s"}' "$ACTION"

