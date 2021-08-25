#!/bin/env ./lib.cgi
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
## Description: execute action
##
#

function nagios_extcmd() {
  [[ $NAGIOS_EXTERNAL_COMMAND_FILE ]] || return
  printf "[%ld] %s\n" $NOW "$1" >> "$NAGIOS_EXTERNAL_COMMAND_FILE"
}

function do_alarm_off() {
  if [[ $svc == _HOST_ ]]; then
    nagios_extcmd "DISABLE_HOST_NOTIFICATIONS;$host"
    nagios_extcmd "DISABLE_HOST_SVC_NOTIFICATIONS;$host"
  else
    nagios_extcmd "DISABLE_SVC_NOTIFICATIONS;$host;$svc"
  fi
}

function do_ack() {
  if [[ $svc == _HOST_ ]]; then
    nagios_extcmd "ACKNOWLEDGE_HOST_PROBLEM;$host;2;0;1;$AUTHOR;$COMMENT"
    sleep 2 && nagios_extcmd "CHANGE_CUSTOM_HOST_VAR;$host;_AUTOTRACK;0"
  else
    nagios_extcmd "ACKNOWLEDGE_SVC_PROBLEM;$host;$svc;2;0;1;$AUTHOR;$COMMENT"
    sleep 2 && nagios_extcmd "CHANGE_CUSTOM_SVC_VAR;$host;$svc;_AUTOTRACK;0"
  fi
}

function do_recharge() {
  if [[ $svc == _HOST_ ]]; then
    nagios_extcmd "SCHEDULE_HOST_CHECK;$host;$NOW"
    nagios_extcmd "SCHEDULE_HOST_SVC_CHECKS;$host;$NOW"
  else
    nagios_extcmd "SCHEDULE_SVC_CHECK;$host;$svc;$NOW"
  fi
}

function do_reset_state() {
  if [[ $svc == _HOST_ ]]; then
    nagios_extcmd "DEL_ALL_HOST_COMMENTS;$host"
    nagios_extcmd "ENABLE_HOST_NOTIFICATIONS;$host"
    nagios_extcmd "ENABLE_HOST_SVC_NOTIFICATIONS;$host"
    nagios_extcmd "REMOVE_HOST_ACKNOWLEDGEMENT;$host"
    nagios_extcmd "SCHEDULE_FORCED_HOST_CHECK;$host;$NOW"
    nagios_extcmd "SCHEDULE_FORCED_HOST_SVC_CHECKS;$host;$NOW"
    nagios_extcmd "CHANGE_CUSTOM_HOST_VAR;$host;_TRACK;0"
    nagios_extcmd "CHANGE_CUSTOM_HOST_VAR;$host;_CLEAR_CACHE;1"
    sleep 2 && nagios_extcmd "CHANGE_CUSTOM_HOST_VAR;$host;_AUTOTRACK;0"
  else
    nagios_extcmd "DEL_ALL_SVC_COMMENTS;$host;$svc"
    nagios_extcmd "ENABLE_SVC_NOTIFICATIONS;$host;$svc"
    nagios_extcmd "REMOVE_SVC_ACKNOWLEDGEMENT;$host;$svc"
    nagios_extcmd "SCHEDULE_FORCED_SVC_CHECK;$host;$svc;$NOW"
    nagios_extcmd "CHANGE_CUSTOM_SVC_VAR;$host;$svc;_TRACK;0"
    nagios_extcmd "CHANGE_CUSTOM_SVC_VAR;$host;$svc;_CLEAR_CACHE;1"
    sleep 2 && nagios_extcmd "CHANGE_CUSTOM_SVC_VAR;$host;$svc;_AUTOTRACK;0"
  fi
}

function do_comment() {
  if [[ $svc == _HOST_ ]]; then
    nagios_extcmd "ADD_HOST_COMMENT;$host;1;$AUTHOR;$COMMENT"
  else
    nagios_extcmd "ADD_SVC_COMMENT;$host;$svc;1;$AUTHOR;$COMMENT"
  fi
}

function do_track() {
  if [[ $svc == _HOST_ ]]; then
    nagios_extcmd "CHANGE_CUSTOM_HOST_VAR;$host;_TRACK;$AUTHOR:$COMMENT"
  else
    nagios_extcmd "CHANGE_CUSTOM_SVC_VAR;$host;$svc;_TRACK;$AUTHOR:$COMMENT"
  fi
}

if [[ -z $_TEMP_CONTENT_DATA || ! -s $_TEMP_CONTENT_DATA ]]; then
  # empty or bad POST
  fatal "error in data"
fi

ACTION=$(jq -r .order < $_TEMP_CONTENT_DATA)
COMMENT=$(jq -r .comment < $_TEMP_CONTENT_DATA)
COMMENT=${COMMENT:--}
AUTHOR="${REMOTE_USER:-anonymous}"

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

IFS=";"
while read host svc rest; do
  [[ -z $svc ]] && svc="_HOST_"
  echo "DO_ACTION '$DO_ACTION' '$host' '$svc' '$AUTHOR' '$COMMENT'" >&2
  $DO_ACTION
done < <(jq -r '.data[]|(.name+";"+.description)' < $_TEMP_CONTENT_DATA)

printf '{"status": "ok", "action": "%s"}' "$ACTION"

